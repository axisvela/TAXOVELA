# ArchHarness — Enterprise Architecture Design & Validation

> This file is the OpenCode native rules file (`AGENTS.md`).
> Claude Code reads the equivalent `CLAUDE.md` in the same directory.
> Both files are kept in sync — do not edit one without updating the other.

## What this is

ArchHarness is a multi-tool architecture skill pack for enterprise architecture work.
It works natively in **OpenCode** and **Claude Code**.
It turns the AI into a team of architecture specialists you summon on demand.

## Available agents and skills

### In OpenCode
Agents are invoked with `@agent-name`. Skills are loaded on-demand by the agent.

| Agent | Invoke | Role |
|-------|--------|------|
| arch-requirements     | `@arch-requirements`      | Orchestrator — interview + multi-source intake, outputs REQ.md + req.yaml |
| arch-req-from-diagram | `@arch-req-from-diagram` | Reader — draw.io / D2 / arch YAML / PNG (vision) → partial req.yaml |
| arch-req-from-doc     | `@arch-req-from-doc`     | Reader — PDF / DOCX / MD / TXT via LLM → partial req.yaml |
| arch-req-from-api     | `@arch-req-from-api`     | Reader — CMDB / ServiceNow / CSV → partial req.yaml |
| arch-req-merge        | `@arch-req-merge`        | Merger — combine partials, conflict detection, gap report | Requirements specialist — structured interview, outputs REQ.md + req.yaml |
| arch-validate | `@arch-validate` | Paranoid security architect — validates diagram, scores six dimensions |
| arch-design   | `@arch-design`   | Senior architect — designs from requirements, produces YAML blueprint |
| arch-enforce  | `@arch-enforce`  | CI enforcement gate — applies arch-gate-policy.yaml to validate JSON, emits PASS/WARN/BLOCK |
| arch-security | `@arch-security` | Security auditor — auth/credentials/network boundary deep-dive |
| arch-review   | `@arch-review`   | Review board — gate decision: APPROVED / CONDITIONS / REJECTED |
| arch-diagram   | `@arch-diagram`  | Diagram generator — YAML → draw.io + PNG |
| arch-report   | `@arch-report`   | Technical writer — Confluence pages, executive summaries, risk briefs |
| arch-optimize | `@arch-optimize` | Staff architect — prioritized fix backlog (P0/P1/P2/P3) |

### In Claude Code
Same agents are available as slash commands: `/arch-validate`, `/arch-design`, etc.

## Available skills

| Skill | Description |
|-------|---------|
| arch-validate | Paranoid security architect — validates a diagram image against your enterprise standards (loaded from config.yaml) |
| arch-design   | Senior architect — designs from requirements, picks patterns, generates YAML |
| arch-security | Security auditor — focused exclusively on auth, credentials, network boundaries |
| arch-review   | Architecture committee reviewer — checks standard compliance, scores dimensions |
| arch-diagram   | `@arch-diagram`  | Diagram generator — YAML → draw.io + PNG |
| arch-report   | `@arch-report`   | Technical writer — generates executive summaries and Confluence-ready docs |
| arch-optimize | Staff architect — identifies improvements, generates prioritized fix list |

## Configuration

All company-specific values (DC names, platform names, input/output paths) live in **`config.yaml`**
at the project root. Edit it before first use — see `CLAUDE.md` for full reference.

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
