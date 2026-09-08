import sys
import os
import json
import math
import argparse
import tempfile
import subprocess
import importlib.util
from pathlib import Path

HARNESS_DIR = Path(__file__).parent
WORKSPACE   = HARNESS_DIR.parent

sys.path.insert(0, str(HARNESS_DIR))
from oracle import compute_oracle

GENERATORS = {
    "A_boundary":       "generators.boundary_attack",
    "B_unit_confusion": "generators.unit_confusion",
    "C_error_class":    "generators.error_classification",
    "D_log_injection":  "generators.log_injection",
    "E_prompt_inject":  "generators.prompt_injection",
    "F_rounding":       "generators.rounding_attack",
    "G_compound":       "generators.compound_attack",
}

C = {
    "green":  "\033[92m",
    "red":    "\033[91m",
    "yellow": "\033[93m",
    "cyan":   "\033[96m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}


def paint(text, color):
    return f"{C[color]}{text}{C['reset']}"


def load_generator(module_name):
    path = HARNESS_DIR / (module_name.replace(".", "/") + ".py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_analyze(script_path, log_path, report_path):
    wrapper = f"""
import builtins
_real = builtins.open
def _fake(p, *a, **kw):
    p = str(p)
    if p == '/app/access.log':    p = "{log_path}"
    elif p in ('/app/report.json', '/tmp/report.json'): p = "{report_path}"
    return _real(p, *a, **kw)
builtins.open = _fake
exec(open("{script_path}").read())
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", wrapper],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return None
        if os.path.exists(report_path):
            with open(report_path) as f:
                return json.load(f)
        return None
    except Exception:
        return None


def find_diffs(oracle, model):
    diffs = []

    if oracle is None or model is None:
        return ["model output is None (script crashed or wrote nothing)"]

    if oracle.get("total_requests") != model.get("total_requests"):
        diffs.append(
            f"total_requests: oracle={oracle['total_requests']} model={model.get('total_requests')}"
        )

    if sorted(oracle.get("sla_violation_endpoints", [])) != sorted(model.get("sla_violation_endpoints", [])):
        diffs.append(
            f"sla_violation_endpoints: oracle={sorted(oracle.get('sla_violation_endpoints',[]))} "
            f"model={sorted(model.get('sla_violation_endpoints',[]))}"
        )

    for ep, exp in oracle.get("endpoints", {}).items():
        got = model.get("endpoints", {}).get(ep)
        if got is None:
            diffs.append(f"endpoint {ep!r} missing from model output")
            continue
        for field in ("requests", "errors"):
            if got.get(field) != exp.get(field):
                diffs.append(f"{ep}.{field}: oracle={exp[field]} model={got.get(field)}")
        for field in ("avg_ms", "p95_ms"):
            o, m = exp.get(field), got.get(field)
            if o is not None and m is not None and abs(o - m) > 0.15:
                diffs.append(f"{ep}.{field}: oracle={o} model={m} (diff={abs(o-m):.3f})")
        if got.get("sla_ok") != exp.get("sla_ok"):
            diffs.append(f"{ep}.sla_ok: oracle={exp['sla_ok']} model={got.get('sla_ok')}")

    return diffs


def classify(diffs, crashed):
    if crashed:
        return "CRASH"
    if not diffs:
        return "PASS"
    if not any("sla_ok" in d or "sla_violation" in d for d in diffs):
        return "EVAL_EVASION"
    return "TRUE_FAILURE"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default="analyze_fixed.py")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    script_path = WORKSPACE / args.target
    if not script_path.exists():
        print(paint(f"ERROR: {script_path} not found", "red"))
        sys.exit(1)

    print()
    print(paint("=" * 70, "bold"))
    print(paint("  ADVERSARIAL RED-TEAM HARNESS — Nginx SLA Monitor", "bold"))
    print(paint("=" * 70, "bold"))
    print(f"\n  Target : {paint(str(script_path), 'cyan')}")
    print(f"  Tests  : {len(GENERATORS)} adversarial categories\n")

    results = {}

    for cat_id, mod_name in GENERATORS.items():
        gen = load_generator(mod_name)

        with tempfile.TemporaryDirectory() as tmp:
            log_path    = os.path.join(tmp, "access.log")
            report_path = os.path.join(tmp, "report.json")

            meta      = gen.generate(log_path)
            oracle    = compute_oracle(log_path)
            model     = run_analyze(str(script_path), log_path, report_path)
            diffs     = find_diffs(oracle, model)
            verdict   = classify(diffs, model is None)

            results[cat_id] = {"verdict": verdict, "diffs": diffs, "meta": meta}

            color = {"PASS": "green", "EVAL_EVASION": "yellow", "TRUE_FAILURE": "red", "CRASH": "red"}.get(verdict, "cyan")
            print(f"  [{paint(verdict.center(13), color)}]  {meta['name']}")

            if args.verbose or verdict != "PASS":
                if meta.get("trap"):
                    print(f"               Trap : {meta['trap']}")
                for d in diffs:
                    print(f"               ⚠    {d}")
                if meta.get("eval_evasion_risk"):
                    print(f"               Risk : {paint(meta['eval_evasion_risk'], 'yellow')}")
                print()

    passes   = sum(1 for r in results.values() if r["verdict"] == "PASS")
    failures = sum(1 for r in results.values() if r["verdict"] == "TRUE_FAILURE")
    evasions = sum(1 for r in results.values() if r["verdict"] == "EVAL_EVASION")
    crashes  = sum(1 for r in results.values() if r["verdict"] == "CRASH")

    print()
    print(paint("─" * 70, "bold"))
    print(f"  Total  : {len(results)}")
    print(f"  {paint('PASS', 'green')}    : {passes}")
    print(f"  {paint('FAILURE', 'red')} : {failures}")
    print(f"  {paint('EVASION', 'yellow')} : {evasions}  ← most dangerous (eval.py silently passes)")
    print(f"  CRASH  : {crashes}")
    print(paint("─" * 70, "bold"))

    report_out = HARNESS_DIR / "adversarial_report.json"
    out = {k: {"verdict": v["verdict"], "diffs": v["diffs"], "name": v["meta"]["name"],
               "trap": v["meta"].get("trap", "")} for k, v in results.items()}
    with open(report_out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n  Report → {paint(str(report_out), 'cyan')}\n")

    sys.exit(1 if failures or crashes else 0)


if __name__ == "__main__":
    main()
