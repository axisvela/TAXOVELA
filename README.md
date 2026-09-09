# ArchHarness

Enterprise architecture design and validation skill pack for **Claude Code**, **OpenCode**,
**Codex**, **GitHub Copilot**, and **Cursor**.

ArchHarness turns your AI coding assistant into a team of architecture specialists —
a requirements analyst, a senior architect, a paranoid security auditor, a committee reviewer,
and a technical writer — each invocable on demand with a single command.

> **Not yet another README-only repo.** `archharness` ships a real CLI
> (`python -m archharness`), a multi-project workspace layout, and platform skills that
> load enterprise values from a single config file.

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
git clone https://github.com/axisrobo/ea-harness.git
cd ea-harness
```

### 2. Configure the organisation profile

Edit **`config.yaml`** at the repository root to match your organisation's
infrastructure (DC names, platform names, classification prefix). Skills and
LLM rules load these values at runtime.

```yaml
company:
  name: "Acme Corp"

datacenters:
  - id: "dc-primary"
    aliases: ["Primary DC", "Tokyo DC"]
    location: { city: "Tokyo", country: "JP" }
    zones: ["DMZ", "App Zone", "DB Zone"]

platforms:
  api_gateway: "Kong API Gateway"   # or WSO2, AWS API GW, Azure APIM…
  message_bus: "RabbitMQ"           # or Kafka, Azure Service Bus…
  k8s_platform: "Rancher"
  integration_platforms:
    - "Kong API Gateway"
    - "RabbitMQ"
    - "SFTP/MFT"
```

> If you manage more than one architecture project, put these company values
> in `config.yaml` once and create **isolated projects** (next step). Per-project
> inputs and outputs live under `projects/<id>/`.

### 3. Create a workspace and a project

One workspace can hold many architecture projects. Each project has its own
`input/`, `working/`, and `output/` trees so files never bleed between projects.

```bash
# POSIX / macOS / Linux
python -m archharness init-workspace .
python -m archharness init-project payments --name "Payments Platform" --default
python -m archharness list-projects
```

```powershell
# Windows PowerShell
python -m archharness init-workspace .
python -m archharness init-project payments --name "Payments Platform" --default
python -m archharness list-projects
```

This creates:

```text
projects/payments/
├─ project.yaml               # id, name, platform, data classification
├─ input/                     # documents, diagrams, api exports, requirements
├─ working/                   # intermediate files
└─ output/                    # requirements, designs, diagrams, validation, reports
```

`project.yaml` and all generated files are git-ignored — only `project.yaml` and
`README.md` are tracked when you choose to commit them.

When you work inside a project directory, tools and skills auto-detect the active
project (`--project` also works from anywhere in the workspace).

### 4. Install Python dependencies

```bash
pip install -e ".[all]"
# or minimal: pip install pyyaml matplotlib
```

### 5. Open in your AI coding tool

**Claude Code**
```bash
claude .
```
Skills under `.claude/skills/` register as `/arch-*` slash commands.

**OpenCode**
```bash
opencode .
```
Agents under `.opencode/agents/` register as `@arch-*` agents.

**Codex / GitHub Copilot / Cursor**
Point the tool at this repository root. `AGENTS.md` is read by all three;
Codex and newer Cursor/Copilot builds discover skills under `.claude/skills/`.

> **Tip:** working directory should be the repository root (or a project
> directory) so skills, tools, and `config.yaml` are found automatically.

## Usage examples

### Design a new system

```
/arch-requirements
```
Claude conducts a structured interview and produces `REQ.md` + `req.yaml`
in the active project's `output/requirements/`.

### Generate a diagram

```
/arch-design
```
Produces an architecture YAML blueprint. Then, from inside the project directory:

```bash
python ../../tools/arch-diagram-gen/arch_diagram_gen.py -i arch.yaml
# → output/diagrams/arch.drawio
```

Or explicitly target a project from anywhere in the workspace:

```bash
python tools/arch-diagram-gen/arch_diagram_gen.py -i projects/payments/input/arch.yaml \
  --project payments
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
├── config.yaml              ← Organisation profile — edit this first
├── README.md
├── CLAUDE.md                ← Claude Code project rules
├── AGENTS.md                ← OpenCode / Codex / Copilot / Cursor project rules
├── ARCHITECTURE.md          ← Design rationale
├── archharness/             ← `python -m archharness` workspace & project CLI
├── benchmark/               ← Experiment scripts, prompts, status, and generated results
├── input/                   ← Legacy single-project input (optional)
├── output/                  ← Legacy single-project output (optional)
├── projects/<id>/           ← Workspace projects (init with `archharness init-project`)
├── standards/               ← Platform-agnostic rules, topology specs, and gate policy
├── tools/
│   ├── config_loader.py     ← Shared config reader for Python tools
│   ├── arch-diagram-gen/    ← YAML → draw.io + PNG
│   └── arch-req-readers/    ← diagram / doc / API → req.yaml
├── tests/                   ← pytest suite
├── .claude/skills/          ← Skill definitions (Claude Code slash commands)
└── .opencode/agents/        ← Agent definitions (OpenCode @agent-name)
```

## Requirements

- Claude Code, OpenCode, Codex, GitHub Copilot, or Cursor
- Python 3.10+ (`pip install -e ".[all]"` pulls everything; `pyyaml matplotlib` is the minimal set)
- draw.io desktop app (optional, for high-fidelity PNG export)

## License

MIT — see `LICENSE`.
