# Requirements Document — Factory MES (PlantMES)
**Version**: 2.0  |  **Project ID**: PMES-US-001  |  **Classification**: Acme Confidential
**Scope**: Plant-edge deployment + central integration (migration view)
**Model**: `req/v2` — entity-separated (see `standards/requirements-model-v2.yaml`)

> Resolve typed codes via `input/systems-registry.md`.

---

## 1. Project Overview

APP-01 (PlantMES) is the manufacturing execution system for a US plant (site
INF-01). The full stack runs plant-local so production continues during WAN
outages; integration with central planning, ERP and data platforms is
asynchronous via Kafka hubs. This is a migration view: interfaces are marked
`[NEW]` or `[EXISTING]`.

Infra: INF-01–INF-20. Systems: APP-01–APP-07. Components: CMP-01–CMP-36.

## 2. Infrastructure Topology

| ID | Name | node_kind | infra_type | network_type | Parent | Country |
|----|------|-----------|------------|--------------|--------|---------|
| INF-01 | plant-us-01 | `data_center` | `private_cloud` | `prod_network` | — | US |
| INF-02 | plant APP Zone | `network_zone` | `private_cloud` | `prod_network` | INF-01 | US |
| INF-03 | dc-us | `data_center` | `private_cloud` | `prod_network` | — | US |
| INF-04 | dc-cn-primary | `data_center` | `private_cloud` | `prod_network` | — | CN |
| INF-05 | dc-us-na | `data_center` | `private_cloud` | `prod_network` | — | US |
| INF-06 | dc-cn-secondary | `data_center` | `private_cloud` | `prod_network` | — | CN |
| INF-07 | azure-eastus | `iaas_vpc_vnet` | `public_cloud` | `prod_network` | — | US |
| INF-08 | NA INTERGATION zone | `network_zone` | `private_cloud` | `prod_network` | INF-05 | US |
| INF-09 | NA K8S zone | `network_zone` | `private_cloud` | `prod_network` | INF-05 | US |
| INF-10 | NA LAKEHOUSE zone | `network_zone` | `private_cloud` | `prod_network` | INF-05 | US |
| INF-11 | NA SAP zone | `network_zone` | `private_cloud` | `prod_network` | INF-05 | US |
| INF-12 | CN App Zone | `network_zone` | `private_cloud` | `prod_network` | INF-04 | CN |
| INF-13 | VIP | `load_balancer` | `private_cloud` | `prod_network` | INF-02 | US |
| INF-14 | ADFS | `identity_provider` | `private_cloud` | `prod_network` | INF-03 | US |
| INF-15–INF-20 | Boundary firewalls | `firewall` | `private_cloud` | `prod_network` | zones above | US/CN |

`INF-20` (Azure EDW firewall) is in a public-cloud region, so it stays an
explicit node; the private-cloud firewalls are **zone boundaries** — all in/out
traffic of their zone passes them, so no component is connected to them
individually (rule R-INF-4).

## 3. Systems in Scope

| ID | System | Type | Owner | Scope |
|----|--------|------|-------|-------|
| APP-01 | PlantMES | New | org_it | Full internal stack |
| APP-02 | LMS ROW | Existing | org_it | Boundary only |
| APP-03 | CN Central Platform | Existing | org_it | Boundary only |
| APP-04 | NA Integration Platform | Existing | org_it | Boundary only |
| APP-05 | SAP NA | Existing | third_party (SAP) | Black box — IDOC/RFC boundary |
| APP-06 | Manufacturing Control Tower | New | org_it | Message bridge |
| APP-07 | EDW ROW | Existing | org_it | Event consumer |

## 4. Components & Services

Plant stack (APP-01): `CMP-01`/`CMP-02` Nginx pair (`load_balancer`),
`CMP-03` web (`web_frontend`), `CMP-04` gateway (`api_gateway`),
`CMP-05`–`CMP-18` 13 Java/Spring services (`backend_service`),
`CMP-19`/`CMP-20` PostgreSQL HA master/mirror (`database`, AES-256 at rest).

Central: `CMP-21` LMS ROW boundary, `CMP-22` APIM, `CMP-23` Kafka CN hub,
`CMP-24`–`CMP-27` MCS/APS/ERPS/PDS, `CMP-28` Kafka NA, `CMP-29` Lakehouse,
`CMP-30` LGS-NA, `CMP-31` IBS, `CMP-32`–`CMP-34` S4-NA/POCS/Service-CRM,
`CMP-35` MCT, `CMP-36` EDW ROW.

`CMP-23` and `CMP-28` are message buses: they are **service providers**, so
every interface points into them.

## 5. Deployments

One deployment unit per component per site (18 rows in the registry). The 13
plant services share the K8s profile (`INF-02`, `container`); the databases run
on VMs at `INF-01` (plant-local only). `CMP-26` (ERPS) has two deployments —
`INF-12` (CN) and `INF-09` (NA) — because the same component is active in both
DCs.

## 6. Component Communication Flows

12 flows (registry R5). Plant-local: ingress `internet → CMP-01 → CMP-03 →
CMP-04 → CMP-05..CMP-18 → CMP-19`, plus `CMP-19 → CMP-20` HA replication.
Central: `CMP-28` → `CMP-29/30/31`, `CMP-28` → `CMP-32/33/34`, `CMP-28 →
CMP-26`, `CMP-35 → CMP-28`, `CMP-28 → CMP-36`. Plant→central egress is
`CMP-16` (durable outbox) — the only plant egress.

Protocols and authentication are coded (`P-*` / `AU-*`); see
`standards/diagram-codes.yaml`.

## 7. Infra Network Links

| ID | Source | Target | Method | Redundancy |
|----|--------|--------|--------|------------|
| LNK-01 | INF-01 | INF-03 | `mpls` | primary |
| LNK-02 | INF-01 | INF-05 | `vpn` | backup |
| LNK-03 | INF-04 | INF-05 | `mpls` | primary |
| LNK-04 | INF-05 | INF-07 | `vpn` | primary |

## 8. User / Entry Authentication

| ID | Subject | Entry | auth_server | Protocol | Authorization | MFA |
|----|---------|-------|-------------|----------|---------------|-----|
| AUTH-01 | user | CMP-03 | INF-14 | SAML2 | RBAC | yes |
| AUTH-02 | application | CMP-04 | INF-14 | SAML2 | RBAC | yes |

## 9. Credential & Key Protection

| Environment | Solution | Notes |
|-------------|----------|-------|
| private_dc | Kubernetes Secrets (encrypted at rest) | DB passwords, Kafka SASL credentials |
| private_dc | SAP logon ticket | IDOC/RFC access from INF-11 only |

## 10. Open Items

| ID | Item | Owner | Blocking |
|----|------|-------|----------|
| TBD-01 | Cut-over sequence for NEW interfaces | Manufacturing IT | Yes (migration) |
| TBD-02 | Kafka topic naming convention per plant | Integration Team | No |

## 11. Architecture Constraints

- Plant autonomy: the plant stack keeps producing with the WAN down; integration is async.
- Plant-to-central integration via Kafka only; no direct DB or API calls.
- SAP access only via IDOC (`CMP-32`) and RFC (`CMP-33`, `CMP-34`) from `INF-11`.
- `CMP-19`/`CMP-20` stay plant-local; no central DB dependency.
- TLS everywhere; credentials in K8s Secrets.
