# ArchHarness

Enterprise architecture design and validation skill pack for **Claude Code** and **OpenCode**.

ArchHarness turns your AI coding assistant into a team of architecture specialists —
a requirements analyst, a senior architect, a paranoid security auditor, a committee reviewer,
and a technical writer — each invocable on demand with a single command.

## Current benchmark status

This repository is the canonical working copy for the AI and Ethics minor-revision experiments:

```text
D:\project\ea-harness
```

The older `D:\project\arch-harness` working copy is deprecated and should only be treated as a temporary backup until final artifacts are archived.

Completed candidate benchmark results are tracked in [`benchmark/EXPERIMENT_STATUS.md`](./benchmark/EXPERIMENT_STATUS.md) and summarized locally in `benchmark/results/summary.md` when generated result files are present.

Current completed candidate artifacts:

```text
benchmark/results/exp1_gate_overhead_20260530_191248.csv
benchmark/results/exp2_temperature_20260530_201852.csv
benchmark/results/summary.md
```

Key results:

| Experiment | Run | Main result |
|---|---|---|
| Exp1 gate overhead | `Repeats = 5` | Baseline 9875.5 ms vs gate-enabled 16220.3 ms; overhead 64.2%; Type-B block rate 100.0%; Type-A false-positive rate 0.0% |
| Exp2 temperature consistency | DeepSeek `Runs = 10` | Violating prompts stable at both temperatures: 100.0% accuracy and 100.0% agreement; boundary prompts remain policy-sensitive |

Generated CSV and summary files under `benchmark/results/` are intentionally git-ignored. Preserve the final artifacts outside git or attach them separately to the manuscript revision package.

## What it does

| Agent / Skill | Claude Code | OpenCode | Role |
|---|---|---|---|
| arch-requirements | `/arch-requirements` | `@arch-requirements` | Structured interview → REQ.md + req.yaml |
| arch-req-from-diagram | `/arch-req-from-diagram` | `@arch-req-from-diagram` | draw.io / PNG → partial req.yaml |
| arch-req-from-doc | `/arch-req-from-doc` | `@arch-req-from-doc` | PDF / DOCX / MD → partial req.yaml |
| arch-req-from-api | `/arch-req-from-api` | `@arch-req-from-api` | CMDB / ServiceNow / CSV → partial req.yaml |
| arch-req-merge | `/arch-req-merge` | `@arch-req-merge` | Merge partials, detect conflicts, gap report |
| arch-design | `/arch-design` | `@arch-design` | Requirements → architecture YAML + draw.io guidance |
| arch-diagram | `/arch-diagram` | `@arch-diagram` | Architecture YAML → draw.io XML + PNG |
| arch-validate | `/arch-validate` | `@arch-validate` | Diagram image → scored JSON report (6 dimensions) |
| arch-enforce  | `/arch-enforce`  | `@arch-enforce`  | CI enforcement gate — PASS / WARN / BLOCK with exit code |
| arch-security | `/arch-security` | `@arch-security` | Auth / credentials / network boundary deep-dive |
| arch-review | `/arch-review` | `@arch-review` | Committee gate: APPROVED / CONDITIONS / REJECTED |
| arch-optimize | `/arch-optimize` | `@arch-optimize` | Prioritized fix backlog (P0/P1/P2/P3) |
| arch-report | `/arch-report` | `@arch-report` | Confluence page / executive summary / risk brief |

## Workflow

```
Requirements → arch-design → draw in draw.io → arch-validate
                                                      │
                                              arch-enforce gate
                                           PASS / WARN / BLOCK
                                                      │  if PASS/WARN
                                                      │
                                          arch-security  arch-review
                                                      │
                                               arch-optimize
                                                      │
                                               arch-report
```

## Setup

### 1. Clone

```bash
git clone https://github.com/your-org/ea-harness.git
cd ea-harness
```

### 2. Configure

Edit **`config.yaml`** to match your organisation's infrastructure:

```yaml
company:
  name: "Acme Corp"

datacenters:
  - id: "dc-primary"
    aliases: ["Primary DC", "Tokyo DC"]
    location: { city: "Tokyo", country: "JP" }
    model: "three-tier"
    zones: ["DMZ", "App Zone", "DB Zone"]

platforms:
  api_gateway: "Kong API Gateway"   # or WSO2, AWS API GW, Azure APIM…
  message_bus: "RabbitMQ"           # or Kafka, Azure Service Bus…
  k8s_platform: "Rancher"
  integration_platforms:
    - "Kong API Gateway"
    - "RabbitMQ"
    - "SFTP/MFT"

paths:
  input_dir: "./input"    # put arch.yaml, diagram PNGs, requirement docs here
  output_dir: "./output"  # generated drawio, PNG, REQ.md, reports go here
```

`config.yaml` is the **only file you need to edit**. All skills and Python tools
read from it at runtime — no other files contain hardcoded company values.

### 3. Create input/output directories

```bash
mkdir -p input output
```

### 4. Install Python dependencies (for diagram generation)

```bash
pip install pyyaml matplotlib
```

### 5. Open in Claude Code or OpenCode

**Claude Code:**
```bash
claude .
```
Skills under `.claude/skills/` are auto-registered as slash commands.

