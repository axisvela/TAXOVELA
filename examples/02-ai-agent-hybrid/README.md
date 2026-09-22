# Example 2 — Data Agent Platform: Private DC + Azure Hybrid

Reverse-engineered from a real data-agent architecture diagram.
Demonstrates a **hybrid AI-agent deployment**: the agent runtime stays in the
private DC (data sovereignty), while Azure provides the data source
and the model service.

> **Name policy:** `input/systems-registry.md` is the only file that contains literal entity names. Every other file — `input/prompt.md`, `input/documents/requirements.md`, `README.md`, `config.yaml` — references `SYS-nn` codes only. The original reference diagram is intentionally not scrubbed and is restricted input.

## Scenario

The platform serves internal admins asking data questions from the office network; the agent answers against governed namespaces and calls models through a controlled service.

- **Private DC (`dc-cn-primary`, three-tier)**
  - App Zone, SYS-10 cluster: SYS-01 (nginx: static hosting + API proxy)
    + dashboard UI; SYS-02 (Node.js: agent API, SSE streaming, agent
    tools); SYS-03 (Node.js: alerts, digests)
  - App Zone, VM (Rocky 9.8): SYS-05 — the *only*
    path from the DC to Azure
  - DB Zone: SYS-04 (VIP TBD), reached via TCP 5432 only from App Zone
  - Identity: SYS-06 (internal STS endpoint)
- **Azure (shared-prod subscription)**
  - SYS-07 — user authentication
  - azure-eastus: SYS-08
    exposing governed namespaces (HTTPS 443)
  - azure-eastus2 (TBD): SYS-09 with two pools
    (overseas / China), reachable via private endpoint subnet
- **Flows**: browser → HTTPS 443 → SYS-01 → SYS-02 / SYS-03 →
  SYS-04 (TCP 5432); SYS-02 → SYS-05 → SYS-08 (HTTPS 443)
  and SYS-09 (HTTPS 443); auth via SYS-07 + SYS-06

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| accuracy-rules | three-tier zone placement, DB reachable only from App Zone |
| security-rules | single controlled outbound path, private endpoint for model service, dual IdP |
| interaction-rules | all cloud calls mediated by SYS-05 (listed in `integration_platforms`) |
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
