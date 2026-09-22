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
| `req/v2` adoption | Migrate or rebuild suitable examples from `req/v1`; each migration has a registry check, requirements validation, and explicit unresolved/TBD items. |
| Traceability | Preserve source references from intake through requirement, blueprint component/interaction, diagram, validation finding, and remediation backlog. |
| Schema evolution | Version schemas and define migration/compatibility rules before adding required fields; reject ambiguous or unsafe defaults. |
| Platform patterns | Expand reusable, tested patterns only where standards can specify physical placement, network zones, protocol, identity, secret handling, and data classification. |

### P3 — Validation and policy automation

**Goal:** shift objective checks from prompt interpretation to deterministic,
machine-testable policy while preserving human architectural judgement.

| Initiative | Deliverable / acceptance criteria |
|---|---|
| Static checks on structured models | Implement high-confidence rules against requirements/architecture YAML before image-based review; retain rule IDs and evidence in reports. |
| Evidence-aware validation | Connect validation findings to relevant model fields and rendered diagram elements, including an explicit confidence and false-positive handling path. |
| Policy profiles | Support versioned policy profiles, documented overrides, and policy-to-standard mappings for different enterprise contexts. |
| CI integration | Provide documented CI examples that archive artifacts, run validate → enforce deterministically, and fail closed on `BLOCK`. |

### P4 — Ecosystem, usability, and adoption

**Goal:** reduce integration friction while keeping the core offline-capable and
deterministic.

| Initiative | Deliverable / acceptance criteria |
|---|---|
| CMDB/EA adapters | Add well-scoped ServiceNow, generic REST, and CSV adapters with authenticated configuration outside source control and normalized partial-requirement output. |
| Guided onboarding | Improve `init-project`, `doctor`, templates, and error messages so a new team can produce its first governed diagram without knowing repository internals. |
| Documentation | Maintain operator guides, decision records, example rebuild instructions, and concise upgrade notes alongside code changes. |
| Metrics and feedback | Measure workflow completion, validation finding categories, routing/readability defects, and review turnaround without collecting sensitive architecture payloads. |

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
