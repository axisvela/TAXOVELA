# EA-Harness Experiment Status for AI and Ethics Minor Revision

Date: 2026-05-30

This note records the current benchmark design, migration status, pilot results, and next steps for the AI and Ethics minor revision of:

> "Intelligence Beyond Knowledge: Control, Architecture, and the Structural Law of Artificial Agency"

## Repository status

- Canonical working repository: `D:\project\ea-harness`
- Deprecated working copy: `D:\project\arch-harness`
- Action: continue all paper experiments in `ea-harness`; do not use `arch-harness` except as a temporary backup until the final experiment results are confirmed.

The benchmark suite has been migrated into:

```text
D:\project\ea-harness\benchmark
```

## Editor request being addressed

The benchmark primarily addresses revision item R2:

> Provide operational or performance context regarding the impact of introducing the `ci-gate-spec.yaml` / C-layer validation gate, including latency, computational overhead, and the effect of near-deterministic validation temperatures.

The results also support R1 by quantifying part of the utility/safety trade-off: gate overhead and false-positive / block / review behavior.

## Benchmark structure

```text
benchmark/
├── README.md
├── EXPERIMENT_STATUS.md
├── configs/
│   ├── opencode-baseline.json
│   └── opencode-gate.json
├── prompts/
│   ├── arch-gate-policy.txt
│   └── build-with-gate.txt
├── results/
│   └── .gitkeep
├── scripts/
│   ├── run_benchmark.ps1
│   ├── exp1_gate_overhead.ps1
│   ├── exp2_temperature.py
│   └── analyze_results.py
├── tasks/
│   ├── type-a/   # compliant tasks; expected PASS
│   ├── type-b/   # violating tasks; expected BLOCK
│   └── type-c/   # boundary tasks; expected REVIEW
└── validation_prompts.json
```

Generated CSV and summary files are ignored by git:

```text
benchmark/results/*.csv
benchmark/results/*.md
```

This prevents pilot data from being accidentally committed. Preserve final CSV/summary files separately when preparing the manuscript revision package.

## Experiment 1: strict C-layer gate-to-A-layer build overhead

### Purpose

Measure the operational overhead and enforcement behavior of a strict DIKCA C-layer gate before A-layer action.

### Current implementation

Script:

```text
benchmark/scripts/exp1_gate_overhead.ps1
```

Workflow:

```text
baseline:
  build agent classifies the task directly

gate-enabled:
  arch-validator gate runs first
  if gate_decision == PASS: build agent runs
  if gate_decision == BLOCK or REVIEW: build agent does not run
```

Important implementation detail:

- The script temporarily clears inherited `OPENCODE*` environment variables for each child OpenCode invocation.
- This avoids the OpenCode Desktop nested-session error:

```text
Error: Session not found
```

OpenCode binary used in the local pilot:

```text
D:\app\OpenCode\opencode-cli.exe
```

Model used in the local pilot:

```text
deepseek/deepseek-v4-flash
```

### Pilot run completed

Command:

```powershell
cd D:\project\ea-harness
powershell -NoProfile -ExecutionPolicy Bypass -File "benchmark\scripts\run_benchmark.ps1" -SkipExp2 -Repeats 1
```

Pilot output files:

```text
benchmark/results/exp1_gate_overhead_20260530_182020.csv
benchmark/results/summary.md
```

Because `benchmark/results/*.csv` and `benchmark/results/*.md` are git-ignored, these files are local artifacts rather than tracked source files.

### Pilot results, `Repeats = 1`

| Metric | Baseline | Gate-enabled | Delta |
|---|---:|---:|---:|
| Mean session time (ms) | 10100.1 +/- 1252.6 | 14675.2 +/- 5413.1 | 45.3% |
| Mean gate-only latency (ms) | n/a | 10324.8 +/- 1178.0 | n/a |
| Mean gated build latency (ms) | n/a | 10876.0 +/- 798.2 | n/a |
| Mean gate output tokens | n/a | 29.7 +/- 13.1 | n/a |
| Type-A false-positive rate | n/a | 0.0% | n/a |
| Type-B block rate | n/a | 100.0% | n/a |
| Type-B safety pass-through error | n/a | 0.0% | n/a |
| Type-C review rate | n/a | 50.0% | n/a |

### Interpretation of pilot results

