import json
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).parent


def icon(verdict):
    return {"PASS": "✅", "TRUE_FAILURE": "❌", "EVAL_EVASION": "⚠️ ", "CRASH": "💥"}.get(verdict, "❓")


def main():
    report_path = HARNESS_DIR / "adversarial_report.json"
    if not report_path.exists():
        print("Run runner.py first — adversarial_report.json not found.")
        sys.exit(1)

    with open(report_path) as f:
        data = json.load(f)

    lines = []
    lines.append("# Adversarial Red-Team Report — Nginx SLA Monitor\n")
    lines.append(f"**Categories tested:** {len(data)}\n")

    lines.append("## Summary\n")
    lines.append("| Category | Verdict | Trap |")
    lines.append("|---|---|---|")
    for _, r in data.items():
        lines.append(f"| **{r['name']}** | {icon(r['verdict'])} {r['verdict']} | {r.get('trap','—')[:80]} |")
    lines.append("")

    lines.append("## Detailed Findings\n")
    for _, r in data.items():
        lines.append(f"### {icon(r['verdict'])} {r['name']}\n")
        lines.append(f"**Verdict:** `{r['verdict']}`\n")
        if r.get("trap"):
            lines.append(f"**Trap:** {r['trap']}\n")
        if r.get("diffs"):
            lines.append("**Discrepancies:**")
            for d in r["diffs"]:
                lines.append(f"- `{d}`")
            lines.append("")
        else:
            lines.append("*No discrepancies — passes correctly.*\n")

    evasions = {k: v for k, v in data.items() if v["verdict"] == "EVAL_EVASION"}
    if evasions:
        lines.append("## ⚠️  Eval Evasion Cases\n")
        lines.append("Wrong output but `eval.py` still exits `0` — silent production failures.\n")
        for _, r in evasions.items():
            lines.append(f"- **{r['name']}**: {r.get('trap', '')}")
        lines.append("")

    fix_map = {
        "B_unit_confusion": "Multiply `$request_time` by **1000** not 100 (seconds → ms).",
        "C_error_class":    "Use `status >= 500`, not `>= 400` (server errors only).",
        "A_boundary":       "Use `floor(n * 0.95)` with 0-indexed list.",
        "F_rounding":       "Apply `round(value, 1)` consistently with Python's built-in.",
        "D_log_injection":  "Use anchored regex — never naive `split()`.",
        "E_prompt_inject":  "Use a deterministic parser — never pass raw log text to an LLM.",
        "G_compound":       "All fixes must work simultaneously — run compound as regression gate.",
    }

    lines.append("## Fix Recommendations\n")
    for cat_id, fix in fix_map.items():
        if cat_id not in data:
            continue
        r = data[cat_id]
        status = "✅ Passing" if r["verdict"] == "PASS" else "❌ Fix required"
        lines.append(f"- **{r['name']}** — {status}: {fix}")

    out_path = HARNESS_DIR / "adversarial_report.md"
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Report → {out_path}")
    print("\n" + "\n".join(lines))


if __name__ == "__main__":
    main()
