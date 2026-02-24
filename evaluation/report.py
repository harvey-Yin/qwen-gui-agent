"""
Benchmark Report Generator.
Loads one or more JSON reports and produces a comparison table.
"""
import json
from pathlib import Path
from typing import List, Dict, Any


def load_report(path: str) -> Dict[str, Any]:
    """Load a benchmark report from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_comparison(reports: List[Dict[str, Any]]) -> None:
    """Print a side-by-side comparison table of multiple benchmark reports."""
    if not reports:
        print("No reports to compare.")
        return

    # Header
    model_names = [r["model_name"] for r in reports]
    header = f"{'Metric':<30}" + "".join(f"{name:>20}" for name in model_names)
    print("\n" + "=" * len(header))
    print("  BENCHMARK COMPARISON")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    # Summary metrics
    metrics = [
        ("Task Completion Rate", lambda r: f"{r['summary']['task_completion_rate']:.1%}"),
        ("Verification Rate",    lambda r: f"{r['summary']['verification_rate']:.1%}"),
        ("Avg Steps",            lambda r: f"{r['summary']['avg_steps']:.1f}"),
        ("Avg Response Time (s)", lambda r: f"{r['summary']['avg_response_time_s']:.1f}"),
    ]

    for name, fn in metrics:
        row = f"{name:<30}" + "".join(f"{fn(r):>20}" for r in reports)
        print(row)

    print("-" * len(header))

    # Per-task breakdown
    all_task_ids = []
    for r in reports:
        for s in r.get("scores", []):
            if s["task_id"] not in all_task_ids:
                all_task_ids.append(s["task_id"])

    print(f"\n{'Task':<30}" + "".join(f"{name:>20}" for name in model_names))
    print("-" * len(header))

    for tid in all_task_ids:
        row = f"{tid:<30}"
        for r in reports:
            score = next((s for s in r["scores"] if s["task_id"] == tid), None)
            if score:
                mark = "✅" if score["completed"] else "❌"
                row += f"{mark} {score['steps_used']}步 {score['response_time']:.0f}s".rjust(20)
            else:
                row += f"{'—':>20}"
        print(row)

    print("=" * len(header))


def generate_markdown_report(reports: List[Dict[str, Any]]) -> str:
    """Generate a Markdown comparison report."""
    lines = ["# GUI Agent Benchmark Report\n"]

    # Summary table
    lines.append("## Summary\n")
    header = "| Metric | " + " | ".join(r["model_name"] for r in reports) + " |"
    sep = "|---|" + "|".join("---" for _ in reports) + "|"
    lines.append(header)
    lines.append(sep)

    metrics = [
        ("Task Completion Rate", lambda r: f"{r['summary']['task_completion_rate']:.1%}"),
        ("Verification Rate",    lambda r: f"{r['summary']['verification_rate']:.1%}"),
        ("Avg Steps",            lambda r: f"{r['summary']['avg_steps']:.1f}"),
        ("Avg Response Time",    lambda r: f"{r['summary']['avg_response_time_s']:.1f}s"),
    ]

    for name, fn in metrics:
        row = f"| {name} | " + " | ".join(fn(r) for r in reports) + " |"
        lines.append(row)

    # Per-task table
    lines.append("\n## Per-Task Results\n")
    header2 = "| Task | " + " | ".join(r["model_name"] for r in reports) + " |"
    lines.append(header2)
    lines.append(sep)

    all_task_ids = []
    for r in reports:
        for s in r.get("scores", []):
            if s["task_id"] not in all_task_ids:
                all_task_ids.append(s["task_id"])

    for tid in all_task_ids:
        cells = []
        for r in reports:
            score = next((s for s in r["scores"] if s["task_id"] == tid), None)
            if score:
                mark = "✅" if score["completed"] else "❌"
                cells.append(f"{mark} {score['steps_used']}步/{score['max_steps']}")
            else:
                cells.append("—")
        row = f"| {tid} | " + " | ".join(cells) + " |"
        lines.append(row)

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare benchmark reports")
    parser.add_argument("reports", nargs="+", help="Paths to JSON report files")
    parser.add_argument("--markdown", action="store_true", help="Output as Markdown")
    args = parser.parse_args()

    loaded = [load_report(p) for p in args.reports]

    if args.markdown:
        md = generate_markdown_report(loaded)
        print(md)
    else:
        print_comparison(loaded)