- The strict gate-to-build flow is operationally working.
- The gate blocks clear violations reliably in the pilot set: Type-B block rate = 100%.
- No compliant task was blocked or reviewed by the gate in the completed pilot: Type-A false-positive rate = 0%.
- The gate introduces measurable wall-clock overhead in this single-workstation OpenCode setup: about 45% in the pilot run.
- Type-C review behavior is partially conservative: one boundary case returned REVIEW and one returned BLOCK. This is acceptable for a pilot, but final reporting should describe boundary behavior as a policy-tuning zone rather than a failure.

### Pilot caveat

This is a pilot result with `Repeats = 1`. It should not be treated as publication-quality final data. Use it to validate instrumentation and workflow only.

### Formal candidate run completed, `Repeats = 5`

Command:

```powershell
cd D:\project\ea-harness
powershell -NoProfile -ExecutionPolicy Bypass -File "benchmark\scripts\run_benchmark.ps1" -SkipExp2 -Repeats 5
```

Output files:

```text
benchmark/results/exp1_gate_overhead_20260530_191248.csv
benchmark/results/summary.md
```

CSV row count check: 100 data rows, matching 10 tasks × 2 configurations × 5 repeats.

| Metric | Baseline | Gate-enabled | Delta |
|---|---:|---:|---:|
| Mean session time (ms) | 9875.5 +/- 853.3 | 16220.3 +/- 8029.7 | 64.2% |
| Mean gate-only latency (ms) | n/a | 11341.7 +/- 4928.5 | n/a |
| Mean gated build latency (ms) | n/a | 12196.4 +/- 5021.8 | n/a |
| Mean gate output tokens | n/a | 39.2 +/- 11.4 | n/a |
| Type-A false-positive rate | n/a | 0.0% | n/a |
| Type-B block rate | n/a | 100.0% | n/a |
| Type-B safety pass-through error | n/a | 0.0% | n/a |
| Type-C review rate | n/a | 30.0% | n/a |

Interpretation for revision draft:

- Exp1 now has a complete `Repeats = 5` candidate result suitable for manuscript drafting, subject to final author review.
- The strict C-layer gate preserved the key safety behavior in this run: no Type-A false positives and 100% Type-B blocking.
- The observed gate overhead increased relative to the pilot, from 45.3% to 64.2%, with high gate-enabled variance. This should be reported as workstation/testbed orchestration overhead rather than production SLA latency.
- Type-C review behavior remains a policy-tuning zone: 30.0% REVIEW, with the remainder conservatively classified outside REVIEW.

Optional confirmation run, only if a larger sample is needed:

```powershell
cd D:\project\ea-harness
powershell -NoProfile -ExecutionPolicy Bypass -File "benchmark\scripts\run_benchmark.ps1" -SkipExp2 -Repeats 10
```

## Experiment 2: temperature consistency

### Purpose

Measure whether near-deterministic validation (`temperature = 0.1`) improves decision stability compared with a more flexible setting (`temperature = 0.3`).

### Current implementation

Script:

```text
benchmark/scripts/exp2_temperature.py
```

Supported backends:

- Qwen / DashScope through OpenAI-compatible API
- DeepSeek through OpenAI-compatible API
- Anthropic API
- Dry-run mode for local smoke testing

### Recommended Qwen run

```powershell
cd D:\project\ea-harness\benchmark\scripts
$env:OPENAI_API_KEY = "your-qwen-or-dashscope-key"
$env:OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:BENCHMARK_MODEL = "qwen-plus"
.\run_benchmark.ps1 -SkipExp1 -Runs 10
```

### Recommended DeepSeek run

```powershell
cd D:\project\ea-harness\benchmark\scripts
$env:OPENAI_API_KEY = "your-deepseek-key"
$env:OPENAI_BASE_URL = "https://api.deepseek.com"
$env:BENCHMARK_MODEL = "deepseek-chat"
.\run_benchmark.ps1 -SkipExp1 -Runs 10
```

### Data to collect

The Exp2 CSV records:

```text
prompt_id, prompt_type, expected, temperature, run, wall_ms,
output_tokens, decision, correct, backend, model
```

The analysis summary reports:

- mean response time
- output tokens
- accuracy against expected PASS/BLOCK/REVIEW label
- repeated-decision agreement
- model used

### Previous failed Exp2 attempt

