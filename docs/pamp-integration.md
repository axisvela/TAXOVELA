# Integrating ArchHarness with AXISRobo-PAMP

[AXISRobo-PAMP](https://github.com/axisrobo/AXISRobo-PAMP) is an enterprise
architecture management and governance platform (FastAPI + PostgreSQL, RBAC,
review workflow, AVDM decision chain). ArchHarness is the offline, deterministic
architecture engine. They are complements, and this page fixes the boundary
between them so integration stays honest: **platform owns workflow, identity,
storage, and UI; engine owns deterministic computation and artifact evidence.**

This is a contract document. It adds no live network code to ArchHarness and
keeps the core runnable with no PAMP instance available.

## 1. Who owns what

| Concern | AXISRobo-PAMP | ArchHarness |
|---|---|---|
| Users, RBAC, multi-tenancy | ✔ owns | ✖ never |
| Review workflow, meetings, actions | ✔ owns | ✖ |
| System of record (PostgreSQL, UI) | ✔ owns | ✖ |
| Requirements intake | ✔ requests | ✔ normalizes to `req/v2` |
| Design (blueprint) | — | ✔ owns |
| Diagram rendering | — | ✔ owns (draw.io / D2 / PNG / PlantUML) |
| Standards scoring | — | ✔ owns |
| Deterministic gate decision | ✔ records | ✔ computes (`enforce`, exit code) |
| Artifact provenance | ✔ stores | ✔ computes (`artifact/v1`, SHA-256) |
| Governance metrics | ✔ renders | ✔ computes (`metrics/v1`) |
| Data governance, AVDM, PACT | ✔ owns | viewpoint names only |

The rule of thumb: if it must be reproducible and hash-verifiable, it is
computed by ArchHarness and *stored* by PAMP. If it involves people, permissions,
or persistence, it is owned by PAMP.

## 2. Contract artifacts

Only versioned ArchHarness contracts cross the boundary. No PAMP code imports
ArchHarness internals, and no ArchHarness code calls PAMP at import time.

| Contract | Producer | Consumer | Carries |
|---|---|---|---|
| `req/v2` | ArchHarness readers/merger | PAMP (application/portfolio) | requirements entities |
| `artifact/v1` | `make_manifest` | PAMP (traceability) | path, SHA-256, producer, lineage |
| `validation/v1` | `arch-validate` | PAMP review record | six-dimension scores + typed findings |
| `enforcement/v1` | `archharness enforce` | PAMP gate record | PASS/WARN/BLOCK, policy digest, reasons |
| `metrics/v1` | `archharness metrics` | PAMP dashboards (v2.4) | aggregate counts only |

Each contract already validates on its own (`archharness … --json` emits it), so
the integration is a data exchange, not a code dependency.

## 3. Surface map (evidence-based)

The mapping below is grounded in PAMP's own code and `integration/` docs.

### 3.1 CMDB application sync → requirements intake

PAMP documents a CMDB CI query (`integration/cmdb-applicaiton-api.md`):
`POST <endpoint>/api/v2/ci-query/search/1` with `conditions` / `showColumns`,
returning rows under `data.pageResult.rows`. Its fields line up with
`archharness/requirements/from_api.py`: `patch_level` → application id,
`name` / `app_full_name` → name, `owned_by` → owner, `appowner_orgname` →
department. A `cmdb-ci-query` profile in `from_api.py` is the read seam; it is
not built yet (see §6).

### 3.2 AI architecture review ↔ deterministic validation

PAMP's `integration/ai-architecture-review-api.md` returns a `score_breakdown`
whose six keys are the same standard dimensions ArchHarness scores:

| PAMP `score_breakdown` key | ArchHarness dimension | Weight |
|---|---|---|
| `cloud_network_completeness` | `Cloud_Network_Completeness` | 2.0 |
| `connectivity` | `Connectivity` | 1.0 |
| `technical_component_completeness` | `Technical_Component_Completeness` | 2.0 |
| `interaction_integration` | `Interaction_Integration` | 2.0 |
| `security_compliance` | `Security_Compliance` | 2.0 |
| `terminology_expression` | `Terminology_Expression` | 1.0 |

PAMP `issues[]` map to `validation/v1` `issues[]` as: `id` → `rule_id`,
`dimension` → `dimension`, `issue_type` (`must_fix`) → `disposition`,
`priority` (`High`) → `severity` (lowercased), `related_entities` → `subject`,
`description` → `evidence`. PAMP's `suggestion` has no `validation/v1` home; it
belongs in the `backlog/v1` remediation list. A converter either way is the core
engine↔platform seam and is not built yet (see §6).

### 3.3 Policy engine and decision traceability

PAMP's roadmap v2.0 wants a version-controlled architecture policy engine and
full decision traceability. ArchHarness already ships the deterministic half:
`standards/arch-gate-policy.yaml` with named profiles and a policy digest,
`archharness enforce` with a process exit code, and `artifact/v1` manifests with
SHA-256 lineage plus `workflow verify`. PAMP supplies the storage, approval, and
"who decided what" narrative around those digests.

### 3.4 Governance observability → `metrics/v1`

PAMP's roadmap v2.4 wants governance metrics (compliance rates, review cycle
times). ArchHarness now computes them without shipping architecture content.

