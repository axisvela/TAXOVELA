# ArchHarness Roadmap

This is the repository-level roadmap. It covers product capability, engineering
quality, and reference content; it is deliberately ordered by dependency rather
than by calendar date. Scope can change as enterprise standards and tool-host
capabilities evolve.

For the detailed draw.io layout and routing plan, see
[`tools/arch-diagram-gen/DIAGRAM_GENERATION_ANALYSIS.md`](../tools/arch-diagram-gen/DIAGRAM_GENERATION_ANALYSIS.md).

## Product direction

ArchHarness should make the enterprise-architecture lifecycle repeatable and
auditable: gather traceable requirements, produce a structured design, render a
reviewable diagram, validate it against standards, enforce a policy decision,
and generate the security, review, remediation, and reporting evidence that
follows from that decision.

## Current baseline

The following capabilities are in place:

- multi-project workspace and `archharness` CLI;
- requirements readers (document, diagram, API/CSV), merge, and `req/v2`
  validation;
- architecture-YAML design flow and platform standards for private cloud, AWS,
  and Azure;
- draw.io, D2, PlantUML, and PNG diagram outputs;
- artifact-gated workflow: requirements → design → draw → validate → enforce →
  security/review → optimize → report;
- deterministic enforcement (`PASS` / `WARN` / `BLOCK`) and specialist skills;
- multi-tool packaging for Claude Code, OpenCode, Codex, Copilot, and Cursor;
- a complete `req/v2` worked reference in example 06.

## Priorities

### P0 — Trustworthy release baseline

**Goal:** ensure generated artifacts, skill mirrors, examples, and releases are
internally consistent and safe to consume.

| Initiative | Deliverable / acceptance criteria |
|---|---|
| Artifact integrity | Done: `check_manifest()` reports structured `invalid-manifest` / `missing-file` / `digest-mismatch` findings, `archharness workflow verify [--json]` exposes them, and the `can` / `status` / `complete` gates re-verify required artifacts against their recorded SHA-256 before allowing a stage. `tests/test_example_artifacts.py` guards the shipped examples against portable-path or digest drift. |
| Packaging and host parity | CI verifies the generated `.agents/skills/` mirror, plugin metadata, package resources, and CLI `doctor` on supported Python versions. |
| Example governance | Done for the shipped examples: recorded artifact paths are project-relative and hash-verified, `tests/test_example_artifacts.py` enforces manifest integrity plus the registry codes-only name policy in CI, and each example documents that its reference image is unscrubbed and restricted. |
| Release discipline | Changelog and compatibility notes live in `CHANGELOG.md` (released history, unreleased section, and the pinned interfaces table). Tags stay reproducible through the release workflow's tag/version gate plus the wheel smoke test. |

### P1 — Diagram quality and reviewability

**Goal:** make the generated technical diagram usable without manual edge cleanup.

| Initiative | Deliverable / acceptance criteria |
|---|---|
| Deterministic draw.io edge router | Select ports, emit Manhattan waypoints, use region/zone gutters for cross-boundary flows, avoid component rectangles, and retain automatic-routing fallback. |
| Route regression suite | Unit tests cover routes and obstacles; representative PNGs (including example 06 and a multi-DC fixture) are visually reviewed or image-regression-tested. |
| Diagram semantics | Continue policy-driven roles, lifecycle/status colour, protocol/auth legends, and accessibility/readability improvements without relying on name matching. |
| Shape coverage | Add shapes only when a platform standard requires them, with generator, PNG renderer, D2 output, legend, and validation coverage together. |

### P2 — Requirements and design model maturity

**Goal:** make the architecture model complete, traceable, and suitable for
automation rather than a diagram-only representation.

| Initiative | Deliverable / acceptance criteria |
|---|---|
| `req/v2` adoption | Done for every example with source input: examples 01–06 measure `reqv2-complete`; 07–08 remain scaffolds awaiting input. `archharness migrate-status` and the example matrix are verified in CI, and the site-qualified diagram id convention is documented. |
| Traceability | Started: `trace-check` joins req/v2 inventory to typed blueprint nodes and verifies CN/NA site-qualified nodes have a matching deployment. Remaining: carry the same evidence through diagrams, validation findings, and remediation backlog. |
| Schema evolution | Started: contracts are versioned by identity (`req/v2`), and `archharness schema-check --baseline <ref|dir>` classifies a change as breaking / additive / cosmetic, failing a breaking change under an existing id so it must ship as a new one. Remaining: a documented migration path when a new id lands. |
| Platform patterns | Private cloud, AWS, and Azure are joined by `gcp-standard.yaml`, `aliyun-standard.yaml`, and `microsoft-saas-standard.yaml` (Microsoft 365 / Power Platform / Dynamics 365), each with placement, zone model, identity, secrets, and data classification plus `E-GCP-*` / `E-ALI-*` / `E-MS-*` rules; `tests/test_platform_standards.py` enforces that contract and the renderer palette. Design templates `gcp-hub-spoke`, `aliyun-landing-zone`, `power-platform`, and `dynamics-365` join the catalog, and `tests/test_templates.py` renders every template in all three formats. Every platform in the standard library now has a tested template and a worked example: `examples/09-analytics-gcp-shared-vpc` (Google Cloud), `examples/10-power-platform-governed` (Microsoft SaaS), and `examples/11-aliyun-landing-zone` (Alibaba Cloud), alongside examples 01–06 for private cloud, AWS, and Azure. |

