# ArchHarness — Enterprise Architecture Design & Validation

> This file is the Claude Code rules file (`CLAUDE.md`). OpenCode, Codex, GitHub
> Copilot, and Cursor read the equivalent `AGENTS.md`. Both files carry the same
> shared body — the block delimited by `archharness-shared` markers below — and CI
> fails when the two drift (`tests/test_rules_files_in_sync.py`).

<!-- archharness-shared:start -->
## What this is

ArchHarness is a multi-tool architecture skill pack for enterprise architecture
work. It runs natively in **Claude Code** and **OpenCode** and is discovered by
**Codex**, **GitHub Copilot**, and **Cursor**. It turns the AI into a team of
architecture specialists you summon on demand, backed by a real CLI
(`python -m archharness`), versioned contracts, and a deterministic gate.

## Available agents and skills

| Agent | Claude Code | OpenCode | Role |
|---|---|---|---|
| arch-workflow | `/arch-workflow` | `@arch-workflow` | Pipeline gatekeeper — enforces stage order and the PASS/WARN/BLOCK gate; blocks skipping |
| arch-requirements | `/arch-requirements` | `@arch-requirements` | Orchestrator — interview + multi-source intake → REQ.md + req.yaml |
| arch-req-from-diagram | `/arch-req-from-diagram` | `@arch-req-from-diagram` | Reader — draw.io / D2 / arch YAML / PNG (vision) → partial req.yaml |
| arch-req-from-doc | `/arch-req-from-doc` | `@arch-req-from-doc` | Reader — PDF / DOCX / MD / TXT via LLM → partial req.yaml |
| arch-req-from-api | `/arch-req-from-api` | `@arch-req-from-api` | Reader — CMDB / ServiceNow / CSV → partial req.yaml |
| arch-req-merge | `/arch-req-merge` | `@arch-req-merge` | Merger — combine partials, conflict detection, gap report |
| arch-design | `/arch-design` | `@arch-design` | Senior architect — requirements → architecture YAML blueprint |
| arch-diagram | `/arch-diagram` | `@arch-diagram` | Diagram generator — Architecture YAML → draw.io / D2 / PNG / PlantUML |
| arch-validate | `/arch-validate` | `@arch-validate` | Paranoid security architect — diagram → scored JSON (6 dimensions) |
| arch-enforce | `/arch-enforce` | `@arch-enforce` | CI enforcement gate — gate policy → PASS/WARN/BLOCK + exit code |
| arch-security | `/arch-security` | `@arch-security` | Security auditor — auth / credentials / network boundary deep-dive |
| arch-review | `/arch-review` | `@arch-review` | Review board — APPROVED / APPROVED WITH CONDITIONS / REJECTED |
| arch-optimize | `/arch-optimize` | `@arch-optimize` | Staff architect — prioritized fix backlog (P0–P3) |
| arch-report | `/arch-report` | `@arch-report` | Technical writer — Confluence pages, executive summaries, risk briefs |

## Configuration

All company-specific values (DC names, platform names, classification labels)
live in **`config.yaml`** at the repository root. Edit it before first use — it is
the only file you need to change. Skills and rules load these values at runtime:
`company.name`, `datacenters` (names, locations, zones), and `platforms` (API
gateway, message bus, K8s platform).

## Multi-project workspace

One checkout supports many isolated projects. Create projects with the CLI
(`python -m archharness`): `init-workspace`, `init-project`, `list-projects`,
`doctor`. Each project lives under `projects/<id>/` with its own `input/`,
`working/`, `output/`, and a `project.yaml` describing `id`, `name`, `platform`,
and `data_classification`.

Working session rules:
- If the cwd is inside `projects/<id>/`, that project is the **active project**.
- Use `--project <id>` to select a project from anywhere in the workspace.
- Inputs resolve against the active project `input/`; generated files land in the
  active project `output/` (subfolders `requirements/`, `designs/`, `diagrams/`,
  `validation/`, `reports/`).
- Project data dirs are git-ignored. Do not scatter generated files in the
  repository root when a workspace project is active — target the project `output/`.

## Standards in scope

