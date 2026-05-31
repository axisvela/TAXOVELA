# ArchHarness Architecture

This document explains why ArchHarness is built the way it is.
For setup and usage, see `CLAUDE.md` (Claude Code) or `AGENTS.md` (OpenCode).

## Core design principle

**Skills are roles, not functions.**

A single "validate everything" prompt produces mediocre output.
A paranoid security architect, a principal design architect, and a
committee reviewer each notice different things. ArchHarness gives you
explicit modes — the ability to tell the AI what kind of brain you want right now.

This is the same insight behind [gstack](https://github.com/garrytan/gstack):
constraining what Claude focuses on at each phase makes its output more
relevant and more consistent.

## Tool compatibility matrix

| Feature | Claude Code | OpenCode |
|---------|-------------|----------|
| Project rules | `CLAUDE.md` ✓ | `AGENTS.md` ✓ (`CLAUDE.md` as fallback) |
| Skill loading | auto via `.claude/skills/` ✓ | on-demand via `skill` tool ✓ |
| Slash commands | `/arch-validate` etc. ✓ | not applicable |
| `@agent` invocation | not applicable | `@arch-validate` etc. ✓ |
| Agent permissions | not applicable | `write: deny` / `write: ask` ✓ |
| Model per agent | not applicable | per-agent model selection ✓ |
| Supporting rule files | co-located in skill dir ✓ | co-located in skill dir ✓ |

## File structure

```
ea-harness/
├── CLAUDE.md           ← Claude Code project rules
├── AGENTS.md           ← OpenCode native project rules (CLAUDE.md as fallback)
├── opencode.json       ← OpenCode project config (default model)
├── ARCHITECTURE.md     ← This file
├── benchmark/          ← DIKCA/EA-Harness experiment scripts and status docs
│
├── .opencode/
│   └── agents/                       ← OpenCode @agent-name entry points
│       ├── arch-validate.md          ← mode: subagent, write: deny, temp: 0.1
│       ├── arch-design.md            ← mode: subagent, write: ask,  temp: 0.3
│       ├── arch-enforce.md           ← mode: subagent, write: deny, temp: 0.0
│       ├── arch-security.md          ← mode: subagent, write: deny, temp: 0.1
│       ├── arch-review.md            ← mode: subagent, write: deny, temp: 0.1
│       ├── arch-report.md            ← mode: subagent, write: ask,  temp: 0.2
│       └── arch-optimize.md          ← mode: subagent, write: ask,  temp: 0.2
│
├── .claude/
│   └── skills/                       ← Shared content (Claude Code + OpenCode)
│       ├── arch-validate/
│       │   ├── SKILL.md              ← Full 8-step validation logic + JSON schema
│       │   └── rules/                ← Co-located rule files, loaded as context
│       │       ├── diagram-rules.yaml       (V- series: shape/color/arrow/legend)
│       │       ├── interaction-rules.yaml   (W- series: protocol/auth/integration)
│       │       ├── security-rules.yaml      (S- series: auth/user-auth/credentials)
│       │       ├── accuracy-rules.yaml      (E- series: DC/network/component)
│       │       ├── platform-rules.yaml      (AWS/Azure/private-cloud specifics)
│       │       └── compliance/
│       │           └── terminology.yaml     (cloud terms + ISO27001/TOGAF mapping)
│       ├── arch-design/SKILL.md
│       ├── arch-enforce/SKILL.md       ← Enforcement gate logic + output schema
│       ├── arch-security/SKILL.md
│       ├── arch-review/SKILL.md
│       ├── arch-report/SKILL.md
│       └── arch-optimize/SKILL.md
│
└── standards/                        ← Shared reference data, read by all agents
    ├── private-cloud-standard.yaml   ← DCs, F5, zones, east-west, PAW/ADFS
    ├── aws-standard.yaml             ← Hub-Spoke, ALB/WAF, API Gateway in Spoke VPC, IAM+Secrets Mgr
    ├── azure-standard.yaml           ← Hub-Spoke, App GW, APIM, Key Vault
    ├── diagram-style.yaml            ← Full shape/color/arrow spec (from PDFs)
    ├── eval-weights.yaml             ← Scoring weights + industry profiles
    ├── arch-gate-policy.yaml         ← A-layer: enforcement bounds + meta-control scope
    └── ci-gate-spec.yaml             ← C-layer: CI gate thresholds + dimension minimums + profiles
```

## Two layers, one content source

The structure has two complementary layers that avoid duplication:

**`.opencode/agents/`** is the OpenCode-native entry point. Each file sets
`mode`, `permissions`, `model`, and `temperature` — capabilities Claude Code
doesn't have. Validation and review agents are fully read-only (`write: deny`).
Design and optimize agents use `write: ask` so they confirm before touching files.
Each agent's prompt is intentionally short: it names the role and points to the
relevant `SKILL.md` for the full procedure.

**`.claude/skills/`** is the shared content layer. It holds the complete prompts,
step-by-step procedures, output schemas, and rule files. Both tools read this:
Claude Code registers each directory as a slash command; OpenCode loads the
content via the `skill` tool when an agent requests it. Rule YAML lives co-located
inside `arch-validate/rules/` — available as file context without path guessing.

This means the full validation logic lives in exactly one place (`SKILL.md` +
rule files), and both tools consume it without duplication.

## Why rules stay in YAML, not embedded in SKILL.md

Rules YAML files serve two roles simultaneously:

1. **LLM context** — precise rule definitions, check targets, and scoring formulas
   that the model reads when validating a diagram.

2. **Future machine validation** — the same YAML can drive a Rust/Python rule
   engine for static checks on YAML architecture descriptions (not just
   image-based LLM checks).

Embedding rules in SKILL.md would make the prompt too long and break machine reuse.

## Why six separate agents instead of one

`arch-validate` is comprehensive — it checks everything and scores six dimensions.
But running the full validator when you only suspect a security gap is wasteful
and produces unfocused output. Each agent is a different cognitive mode:

- `arch-security` thinks in attack paths, not compliance checklists. Faster and
  more aggressive. Use it when you already know something smells wrong.
- `arch-review` produces a gate decision with committee-style narrative. Output
  for a human review board, not a CI pipeline.
- `arch-optimize` turns findings into a sprint backlog. Pure planning mode.
- `arch-report` is a technical writer. It doesn't evaluate — it documents.

## The workflow

```
Requirements → @arch-design (or /arch-design)
                    │  YAML blueprint + draw.io guidance
                    ▼
             Draw in draw.io, export PNG
                    │
                    ▼
             @arch-validate
                    │  JSON report (score + issues)
                    ▼
     ╔═════════════════════════════════════════╗
     ║         arch-enforce gate              ║
     ║                                         ║
     ║  Reads: validate_result.json +          ║
     ║         arch-gate-policy.yaml           ║
     ║                                         ║
      ║  score ≥ 8.0 AND must_fix == 0          → PASS ║
      ║  score ≥ 6.0 AND < 8.0 AND must_fix == 0 → WARN ║
      ║  score < 6.0  OR  must_fix > 0           → BLOCK║
     ║                                         ║
     ║  Output: enforce_result.json +          ║
     ║          exit_code (0 = PASS, 1 = BLOCK)║
     ╚═════════════════════════════════════════╝
                    │  if PASS or WARN
                    ▼
     @arch-security               @arch-review
     (attack paths,               (APPROVED /
      finding list)                CONDITIONS /
            │                      REJECTED)
            └──────────┬───────────┘
                       ▼
                @arch-optimize
                (P0/P1/P2/P3 backlog)
                       │
                       ▼
                @arch-report
                (Confluence / exec summary / risk brief)
```

The validation gate is a CI-native step — it runs automatically after
`arch-validate` in a pipeline and produces a machine-readable binary
decision. For human review, bypass the gate and use `arch-review`
directly.

## Validation gate

### Control objective

The gate exists to enforce a minimum quality and compliance bar before
architecture artifacts can progress through a delivery pipeline. It
implements the DIKCA framework transition from **Knowledge** (advisory
rule files in `arch-validate/rules/` and `standards/*.yaml`) to
**Control** (mandatory binary decision that blocks non-compliant
architectures from moving forward).

The gate is an automated compliance officer, not a reviewer. It
mechanically applies pre-configured thresholds to a structured
validation report and emits one of three decisions — no interpretation,
no judgement, no override without formal process.

### Decision criteria

The gate reads two inputs:
1. **`validate_result.json`** — the output of `arch-validate`, containing
   overall score, dimension scores, gate decision recommendation, and
   a list of `must_fix`, `should_fix`, and `consider` issues.
2. **`arch-gate-policy.yaml`** — the A-layer policy file that defines
   enforcement bounds and who may change them.

The decision matrix is applied in order:

| Condition | Result | Exit code |
|-----------|--------|-----------|
| Total score < 6.0 (`block_threshold`) | **BLOCK** | 1 |
| Any `must_fix` issue present (`must_fix_zero_required: true`) | **BLOCK** | 1 |
| Total score >= 6.0 AND score < 8.0 (`warn_threshold`) | **WARN** | 0 |
| Total score >= 8.0 AND no `must_fix` issues | **PASS** | 0 |

**Profile-specific overrides** (from `ci-gate-spec.yaml`):

| Profile | Overall minimum | Notable dimension minimums |
|---------|----------------|---------------------------|
| Default | 6.0 (grade C) | Security_Compliance: 6.0, Interaction_Integration: 6.0 |
| Financial | 7.0 | Security_Compliance: 8.0, zero critical must_fix tolerance |
| Internet-facing | 7.0 | Security_Compliance: 7.5, Interaction_Integration: 7.0 |
| Internal system | 5.5 | Security_Compliance: 5.0, Connectivity: 3.0 |

**Blocking rule IDs** — regardless of score, the following rule
violations cause an automatic BLOCK:
- `S-001` — system has no authentication on any connection
- `S-004` — no user authentication declared
- `E-PC-001` — no F5 on private cloud ingress
- `E-AWS-005` — no WAF + API Gateway on external API
- `W-006` — (internet-facing profile only)

### Audit trail

Every gate invocation writes a structured record to
**`enforce_result.json`** with the following fields:

| Field | Description |
|-------|-------------|
| `decision` | PASS, WARN, or BLOCK |
| `exit_code` | 0 (pass) or 1 (block / fail CI step) |
| `policy_version` | Version string from `arch-gate-policy.yaml` |
| `applied_rules` | List of rule IDs that were evaluated |
| `override_available` | Whether an override route exists |
| `override_requires` | Conditions for override (committee approval + Jira ticket) |
| `audit_entry.timestamp` | ISO 8601 timestamp of enforcement event |
| `audit_entry.diagram_hash` | Content hash of the validated diagram |
| `audit_entry.score` | Total score from `validate_result.json` |
| `audit_entry.decision` | Decision emitted (duplicated for queryability) |

Override requests are logged separately to **`output/override-log.yaml`**
with a retention period of 12 months. Each override must include the
approver name and role, a written rationale, an expiry date, and a
remediation ticket link.

### Meta-control (who guards the gate?)

Changes to the enforcement policy itself require:
- Approval from `architecture-committee` AND `cto-office`
- Minimum 2 approvals
- Submission via pull request to main with required reviewers
- Automatic notification to `security-team` and `cto-office`

This ensures the gate cannot be weakened without visibility and
consensus from both the architecture and security functions.

## Standards provenance

Standards in `standards/` encode topology and security rules for three deployment targets:
AWS, Azure, and private cloud. They were authored to reflect common enterprise patterns
(Hub-Spoke networking, DMZ/App/DB zone segmentation, API gateway placement, east-west
isolation via integration platforms) aligned with ISO 27001 and TOGAF conventions.

Company-specific values — DC names, platform names, classification labels — are **not**
stored in `standards/`. They live in `config.yaml` and are injected at runtime.

To adapt the standards to your organisation's internal guidelines:
1. Edit `config.yaml` to set your DC list, platform names, and classification prefix.
2. If your topology rules differ from the defaults (e.g. a different ingress model),
   update the relevant YAML under `standards/` and bump its `version` field.
3. For platform-specific rules, edit `.claude/skills/arch-validate/rules/platform-rules.yaml`.
