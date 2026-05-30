#!/usr/bin/env python3
"""Summarise EA-Harness benchmark CSV outputs into manuscript-ready tables."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def mean_sd(values):
    values = [float(v) for v in values]
    if not values:
        return "n/a"
    if len(values) == 1:
        return f"{values[0]:.1f}"
    return f"{statistics.mean(values):.1f} +/- {statistics.stdev(values):.1f}"


def latest(results_dir: Path, prefix: str) -> Path | None:
    files = sorted(results_dir.glob(f"{prefix}_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def analyse_exp1(path: Path) -> str:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    by_config = defaultdict(list)
    by_config_type = defaultdict(list)
    gate_rows = []
    for r in rows:
        total_key = "total_wall_ms" if "total_wall_ms" in r else "wall_ms"
        by_config[r["config"]].append(float(r[total_key]))
        by_config_type[(r["config"], r["task_type"])].append(r)
        if r["config"] == "gate":
            gate_rows.append(r)
    baseline = by_config.get("baseline", [])
    gate = by_config.get("gate", [])
    overhead = "n/a"
    if baseline and gate:
        overhead = f"{((statistics.mean(gate) - statistics.mean(baseline)) / statistics.mean(baseline) * 100):.1f}%"
    type_a = by_config_type.get(("gate", "type-a"), [])
    type_b = by_config_type.get(("gate", "type-b"), [])
    type_c = by_config_type.get(("gate", "type-c"), [])
    gate_key = "gate_decision" if rows and "gate_decision" in rows[0] else "decision"
    fpr = sum(1 for r in type_a if r[gate_key] in {"BLOCK", "REVIEW"}) / len(type_a) * 100 if type_a else 0.0
    block_rate = sum(1 for r in type_b if r[gate_key] == "BLOCK") / len(type_b) * 100 if type_b else 0.0
    pass_through = sum(1 for r in type_b if r[gate_key] == "PASS") / len(type_b) * 100 if type_b else 0.0
    review_rate = sum(1 for r in type_c if r[gate_key] == "REVIEW") / len(type_c) * 100 if type_c else 0.0
    gate_latency = [r.get("gate_wall_ms", 0) for r in gate_rows]
    build_latency = [r.get("build_wall_ms", 0) for r in gate_rows if str(r.get("build_executed", "")).lower() == "true"]
    gate_tokens = [float(r.get("gate_output_tokens", 0) or 0) for r in gate_rows]
    return "\n".join([
        "## Experiment 1 - Gate overhead",
        f"Source: `{path.name}`",
        "",
        "| Metric | Baseline | Gate-enabled | Delta |",
        "|---|---:|---:|---:|",
        f"| Mean session time (ms) | {mean_sd(baseline)} | {mean_sd(gate)} | {overhead} |",
        f"| Mean gate-only latency (ms) | n/a | {mean_sd(gate_latency)} | n/a |",
        f"| Mean gated build latency (ms) | n/a | {mean_sd(build_latency)} | n/a |",
        f"| Mean gate output tokens | n/a | {mean_sd(gate_tokens)} | n/a |",
        f"| Type-A false-positive rate | n/a | {fpr:.1f}% | n/a |",
        f"| Type-B block rate | n/a | {block_rate:.1f}% | n/a |",
        f"| Type-B safety pass-through error | n/a | {pass_through:.1f}% | n/a |",
        f"| Type-C review rate | n/a | {review_rate:.1f}% | n/a |",
    ])


def analyse_exp2(path: Path) -> str:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    grouped = defaultdict(list)
    prompt_decisions = defaultdict(list)
    for r in rows:
        key = (r["temperature"], r["prompt_type"])
        grouped[key].append(r)
        prompt_decisions[(r["temperature"], r["prompt_id"])].append(r["decision"])
    agreement_by_temp_type = defaultdict(list)
    prompt_type_lookup = {r["prompt_id"]: r["prompt_type"] for r in rows}
    for (temp, prompt_id), decisions in prompt_decisions.items():
        majority = Counter(decisions).most_common(1)[0][1]
        agreement_by_temp_type[(temp, prompt_type_lookup[prompt_id])].append(majority / len(decisions) * 100)
    lines = [
        "## Experiment 2 - Temperature consistency",
        f"Source: `{path.name}`",
        "",
        "| Temperature | Prompt type | Mean RT (ms) | Output tokens | Accuracy | Agreement | Model |",
        "|---:|---|---:|---:|---:|---:|---|",
    ]
    for key in sorted(grouped.keys()):
        temp, ptype = key
        items = grouped[key]
        rt = mean_sd([r["wall_ms"] for r in items])
        tokens = mean_sd([r["output_tokens"] for r in items])
        acc = sum(1 for r in items if str(r["correct"]).lower() == "true") / len(items) * 100
        agreement = statistics.mean(agreement_by_temp_type[key]) if agreement_by_temp_type[key] else 0.0
        model = items[0].get("model", "n/a")
        lines.append(f"| {temp} | {ptype} | {rt} | {tokens} | {acc:.1f}% | {agreement:.1f}% | {model} |")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default=str(Path(__file__).resolve().parents[1] / "results"))
    args = parser.parse_args()
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    sections = []
    exp1 = latest(results_dir, "exp1_gate_overhead")
    exp2 = latest(results_dir, "exp2_temperature")
    if exp1:
        sections.append(analyse_exp1(exp1))
    if exp2:
        sections.append(analyse_exp2(exp2))
    if not sections:
        print("No benchmark CSV files found.")
        return
    summary = "\n\n".join(sections) + "\n"
    out = results_dir / "summary.md"
    out.write_text(summary, encoding="utf-8")
    print(summary)
    print(f"[OK] Summary written: {out}")


if __name__ == "__main__":
    main()
