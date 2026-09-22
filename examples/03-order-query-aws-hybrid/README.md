# Example 3 — Order Query Platform (OVP ROW): AWS + Multi-DC Hybrid

Reverse-engineered from a real order-query architecture diagram. Textual
names are scrubbed through the registry; the restricted image is unchanged.
Demonstrates an **AWS-hosted query platform** federating order data from
four private DCs and two Azure EDW sources — with every integration
mediated by the SYS-29/SYS-30/SYS-31 gateways or the Kafka clusters.

> **Name policy:** `input/systems-registry.md` is the only file that contains literal entity names. Every other file — `input/prompt.md`, `input/documents/requirements.md`, `README.md`, `config.yaml` — references `SYS-nn` codes only. The original reference diagram is intentionally not scrubbed and is restricted input.

## Scenario

**OVP ROW** gives internal and external users a single order-query view.
The query platform runs on AWS US; the data lives in source systems spread
across US/CN data centers and Azure EDWs.

- **AWS US VPC** (three-tier subnets):
  - Public subnet (DMZ): Front-End K8s cluster — SYS-05
  - Private subnet (App Zone): Backend K8s cluster — SYS-06 + services
    SYS-07–SYS-23 (portal, report, notification, transform, task, web UI,
    nine Kafka consumers SYS-13–SYS-21, consumer task, job scheduler);
    plus SYS-24
  - Private subnet (DB Zone): SYS-25 + SYS-26, SYS-27, SYS-28
- **Identity** (`dc-us`): SYS-01 (internal users) + SYS-02 (external
  users), both SAML; SYS-03 + SYS-04 in the DMZ
- **Integration hubs**: SYS-29 (external), SYS-30 (internal), SYS-31
  (NA-DC integration zone); Kafka clusters SYS-32–SYS-36
- **Sources**: SYS-54 (SaaS), SYS-55 + SYS-56 (Azure US), SYS-57 (Azure CN
  North), SYS-48 + SYS-49 (CN primary), SYS-42–SYS-47 (CN secondary),
  SYS-50–SYS-53 (NA-DC) — see `input/systems-registry.md` and
  `input/api/cmdb-export.csv`
- **WAN**: MPLS between every DC and the AWS VPC; TLS firewalls on each
  boundary

## What it demonstrates

| Pipeline stage | Highlight |
|---|---|
| interaction-rules | 100% mediated integration (SYS-29/SYS-30/SYS-31 or Kafka only — no direct calls) |
| arch-req-from-api | `input/api/cmdb-export.csv` → high-confidence location/ownership |
| security-rules | dual-IdP SAML, cross-border annotation (SYS-57 stays in-country) |
| accuracy-rules | multi-zone NA-DC: Kafka/SYS-31 only in INTEGRATION zone |

## Inputs

- `input/systems-registry.md` — ★ system registry (read this first)
- `input/prompt.md` — human-maintained one-shot prompt with readable names
- `input/documents/requirements.md` — structured requirements (Path B)
- `input/api/cmdb-export.csv` — CMDB export (Path C: `arch-req-from-api`)
- `input/diagrams/reference-architecture.png` — *(place the provided image here;
  keep original system names — do NOT scrub the image)*

## Scrub notes

| Original | Scrubbed |
|---|---|
| External IdP brand | see registry SYS-02 |
| K8s platform codename | see registry SYS-58 |
| Internal EDW / data-lake / codename systems | see registry SYS-32–SYS-36, SYS-45, SYS-53, SYS-55–SYS-57 |
| CMDB record IDs | masked as `A-XXXX-nn` (keeps the ID shape for the CMDB-reader demo) |
| IP addresses | removed from all documents |