```bash
archharness metrics --project orders --json \
    -o projects/orders/output/reports/metrics.json
```

The roll-up measures exactly the four roadmap concerns:

| Concern | `metrics/v1` field |
|---|---|
| Workflow completion | `workflow.stages_completed` / `stages_total` / `completion_ratio` / `stages_ready` |
| Validation finding categories | `validation.by_severity` / `by_disposition` / `by_dimension` / `by_rule_family` |
| Routing / readability defects | `routing.fallback_ratio` / `waypoint_buckets` / `readability_defects` |
| Review turnaround | `turnaround.transitions[*].median_seconds` |

### 3.5 Viewpoints and AVDM

PAMP's AVDM chain (`Questionnaire → Concern → Viewpoint → Artifact`) and
ArchHarness's viewpoint selection (`archharness view`) describe the same layer.
Aligning the PACT viewpoint ids with the ArchHarness viewpoint ids is a naming
exercise, deliberately deferred until both taxonomies are frozen.

## 4. Recommended integration patterns

1. **Engine-in-platform (default).** PAMP calls the ArchHarness CLI as a
   subprocess (`archharness arch-check …`, `… enforce …`, `… metrics --json`)
   or imports the library, then stores the emitted `enforcement/v1` /
   `metrics/v1` document. ArchHarness stays offline and deterministic; PAMP owns
   auth, storage, and the review UI.
2. **Evidence exchange.** PAMP stores `artifact/v1` manifests and replays
   `archharness workflow verify` to detect drift; ArchHarness never needs a
   database.
3. **Requirements intake.** ArchHarness pulls application metadata from the
   CMDB/EA API and emits `req/v2`; PAMP keeps the portfolio view.

In all three, the direction of data is explicit and the contracts are versioned
by identity, so a breaking change ships under a new id (see `schema-check`).

## 5. Privacy and security

- **`metrics/v1` excludes payloads by contract.** It carries counts, fixed
  enums, and standard rule/dimension labels — never entity names, ids, subjects,
  evidence, notes, or artifact paths. `tests/test_metrics.py` asserts that
  distinctive payload tokens do not appear in the JSON or Markdown output.
- **Credentials stay in the environment.** ArchHarness adapters read endpoints
  and secrets only from named environment variables; no credential is ever
  written into a blueprint, a manifest, or a roll-up.
- **Action required in PAMP.** `integration/ai-architecture-review-api.md`
  currently embeds a live-looking `X-API-KEY` and a username in source control
  (the token appears in the header examples and the cURL blocks). Treat it as
  compromised: **rotate the key**, purge it from git history, and move it to
  environment configuration, matching the rule ArchHarness enforces for its own
  adapters. This document intentionally does not reproduce the value.

## 6. Deliberately not built yet

| Item | Why deferred |
|---|---|
| `cmdb-ci-query` profile in `from_api.py` | needs the POST body shape and a fake-HTTP test fixture; scoped as the next read-side slice |
| PAMP review ⇄ `validation/v1` converter | needs agreement on `severity` precedence and where `suggestion` lands (`backlog/v1`) |
| PAMP-side plugin calling ArchHarness | lives in the PAMP repository, not here |
| Viewpoint id alignment | both taxonomies are still moving |

Each of these is additive and can ship behind the existing contracts without
changing them.