All skills load company-specific values from `config.yaml` at runtime. The
`standards/` directory holds the platform-agnostic rules and topology
requirements. Six deployment targets are supported, each with a standard, a
placement-rule family (`E-*`), a design template, and a worked example:

- `private-cloud-standard.yaml` — F5 ingress model, east-west isolation, PAW, DC zone models
- `aws-standard.yaml` — Hub-Spoke, ALB/WAF, API Gateway in Spoke VPC, IAM + Secrets Manager
- `azure-standard.yaml` — Hub-Spoke, App Gateway WAF v2, APIM in Spoke VNET, Key Vault
- `gcp-standard.yaml` — Shared VPC host + service projects, global HTTPS LB + Cloud Armor, Cloud NAT, CMEK (`E-GCP-*`)
- `aliyun-standard.yaml` — resource directory + central VPC, Anti-DDoS → WAF → SLB, CEN, RAM roles + STS (`E-ALI-*`)
- `microsoft-saas-standard.yaml` — black-box tenant/environment containers, one boundary component, Entra ID + DLP; Microsoft 365 / Power Platform / Dynamics 365 (`E-MS-*`)

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
- `platform-rules.yaml` — platform-specific rules for private cloud, AWS, Azure, GCP, Alibaba Cloud, Microsoft SaaS
- `compliance/terminology.yaml` — cloud terminology and ISO27001/TOGAF mapping

## Scoring

Six dimensions, 10 points total:
- Cloud_Network_Completeness (2.0), Connectivity (1.0), Technical_Component_Completeness (2.0)
- Interaction_Integration (2.0), Security_Compliance (2.0), Terminology_Expression (1.0)

## Usage pattern

1. **Design** → run the design skill to generate architecture YAML from requirements
2. **Validate** → run the validation skill on the diagram image for a scored JSON report
3. **Enforce** → run the enforce skill to apply the CI gate policy (or skip for human review)
4. **Deep-dive security** → run the security skill for an auth/credential/network boundary audit
5. **Standards check** → run the review skill for committee-style compliance scoring
6. **Fix it** → run the optimize skill for prioritized improvement suggestions
7. **Document it** → run the report skill for an executive summary or Confluence page

## Pipeline discipline (mandatory order)

Architecture stages run in the order defined by `standards/workflow.yaml`:

```
Requirements → design → draw (export PNG) → validate → enforce gate
                                                    │ PASS / WARN → security + review
                                                    │ BLOCK       → pipeline stops
security + review → optimize → report
```

Gate rules (fail-closed, enforced by the `arch-workflow` gatekeeper):
- A stage starts only when every artifact in its `requires` list exists in the
  active project `output/`/`working/`.
- Never fabricate predecessor outputs and never skip a stage.
- After the enforce gate, continue only on PASS or WARN. BLOCK requires fixing
  the findings and re-running validate → enforce.
- Invoke `arch-workflow status` / `arch-workflow can <stage>` (`@arch-workflow`
  in OpenCode) before starting a stage when in doubt.
<!-- archharness-shared:end -->

## Claude Code specifics

**Discovery.** Claude Code registers each directory under `.claude/skills/` that
contains a `SKILL.md` as a `/arch-*` slash command — the Claude Code Agent Skills
open standard.

**Install from the chat window (plugin marketplace).**

```
/plugin marketplace add axisrobo/ea-harness
/plugin install archharness@archharness-marketplace
/reload-plugins
```

Plugin skills are namespaced `/archharness:arch-validate`, `/archharness:arch-design`,
etc. For shared resources (`standards/`, `tools/`, `config.yaml`) run
`pip install "archharness[all]"` once, or set `ARCHHARNESS_HOME` to a checkout.

**Diagram tool.** `tools/arch-diagram-gen/arch_diagram_gen.py -i arch.yaml` is
equivalent to `python -m archharness diagram -i arch.yaml`; both write into the
active project `output/diagrams/` and emit draw.io, D2, PlantUML, and PNG.

**If skills aren't loading**, confirm the working directory is the repository root
(or a project directory) and that `.claude/skills/` exists.