An initial DeepSeek-compatible Exp2 attempt was made after Exp1 completion, but the provider returned an authentication failure:

```text
openai.AuthenticationError: Error code: 401
Authentication Fails ... api key ... is invalid
```

No valid Exp2 result CSV was produced by this failed attempt. The `summary.md` file was regenerated from the existing Exp1 data only.

Required fix before rerunning Exp2:

1. Rotate/delete the exposed invalid key in the provider console.
2. Create a new valid DeepSeek API key.
3. In a fresh PowerShell session, set:

```powershell
cd D:\project\ea-harness\benchmark\scripts
$env:OPENAI_API_KEY = "<new-deepseek-key>"
$env:OPENAI_BASE_URL = "https://api.deepseek.com"
$env:BENCHMARK_MODEL = "deepseek-v4-flash"
```

Then rerun:

```powershell
.\run_benchmark.ps1 -SkipExp1 -Runs 10
```

### Exp2 completed, `Runs = 10`

Output files:

```text
benchmark/results/exp2_temperature_20260530_201852.csv
benchmark/results/summary.md
```

CSV row count check: 400 data rows, matching 20 validation prompts × 2 temperatures × 10 runs.

Model:

```text
deepseek-v4-flash
```

| Temperature | Prompt type | Mean RT (ms) | Output tokens | Accuracy | Agreement | Model |
|---:|---|---:|---:|---:|---:|---|
| 0.1 | boundary | 3090.7 +/- 921.6 | 247.0 +/- 58.5 | 48.0% | 70.0% | deepseek-v4-flash |
| 0.1 | compliant | 2480.6 +/- 475.0 | 177.1 +/- 50.1 | 87.5% | 95.0% | deepseek-v4-flash |
| 0.1 | violating | 2272.2 +/- 382.3 | 160.9 +/- 41.7 | 100.0% | 100.0% | deepseek-v4-flash |
| 0.3 | boundary | 3234.5 +/- 1170.7 | 248.8 +/- 56.6 | 56.0% | 72.0% | deepseek-v4-flash |
| 0.3 | compliant | 2406.9 +/- 461.2 | 174.2 +/- 51.3 | 91.2% | 93.8% | deepseek-v4-flash |
| 0.3 | violating | 2155.1 +/- 338.0 | 145.4 +/- 38.7 | 100.0% | 100.0% | deepseek-v4-flash |

Interpretation for revision draft:

- Clear violating prompts were stable across both temperatures: 100.0% accuracy and 100.0% agreement.
- Compliant prompts were also relatively stable, with high agreement at both temperatures: 95.0% at 0.1 and 93.8% at 0.3.
- Boundary prompts were intentionally harder and show lower accuracy/agreement, supporting the claim that ambiguous C-layer cases require review-policy calibration rather than direct automation.
- In this DeepSeek run, temperature 0.1 did not dominate temperature 0.3 on every metric; report this conservatively as evidence that near-deterministic validation improves or preserves stability for non-boundary cases, while boundary cases remain policy-sensitive.

## Manuscript use

The final manuscript should present these measurements as testbed-scale operational estimates, not production SLA benchmarks.

Suggested disclosure language:

> Measurements were obtained from the EA-Harness reference testbed running in an OpenCode agent environment on a single developer workstation. Session timing includes agent orchestration overhead. Task prompts were held fixed across runs; validation temperature was the primary varied runtime parameter. These measurements are testbed-scale operational estimates rather than production SLA benchmarks; enterprise deployments may differ in absolute latency while preserving the observed relative trade-offs.

## Next steps

1. Preserve the completed Exp1 and Exp2 artifacts: `exp1_gate_overhead_20260530_191248.csv`, `exp2_temperature_20260530_201852.csv`, and `summary.md`.
2. Optionally run Exp1 with `Repeats = 10` only if time/API quota permit and a lower-variance estimate is needed.
3. Optionally run Exp2 with a second provider/model, such as Qwen, only if the revision needs a cross-model robustness check.
4. Preserve the final `benchmark/results/*.csv` and `benchmark/results/summary.md` outside git or attach them to the revision working folder.
5. Use the final summary table in the revised Section 5 or 6 and in the point-by-point response to the editor.
6. After final results are confirmed and backed up, delete `D:\project\arch-harness` to avoid future workspace confusion.
