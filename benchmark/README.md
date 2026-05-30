# EA-Harness benchmark suite

Operational measurement scripts for the AI and Ethics minor revision of:

> **"Intelligence Beyond Knowledge: Control, Architecture, and the Structural Law of Artificial Agency"**

The suite measures two DIKCA/EA-Harness claims:

1. **Gate overhead**: the incremental wall-clock cost of adding a C-layer validation gate before A-layer execution.
2. **Temperature consistency**: latency, token use, accuracy, and repeated-decision agreement at `temperature=0.1` versus `temperature=0.3`.

Current migration and pilot-run status is tracked in [`EXPERIMENT_STATUS.md`](./EXPERIMENT_STATUS.md).

## Directory structure

```text
benchmark/
├── scripts/
│   ├── run_benchmark.ps1
│   ├── exp1_gate_overhead.ps1
│   ├── exp2_temperature.py
│   └── analyze_results.py
├── configs/
│   ├── opencode-baseline.json
│   └── opencode-gate.json
├── prompts/
│   ├── arch-gate-policy.txt
│   └── build-with-gate.txt
├── tasks/type-a|type-b|type-c/
├── validation_prompts.json
└── results/
```

## Quick start

```powershell
cd D:\project\ea-harness\benchmark\scripts

# Local smoke test, no API calls and no OpenCode calls
.\run_benchmark.ps1 -DryRun -Repeats 1 -Runs 1

# Exp1 with local OpenCode binary and DeepSeek model
.\run_benchmark.ps1 -SkipExp2 -Repeats 3

# Exp2 with Qwen OpenAI-compatible API
$env:OPENAI_API_KEY = "your-qwen-or-dashscope-key"
$env:OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:BENCHMARK_MODEL = "qwen-plus"
.\run_benchmark.ps1 -SkipExp1 -Runs 10

# Exp2 with DeepSeek OpenAI-compatible API
$env:OPENAI_API_KEY = "your-deepseek-key"
$env:OPENAI_BASE_URL = "https://api.deepseek.com"
$env:BENCHMARK_MODEL = "deepseek-chat"
.\run_benchmark.ps1 -SkipExp1 -Runs 10
```

## Experiment 1: strict gate-to-build overhead

`scripts/exp1_gate_overhead.ps1` compares:

- `baseline`: build agent classifies the task directly.
- `gate`: strict two-stage flow. The script first calls `arch-validator`; only `PASS` triggers `build`. `BLOCK` and `REVIEW` stop before A-layer execution.

The script clears inherited `OPENCODE*` environment variables during each child OpenCode run. This avoids the `Session not found` error caused by nested OpenCode desktop/session variables.

CSV columns include:

```text
task_id, task_type, config, run, expected_decision, gate_decision,
build_executed, gate_wall_ms, build_wall_ms, total_wall_ms,
gate_exit_code, build_exit_code, gate_input_tokens, gate_output_tokens,
build_input_tokens, build_output_tokens, final_decision
```

## Experiment 2: temperature consistency

`scripts/exp2_temperature.py` supports:

- `--backend openai` for Qwen / DeepSeek OpenAI-compatible APIs
- `--backend anthropic` for Anthropic
- `--backend auto` for environment-based selection

CSV columns include prompt type, expected decision, temperature, run number, wall-clock latency, output tokens, observed decision, correctness, backend, and model.

## Analysis

```powershell
python .\analyze_results.py --results-dir ..\results
```

The summary is written to:

```text
benchmark/results/summary.md
```

## Paper disclosure language

> Measurements were obtained from the EA-Harness reference testbed running in an OpenCode agent environment on a single developer workstation. Session timing includes agent orchestration overhead. Task prompts were held fixed across runs; validation temperature was the primary varied runtime parameter. These measurements are testbed-scale operational estimates rather than production SLA benchmarks; enterprise deployments may differ in absolute latency while preserving the observed relative trade-offs.
