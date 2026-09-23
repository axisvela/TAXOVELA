# Example 2 — Data Agent Platform: Private DC + Azure Hybrid

Reverse-engineered from a real data-agent architecture diagram.
Demonstrates a **hybrid AI-agent deployment**: the agent runtime stays in the
private DC (data sovereignty), while Azure provides the data source
and the model service.

> **Name policy:** `input/systems-registry.md` is the only file that contains literal entity names. Every other file — `input/prompt.md`, `input/documents/requirements.md`, `README.md`, `config.yaml` — references typed codes only (`INF-` infra · `APP-` systems · `CMP-` components · the `DEP`/`FLOW`/`LNK`/`AUTH` derived layers). The original reference diagram is intentionally not scrubbed and is restricted input.

## Diagram artwork

| Artifact | What it is |
|---|---|
| `output/diagrams/diagram.drawio` / `.png` | Artwork the recorded validation and enforcement decision were produced from, on the retired `SYS-nn` id space. |
| `output/diagrams/diagram-v2.drawio` / `.d2` / `.png` | Rendered from the migrated blueprint, where every node carries its registry code. |
| `output/diagrams/diagram-v2-d2.png` | **D2/ELK preview** rendered from `diagram-v2.d2`; its automatic layout differs from the draw.io artwork, so it is not the validation target. |

The blueprint was migrated after the recorded validation: nodes now use the
registry's typed codes and the internal K8s platform is no longer a node — the
registry models it as the runtime of the components it hosts. The topology is
unchanged, so the recorded findings still apply, but promoting v2 means
re-running validate → enforce against it and re-recording `diagram.png`.

## Scenario

The platform serves internal admins asking data questions from the office network; the agent answers against governed namespaces and calls models through a controlled service.

- **Private DC (`dc-cn-primary`, three-tier)**
  - App Zone, Internal K8s cluster: CMP-01 (nginx: static hosting + API proxy)
    + dashboard UI; CMP-02 (Node.js: agent API, SSE streaming, agent
    tools); CMP-03 (Node.js: alerts, digests)
  - App Zone, VM (Rocky 9.8): CMP-05 — the *only*
    path from the DC to Azure
  - DB Zone: CMP-04 (VIP TBD), reached via TCP 5432 only from App Zone
  - Identity: INF-05 (internal STS endpoint)
- **Azure (shared-prod subscription)**
  - INF-07 — user authentication
  - azure-eastus: CMP-06
    exposing governed namespaces (HTTPS 443)
  - azure-eastus2 (TBD): CMP-07 with two pools
    (overseas / China), reachable via private endpoint subnet
- **Flows**: browser → HTTPS 443 → CMP-01 → CMP-02 / CMP-03 →
  CMP-04 (TCP 5432); CMP-02 → CMP-05 → CMP-06 (HTTPS 443)
  and CMP-07 (HTTPS 443); auth via INF-07 + INF-05

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| accuracy-rules | three-tier zone placement, DB reachable only from App Zone |
| security-rules | single controlled outbound path, private endpoint for model service, dual IdP |
| interaction-rules | all cloud calls mediated by CMP-05 (listed in `integration_platforms`) |
| arch-design | hybrid AI pattern: private runtime + public model/data via egress proxy |

## Inputs

- ★ `input/systems-registry.md` — code-to-name map (load first)
- `input/prompt.md` — human-maintained readable one-shot prompt (Path A) and manual scrubbing source
- `input/documents/requirements.md` — structured requirements (Path B)
- `input/diagrams/reference-architecture.png` — restricted original reference diagram, intentionally NOT scrubbed
  *(place the provided original image here; names map via the registry)*

## Name policy

| Reference | Handling |
|---|---|
| Human source | Manually scrub names in `input/prompt.md`, then update the registry's `文档用名` column |
| Company domains, subscription IDs, VIPs | Replaced with generic placeholders / TBD, no IPs |
| Reference diagram | Restricted input; intentionally NOT scrubbed and keeps original names for traceability |
