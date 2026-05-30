#!/usr/bin/env python3
"""Measure validation-agent response time and decision consistency.

Supports Anthropic and OpenAI-compatible providers such as Qwen DashScope and
DeepSeek. For Qwen/DeepSeek set OPENAI_API_KEY, OPENAI_BASE_URL, and
BENCHMARK_MODEL.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PROMPTS_FILE = ROOT / "validation_prompts.json"
POLICY_FILE = ROOT / "prompts" / "arch-gate-policy.txt"


def classify_text(text: str) -> str:
    upper = text.upper()
    if "BLOCK" in upper:
        return "BLOCK"
    if "REVIEW" in upper:
        return "REVIEW"
    if "PASS" in upper:
        return "PASS"
    return "UNCLEAR"


def dry_response(prompt: dict, temperature: float) -> tuple[str, int, str]:
    expected = prompt["expected"]
    if temperature >= 0.3 and prompt["type"] == "boundary" and random.random() < 0.18:
        decision = random.choice(["PASS", "BLOCK"])
    elif temperature >= 0.3 and random.random() < 0.04:
        decision = "REVIEW" if expected != "REVIEW" else random.choice(["PASS", "BLOCK"])
    else:
        decision = expected
    text = f"{decision}: simulated DIKCA C-layer classification."
    return decision, len(text.split()), text


def anthropic_response(prompt: dict, temperature: float, model: str, max_tokens: int) -> tuple[str, int, str]:
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Install anthropic or run with --dry-run") from exc
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=POLICY_FILE.read_text(encoding="utf-8"),
        messages=[{"role": "user", "content": prompt["content"]}],
    )
    text = "\n".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    return classify_text(text), response.usage.output_tokens, text


def openai_compatible_response(prompt: dict, temperature: float, model: str, max_tokens: int) -> tuple[str, int, str]:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install openai or run with --dry-run") from exc
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY, QWEN_API_KEY, DASHSCOPE_API_KEY, or DEEPSEEK_API_KEY")
    if not base_url:
        raise RuntimeError("Set OPENAI_BASE_URL for the OpenAI-compatible provider")
    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": POLICY_FILE.read_text(encoding="utf-8")},
            {"role": "user", "content": prompt["content"]},
        ],
    )
    text = response.choices[0].message.content or ""
    tokens = response.usage.completion_tokens if response.usage else 0
    return classify_text(text), tokens, text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--temperatures", nargs="*", type=float, default=[0.1, 0.3])
    parser.add_argument("--backend", choices=["auto", "openai", "anthropic"], default=os.environ.get("BENCHMARK_BACKEND", "auto"))
    parser.add_argument("--model", default=os.environ.get("BENCHMARK_MODEL") or os.environ.get("ANTHROPIC_MODEL") or "qwen-plus")
    parser.add_argument("--max-tokens", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    prompts = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    out = RESULTS / f"exp2_temperature_{time.strftime('%Y%m%d_%H%M%S')}.csv"

    random.seed(42)
    backend = args.backend
    if backend == "auto":
        backend = "openai" if (os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_KEY") or os.environ.get("QWEN_API_KEY") or os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")) else "anthropic"

    rows = []
    for temp in args.temperatures:
        for prompt in prompts:
            for run in range(1, args.runs + 1):
                start = time.perf_counter()
                if args.dry_run:
                    decision, tokens, _ = dry_response(prompt, temp)
                    time.sleep(random.uniform(0.05, 0.16))
                elif backend == "openai":
                    decision, tokens, _ = openai_compatible_response(prompt, temp, args.model, args.max_tokens)
                else:
                    decision, tokens, _ = anthropic_response(prompt, temp, args.model, args.max_tokens)
                wall_ms = round((time.perf_counter() - start) * 1000, 1)
                rows.append({
                    "prompt_id": prompt["id"],
                    "prompt_type": prompt["type"],
                    "expected": prompt["expected"],
                    "temperature": temp,
                    "run": run,
                    "wall_ms": wall_ms,
                    "output_tokens": tokens,
                    "decision": decision,
                    "correct": decision == prompt["expected"],
                    "backend": backend,
                    "model": args.model,
                })
                print(f"T={temp} {prompt['id']} run={run} decision={decision} wall_ms={wall_ms}")

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] Exp2 results: {out}")


if __name__ == "__main__":
    main()
