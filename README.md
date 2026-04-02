# ArchHarness

Enterprise architecture design and validation skill pack for **Claude Code** and **OpenCode**.

ArchHarness turns your AI coding assistant into a team of architecture specialists —
a requirements analyst, a senior architect, a paranoid security auditor, a committee reviewer,
and a technical writer — each invocable on demand with a single command.

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
| arch-security | `/arch-security` | `@arch-security` | Auth / credentials / network boundary deep-dive |
| arch-review | `/arch-review` | `@arch-review` | Committee gate: APPROVED / CONDITIONS / REJECTED |
| arch-optimize | `/arch-optimize` | `@arch-optimize` | Prioritized fix backlog (P0/P1/P2/P3) |
| arch-report | `/arch-report` | `@arch-report` | Confluence page / executive summary / risk brief |

## Workflow

```
Requirements → arch-design → draw in draw.io → arch-validate
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
git clone https://github.com/your-org/arch-harness.git
cd arch-harness
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

## Supported platforms

Standards in `standards/` cover three deployment targets:

- **Private cloud** — F5 ingress, east-west isolation via integration platform, PAW/ADFS
- **AWS** — Hub-Spoke VPC, ALB+WAF, API Gateway in Spoke VPC, IAM + Secrets Manager
- **Azure** — Hub-Spoke VNET, App Gateway WAF v2, APIM in Spoke VNET, Key Vault

All platform-specific names (API gateway, message bus, K8s platform) are read
from `config.yaml` — no hardcoding in rules or skill files.

## Project structure

```
arch-harness/
├── config.yaml              ← Edit this first
├── README.md
├── CLAUDE.md                ← Claude Code project rules
├── AGENTS.md                ← OpenCode project rules
├── ARCHITECTURE.md          ← Design rationale
├── input/                   ← Put your arch.yaml, PNGs, docs here
├── output/                  ← Generated files land here
├── standards/               ← Platform-agnostic rules and topology specs
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
