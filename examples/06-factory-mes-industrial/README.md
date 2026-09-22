# Example 6 — Factory MES (PlantMES): Plant Edge + Central DC Integration

Reverse-engineered from a real factory MES architecture diagram.
Demonstrates the **industrial plant-edge pattern**: an autonomous MES stack
at the plant, integrated with central DC systems and SAP through Kafka hubs —
plus **migration markers** (existing vs new interfaces).

> **Name policy:** `input/systems-registry.md` is the only file that contains literal entity names. Every other file — `input/prompt.md`, `input/documents/requirements.md`, `README.md`, `config.yaml` — references typed codes only (`INF-` infra, `APP-` systems, `CMP-` components, `DEP`/`FLOW`/`LNK`/`AUTH` for the derived layers). The original reference diagram is intentionally not scrubbed and is restricted input.

## Scenario

**CMP-03 through CMP-20** (system `APP-01`, PlantMES) runs the shop floor of a
US plant (`INF-01`). It must keep running during WAN outages, so the full stack
is plant-local; integration with central planning/ERP is asynchronous via Kafka.

- **Plant site (`INF-01`, zone `INF-02`)**
  - `INF-13` → `CMP-01` / `CMP-02` (HTTPS ingress; Nginx)
  - K8s cluster: `CMP-03`, `CMP-04`, and 13 Java/Spring services `CMP-05`–`CMP-18`
  - `CMP-19` / `CMP-20`, VM-based
- **Users**: plant intranet — thick client (printing) and web browser, both HTTPS
  (`AUTH-01` via the IdP `INF-14`)
- **Identity**: external authorization via `CMP-21` + `INF-14` in `INF-03`
- **Integration (migration view — red = new, black = existing)**
  - `INF-04`: `CMP-22` + `CMP-23`; peer systems `CMP-24`–`CMP-27` (TCP)
  - `INF-05` (multi-zone): `CMP-28` in `INF-08`; `CMP-29` (TCP/TLS 1.2) in
    `INF-10`; `CMP-26` / `CMP-30` in `INF-09`; `CMP-32` via **IDOC**,
    `CMP-33` / `CMP-34` via **RFC** in `INF-11`; `CMP-31` in `INF-09`
  - `INF-06`: `CMP-35` (TCP/Kafka)
  - `INF-07`: `CMP-36` (Kafka SASL_SSL)
- Every boundary crossing passes a firewall

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| private-cloud-standard | plant-edge zone model, DB HA inside the plant |
| interaction-rules | Kafka-only plant↔central mediation; SAP IDOC vs RFC |
| accuracy-rules | multi-zone NA-DC placement; edge autonomy |
| arch-validate | migration markers (new/existing interfaces) in diagrams |
| req/v2 model | one component (`CMP-26`) with two site deployments; appliances (`INF-13`, `INF-14`) kept out of components |

## Inputs

- `input/systems-registry.md` — seven typed tables (infra / systems / components / deployments / flows / network links / auth)
- `input/prompt.md` — human-maintained readable one-shot prompt (Path A)
- `input/documents/requirements.md` — structured requirements (Path B)
- `input/diagrams/reference-architecture.png` — original, intentionally not scrubbed, restricted input

## Scrub notes

| Original | Scrubbed |
|---|---|
| Plant site code (USxx01-city) | `plant-us-01` |
| Reference diagram names | kept originals; the image is intentionally not scrubbed and is restricted input |
| Prompt names | manually scrubbed in `input/prompt.md`, then synchronized to registry `文档用名` |
| K8s platform | see `config.yaml` platforms.* |
| DC names | config ids |
| IP addresses | none present / removed |

## Diagram artwork

| Artifact | What it is |
|---|---|
| `output/diagrams/diagram-v11.drawio` / `.png` | Artwork the recorded validation and enforcement decision were produced from. The PNG is a draw.io CLI export, so it needs draw.io desktop to reproduce. |
| `output/diagrams/diagram-v12.drawio` / `.d2` | Regenerated with the current generator, including deterministic edge routing. |
| `output/diagrams/diagram-v12.png` | **Preview only** — rendered by the D2 engine (ELK layout), not a draw.io export. It is not the reviewed artwork. |

Promoting v12 means re-running validate → enforce against a draw.io export of
`diagram-v12.drawio`, then re-recording `diagram.png` in the workflow state.