### P3 — Validation and policy automation

**Goal:** shift objective checks from prompt interpretation to deterministic,
machine-testable policy while preserving human architectural judgement.

| Initiative | Deliverable / acceptance criteria |
|---|---|
| Static checks on structured models | Started: `archharness arch-check` runs rules A-01..A-06 on an architecture YAML with rule ids and evidence, and the example governance test regenerates every shipped blueprint. Rule coverage still grows from real review findings. |
| Evidence-aware validation | `archharness validate-check` joins each finding's cited codes back to the requirements inventory and blueprint (the error rule runs over every example in CI), and `archharness backlog` groups the findings by the element they cite into an ordered `backlog/v1` remediation list, marking unanchored and unverifiable items. Field-level citations (`CMP-03.encryption_at_rest`) are verified against the entity definition, and the backlog carries the field as `anchor.field`. Remaining: carry per-item owner/effort and wire the backlog into `arch-optimize`. |
| Policy profiles | Started: `standards/arch-gate-policy.yaml` declares named profiles over the baseline, `archharness enforce --profile <name>` selects one, the decision records which profile applied, and a looser profile must declare `allow_looser` with a rationale. Remaining: policy-to-standard mappings and per-profile override evidence. |
| CI integration | Started: the shipped workflow runs the unit suite, distribution health, mirror drift, YAML validity, schema compatibility against the pull request base, and a clean-wheel smoke test. `docs/first-run.md` documents the local equivalents. `docs/ci-pipeline.md` is a worked pull-request workflow that runs the full deterministic chain, gates on `enforce` (failing closed on `BLOCK`), and archives the decision and rendered diagram; CI publishes the reference examples' gate evidence, and this repository's own recorded decisions are replayed in tests. |

### P4 — Ecosystem, usability, and adoption

**Goal:** reduce integration friction while keeping the core offline-capable and
deterministic.

| Initiative | Deliverable / acceptance criteria |
|---|---|
| CMDB/EA adapters | Done: `archharness/requirements/from_api.py` ships ServiceNow, generic REST, and CSV adapters behind the CLI's `--api` / `--csv`. Endpoints and credentials come from named environment variables (`SERVICENOW_URL` / `_USER` / `_PASSWORD`, `CMDB_URL` / `CMDB_TOKEN`, or a custom `--config`), never from source control, and each yields normalized `req/v2` partial entities: systems, de-duplicated infra, and — when a CSV carries a tech stack — components, stacks, and deployments. `tests/test_req_from_api.py` covers the field mappings, the auth headers, the fail-closed gaps, DC normalization, and a merge regression that the deployment's infra reference resolves to the normalized node name. |
| Guided onboarding | Started: `doctor` loads every governance input (gate policy and all its profiles, workflow spec, req/v2 schema, diagram style) and fails closed with the loader's message, so a broken installation is diagnosed before the first pipeline run. `init-project` scaffolds a startable registry, coded prompt, and quick-start README that pass the registry checker, without overwriting existing files. [docs/first-run.md](first-run.md) walks a new team from clone to a gated diagram and pairs each common failure with the command that diagnoses it. Done: the walkthrough ends with a short recipe per platform standard — private cloud, AWS, Azure, Google Cloud, Alibaba Cloud, and Microsoft SaaS — naming the template to copy, the region kind, the placement rules that trip people up, and a worked example. |
| Documentation | Maintain operator guides, decision records, example rebuild instructions, and concise upgrade notes alongside code changes. [docs/pamp-integration.md](pamp-integration.md) fixes the engine↔platform boundary with AXISRobo-PAMP as a versioned contract (which side owns users, workflow, storage, and which computes scores, gate decisions, provenance, and metrics), and records the PAMP-side credential remediation it implies. |
| Metrics and feedback | Done: `archharness metrics` aggregates a project's validation results, enforcement decisions, routing diagnostics, and workflow state into a `metrics/v1` roll-up — workflow completion, findings by severity / disposition / dimension / rule family, routing fallback ratio and waypoint buckets (readability defects), and median stage turnaround. It carries counts, fixed enums, and standard labels only; `tests/test_metrics.py` proves distinctive payload tokens never reach the JSON or the Markdown. The contract is the observability seam for an external governance platform ([docs/pamp-integration.md](pamp-integration.md) §3.4). |

## Research / deliberately deferred

- **LLM-generated draw.io XML:** not planned. Precise geometry must remain
  deterministic, testable, and version-control friendly.
- **LLM-assisted review:** useful as advisory content validation or diagram
  critique, but it must not replace deterministic enforcement or fabricate
  artifact evidence.
- **Advanced graph routing:** consider visibility-graph or A* routing only after
  the deterministic port/gutter/L-shape router and route regression suite prove
  insufficient on real examples.
- **More cloud patterns:** do not add a platform pattern merely to broaden the
  catalog; each must be backed by a reviewed standard and test fixtures.

## Roadmap operating rules

1. Keep workflow stage order fail-closed; no feature may fabricate predecessor
   artifacts or bypass the enforce decision.
2. Treat standards, schemas, and generated artifacts as versioned interfaces.
3. Prefer deterministic, locally testable transformations for structure, layout,
   hashing, and gate decisions; use LLMs for interpretation, critique, and prose.
4. Every new capability needs focused tests and at least one representative
   example or fixture before it is described as supported.
