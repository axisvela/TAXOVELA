# Example 5 — Supply-Chain Order Platform (OSP): Private Cloud Active-Active

Reverse-engineered from a real supply-chain order architecture diagram.
Demonstrates **symmetric active-active deployment** across CN
and NA private DCs, deep **SAP (ERP) integration**, and CDC-based data
synchronization — plus the full multi-zone model on the NA side.

> **Name policy:** `input/systems-registry.md` is the only file that contains literal entity names. Every other file — `input/prompt.md`, `input/documents/requirements.md`, `README.md`, `config.yaml` — references typed codes only (`INF-` infra, `APP-` systems, `CMP-` components, `DEP`/`FLOW`/`LNK`/`AUTH` for the derived layers). The original reference diagram is intentionally not scrubbed and is restricted input.

## Scenario

**APP-01 (OSP)** is the order service platform for supply chain. Its eight
logical backends (`CMP-03` through `CMP-10`) are deployed identically in CN and
NA — **one component, two deployment units** — each integrated with the local
SAP landscape (`CMP-33`/`CMP-34` in APP-05, `CMP-35` in APP-06).

- **CN DC (`INF-01`, three-tier)**
  - Employee access: `INF-13` → `INF-16` (ingress) → `INF-17` (security,
    optional) → `INF-18` (edge routing) → `CMP-01` (web, Nginx, internal access
    authentication)
  - `INF-02`: `CMP-02` (gateway, K8s) → `CMP-03`–`CMP-10` (backend ×8,
    Java/Spring, K8s); `CMP-11`–`CMP-14` (integration + messaging)
  - Peer apps `CMP-25`–`CMP-29` in APP-02
  - SAP `CMP-33`/`CMP-34` (Function + SLT) via TCP/RFC/HTTPS
  - Middleware `CMP-15`, `CMP-16` (CDC)
  - DB zone `INF-03`: `CMP-17`–`CMP-21` (persistence HA groups)
  - Identity AUTH-01 via `INF-22` (HTTPS/SAML)
- **NA DC (`INF-04`, multi-zone)** — same workloads split across zones:
  - `INF-05`: `CMP-01`–`CMP-10`, plus `CMP-22`–`CMP-24` (NA backends)
  - `INF-06`: `CMP-13`/`CMP-14` (the only mediation zone)
  - `INF-08`: `CMP-35` (NA ERP, Function + SLT)
  - `INF-07`: `CMP-15`/`CMP-16` (middleware, CDC)
  - `INF-09`: `CMP-17`–`CMP-21` (persistence HA groups)
- **Adjacent clouds**: `INF-11` AWS US (`CMP-30`, messaging SASL/SCRAM),
  `INF-12` Azure US (`CMP-31`/`CMP-32`; HTTPS / messaging)

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| accuracy-rules | multi-zone placement: integration components only in `INF-06`; SAP isolated in `INF-08` (`CMP-35`) |
| interaction-rules | `CMP-13`/`CMP-14` (NA) and `CMP-11`–`CMP-14` (CN) as legal mediators; SAP RFC boundary (`CMP-33`/`CMP-34`, `CMP-35`) |
| security-rules | SAML→`INF-22`, internal access authentication at web tier (`CMP-01`), optional `INF-17`/`INF-20` |
| arch-design | active-active symmetric topology, CDC sync pattern (`CMP-16`) |
| req/v2 model | CN+NA modelled as **one component with two deployments**; F5/WAF/router are `INF` L4 nodes, not components |

## Inputs

- `input/systems-registry.md` — seven typed tables (infra / systems / components / deployments / flows / network links / auth)
- `input/prompt.md` — typed-code one-shot prompt (Path A)
- `input/documents/requirements.md` — structured requirements (Path B)
- `input/diagrams/reference-architecture.png` — original, intentionally not scrubbed; restricted input

## Name policy

| Artifact | Policy |
|---|---|
| `input/systems-registry.md` | The only file with literal names: typed code-to-name mapping and source of `文档用名` values. |
| `input/prompt.md` | Typed-code one-shot prompt. Resolve every code through the registry. |
| `input/documents/requirements.md` | Typed-code structured requirements. |
| `input/diagrams/reference-architecture.png` | Original reference image; intentionally not scrubbed and restricted input. |
| IP addresses | None present in the maintained documents. |

## Diagram artwork

| Artifact | What it is |
|---|---|
| `output/diagrams/diagram.drawio` / `.png` | Artwork the recorded validation and enforcement decision were produced from, on the earlier `SYS-nn` id space. |
| `output/diagrams/diagram-v2.drawio` / `.d2` / `.png` | Rendered from the migrated blueprint, where every node carries its typed code. The D2 file is the text, ELK-layout-friendly companion for review and diffing. |

The blueprint was migrated to the req/v2 id space after the recorded
validation: components folded onto a single `CMP-nn` row across both sites
carry a site suffix (`CMP-03-CN`, `CMP-03-NA`), while single-site components
keep the bare code. The topology is unchanged, so the recorded findings still
apply, but promoting v2 means re-running validate → enforce against it and
re-recording `diagram.png` in the workflow state.