**OpenCode:**
```bash
opencode .
```
Agents under `.opencode/agents/` are available as `@agent-name`.

## Usage examples

### Design a new system

```
/arch-requirements
```
Claude conducts a structured interview and produces `REQ.md` + `req.yaml` in `output/`.

### Generate a diagram

```
/arch-design
```
Produces an architecture YAML blueprint. Then:

```bash
python tools/arch-diagram-gen/arch_diagram_gen.py -i input/arch.yaml
# → output/arch.drawio (open in draw.io or Confluence)
# → output/arch.png
```

### Validate a diagram

Attach your diagram PNG and run:
```
/arch-validate
```
Returns a scored JSON report with `must_fix`, `should_fix`, and `consider` findings.

### Full pipeline (OpenCode)

```
@arch-requirements   # gather requirements
@arch-design         # design the architecture
@arch-validate       # validate the diagram
@arch-enforce        # CI enforcement gate decision
@arch-security       # deep security audit
@arch-review         # committee gate decision
@arch-optimize       # prioritized fix backlog
@arch-report         # Confluence-ready documentation
```

## Scoring dimensions

| Dimension | Weight |
|---|---|
| Cloud / Network Completeness | 2.0 |
| Connectivity | 1.0 |
| Technical Component Completeness | 2.0 |
| Interaction / Integration | 2.0 |
| Security Compliance | 2.0 |
| Terminology Expression | 1.0 |
| **Total** | **10.0** |

## Validation rules

Rules live in `.claude/skills/arch-validate/rules/`:

| File | Series | Coverage |
|---|---|---|
| `diagram-rules.yaml` | V- | Shape, color, arrow direction, legend |
| `interaction-rules.yaml` | W- | Protocol, auth, integration platform placement |
| `security-rules.yaml` | S- | System auth, user auth, credential protection |
| `accuracy-rules.yaml` | E- | DC location, network segments, component completeness |
| `platform-rules.yaml` | — | AWS / Azure / private cloud specific rules |
| `compliance/terminology.yaml` | — | Cloud terms, ISO 27001 / TOGAF mapping |

## Enforcement gate

After validation, the **arch-enforce** gate applies policy thresholds
to the validation result and emits a CI-ready decision:

| Decision | Condition | Exit code |
|----------|-----------|-----------|
| **PASS** | Score ≥ 8.0 AND no `must_fix` issues | 0 |
| **WARN** | Score ≥ 6.0 AND < 8.0 AND no `must_fix` issues | 0 |
| **BLOCK** | Score < 6.0 OR any `must_fix` issue present | 1 |

The gate is designed for automated CI pipelines. For human review,
skip the gate and use `arch-review` directly.

Policy lives in two files:
- `standards/arch-gate-policy.yaml` — enforcement bounds, override conditions, meta-control
- `standards/ci-gate-spec.yaml` — per-dimension minimums, blocking rule IDs, profiles (financial / internet-facing / internal)

See `ARCHITECTURE.md` for the full control objective and audit trail
specification.

## Benchmark suite

The `benchmark/` directory contains the AI and Ethics revision measurement suite for:

- Exp1: strict C-layer gate-to-A-layer build overhead.
- Exp2: temperature consistency at `temperature=0.1` and `temperature=0.3`.

Current completed candidate results are documented in `benchmark/EXPERIMENT_STATUS.md` and summarized in `benchmark/results/summary.md` when local generated result files are present. Generated CSV/summary files are git-ignored; preserve final artifacts separately when preparing a manuscript revision package.

## Supported platforms

Standards in `standards/` cover three deployment targets:

- **Private cloud** — F5 ingress, east-west isolation via integration platform, PAW/ADFS
- **AWS** — Hub-Spoke VPC, ALB+WAF, API Gateway in Spoke VPC, IAM + Secrets Manager
- **Azure** — Hub-Spoke VNET, App Gateway WAF v2, APIM in Spoke VNET, Key Vault

All platform-specific names (API gateway, message bus, K8s platform) are read
from `config.yaml` — no hardcoding in rules or skill files.

## Project structure

```
ea-harness/
├── config.yaml              ← Edit this first
├── README.md
├── CLAUDE.md                ← Claude Code project rules
├── AGENTS.md                ← OpenCode project rules
├── ARCHITECTURE.md          ← Design rationale
├── benchmark/               ← Experiment scripts, prompts, status, and generated results
├── input/                   ← Put your arch.yaml, PNGs, docs here
├── output/                  ← Generated files land here
├── standards/               ← Platform-agnostic rules, topology specs, and gate policy
├── tools/
│   ├── config_loader.py     ← Shared config reader for Python tools
│   ├── arch-diagram-gen/    ← YAML → draw.io + PNG
│   └── arch-req-readers/    ← diagram / doc / API → req.yaml
├── .claude/skills/          ← Skill definitions (Claude Code slash commands)
└── .opencode/agents/        ← Agent definitions (OpenCode @agent-name)
```

## Requirements

- Claude Code or OpenCode
- Python 3.9+ with `pyyaml` and `matplotlib` (for diagram generation)
- draw.io desktop app (optional, for high-fidelity PNG export)

## License

MIT
