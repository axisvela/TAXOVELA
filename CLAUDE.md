# ArchHarness — Enterprise Architecture Design & Validation

## What this is

ArchHarness is a Claude Code skill pack for enterprise architecture work.
It turns Claude into a team of architecture specialists you summon on demand.

## Available skills

| Skill | Command | Role |
|-------|---------|------|
| arch-requirements   | `/arch-requirements`    | Orchestrator — interview + multi-source intake, outputs REQ.md + req.yaml |
| arch-req-from-diagram | `/arch-req-from-diagram` | Reader — draw.io / D2 / arch YAML / PNG (vision) → partial req.yaml |
| arch-req-from-doc  | `/arch-req-from-doc`   | Reader — PDF / DOCX / MD / TXT via LLM → partial req.yaml |
| arch-req-from-api  | `/arch-req-from-api`   | Reader — CMDB / ServiceNow / CSV → partial req.yaml |
| arch-req-merge     | `/arch-req-merge`      | Merger — combine partials, conflict detection, gap report | Requirements specialist — structured interview, outputs REQ.md + req.yaml for arch-design |
| arch-validate | `/arch-validate` | Paranoid security architect — validates a diagram image against all rules |
| arch-design   | `/arch-design`   | Senior architect — designs from requirements, picks patterns, generates YAML |
| arch-diagram  | `/arch-diagram`  | Diagram generator — converts Architecture YAML → draw.io file + PNG |
| arch-enforce  | `/arch-enforce`  | CI enforcement gate — applies arch-gate-policy.yaml to validate JSON, emits PASS/WARN/BLOCK |
| arch-security | `/arch-security` | Security auditor — focused exclusively on auth, credentials, network boundaries |
| arch-review   | `/arch-review`   | Architecture committee reviewer — checks standard compliance, scores dimensions |
| arch-report   | `/arch-report`   | Technical writer — generates executive summaries and Confluence-ready docs |
| arch-optimize | `/arch-optimize` | Staff architect — identifies improvements, generates prioritized fix list |

## Configuration

All company-specific values live in **`config.yaml`** at the project root.
Edit it before first use — this is the only file you need to change.

Key fields:
- `company.name` — used in report headers and classification labels
- `datacenters` — your DC names, locations, and network zones
- `platforms` — API gateway, message bus, K8s platform names
- `paths.input_dir` / `paths.output_dir` — default input/output directories for Python tools

```yaml
# config.yaml (excerpt)
company:
  name: "Acme Corp"
datacenters:
  - id: "dc-primary"
    aliases: ["Primary DC"]
    location: { city: "Tokyo", country: "JP" }
    zones: ["DMZ", "App Zone", "DB Zone"]
platforms:
  api_gateway: "Kong API Gateway"
  message_bus: "RabbitMQ"
paths:
  input_dir: "./input"
  output_dir: "./output"
```

## Diagram generation tool

`tools/arch-diagram-gen/` — Python tool that converts Architecture YAML to draw.io XML and PNG.

```bash
# Install
pip install pyyaml matplotlib

# Generate (output goes to config.yaml > paths.output_dir by default)
python tools/arch-diagram-gen/arch_diagram_gen.py -i input/arch.yaml

# Override output explicitly
python tools/arch-diagram-gen/arch_diagram_gen.py -i arch.yaml -o out.drawio --png out.png

# Use a specific config file
python tools/arch-diagram-gen/arch_diagram_gen.py -i arch.yaml --config /path/to/config.yaml
```

See `tools/arch-diagram-gen/README.md` and `arch-schema-reference.yaml` for full docs.
The tool produces standard architecture shapes: hexagons for F5/FW, parallelograms for
API gateways, cylinders for databases, dashed zones, status colors.

## Standards in scope

All skills load company-specific values from `config.yaml` at runtime.
The `standards/` directory holds the platform-agnostic rules and topology requirements:
- `private-cloud-standard.yaml` — F5 ingress model, east-west isolation, PAW, DC zone models
- `aws-standard.yaml` — Hub-Spoke, ALB/WAF, API Gateway in Spoke VPC, IAM + Secrets Manager
- `azure-standard.yaml` — Hub-Spoke, App Gateway WAF v2, APIM in Spoke VNET, Key Vault

## Diagram shape spec

`standards/diagram-style.yaml` — full shape, color, arrow, and metadata rules from:
- Private Cloud Architecture Diagram Shape Specification v1.0
- Technical Architecture Diagram Specification v1.0

## Validation rules

Skills load rules from `.claude/skills/arch-validate/rules/`:
- `diagram-rules.yaml` — V- series: shape, color, arrow, legend
- `interaction-rules.yaml` — W- series: arrow direction, protocol, integration platform
- `security-rules.yaml` — S- series: auth, user auth, credential protection
- `accuracy-rules.yaml` — E- series: DC location, network segments, component completeness
- `platform-rules.yaml` — AWS/Azure/private-cloud platform-specific rules
- `compliance/terminology.yaml` — cloud terminology and ISO27001/TOGAF mapping

## Scoring

Six dimensions, 10 points total:
- Cloud_Network_Completeness (2.0), Connectivity (1.0), Technical_Component_Completeness (2.0)
- Interaction_Integration (2.0), Security_Compliance (2.0), Terminology_Expression (1.0)

## Usage pattern

1. **Design** → `/arch-design` to generate architecture YAML from requirements
2. **Validate** → `/arch-validate` with diagram image to get scored JSON report
3. **Deep-dive security** → `/arch-security` for auth/credential/network boundary audit
4. **Standards check** → `/arch-review` for committee-style compliance scoring
5. **Fix it** → `/arch-optimize` for prioritized improvement suggestions
6. **Document it** → `/arch-report` for executive summary or Confluence page

## If skills aren't loading

Check that `.claude/skills/` is on the project path. Skills follow the
Claude Code Agent Skills open standard — each directory under `.claude/skills/`
with a `SKILL.md` is automatically registered as a slash command.

## OpenCode usage

This project also supports OpenCode. Use `@agent-name` instead of `/skill-name`:

```
@arch-validate   →  validate a diagram image
@arch-design     →  design from requirements
@arch-security   →  security deep-dive
@arch-review     →  committee gate decision
@arch-optimize   →  prioritized fix backlog
@arch-report     →  Confluence page / exec summary
```

Agent definitions live in `.opencode/agents/`. They point to the same
`SKILL.md` files in `.claude/skills/` that Claude Code uses.
The `AGENTS.md` in this directory is the OpenCode-native equivalent of this file.
