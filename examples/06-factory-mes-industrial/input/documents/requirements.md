# Requirements Document — Factory MES (PlantMES)
**Version**: 2.0  |  **Project ID**: PMES-US-001  |  **Classification**: Acme Confidential
**Scope**: Plant-edge deployment + central integration (migration view; scrubbed)

> Resolve typed codes via `input/systems-registry.md` (req/v2 entity model).

---

## 1. Project Overview

CMP-03 through CMP-20 (system APP-01, PlantMES) is the manufacturing execution
system for a US plant (site INF-01). The full stack runs plant-local so
production continues during WAN outages; integration with central planning, ERP
and data platforms is asynchronous via Kafka hubs. This diagram is a migration
view: interfaces are marked EXISTING (black) or NEW (red).

## 2. Plant-Local Deployment (site INF-01, zone INF-02)

| Layer | Components |
|-------|-----------|
| Ingress | INF-13 → CMP-01 / CMP-02 (HTTPS; Nginx) |
| Web | CMP-03 |
| Gateway | CMP-04 |
| Services (Java/Spring ×13) | CMP-05 through CMP-18 |
| Persistence | CMP-19 / CMP-20, VM-based |

Users: plant intranet thick client (with label printing) and web browser, both
HTTPS to INF-13. User authentication is AUTH-01 (IdP INF-14).

## 3. Central Systems and Integration

| Location | Entity | Interface | Status |
|----------|--------|-----------|--------|
| INF-03 | INF-14 | HTTPS (external authorization IdP) | Existing |
| INF-03 | CMP-21 | HTTPS (external authorization) | Existing |
| INF-04 | CMP-22 | HTTPS | Existing |
| INF-04 | CMP-23 | TCP | Existing |
| INF-04 / INF-12 | CMP-24, CMP-25, CMP-26, CMP-27 | TCP via CMP-23 / CMP-22 | New |
| INF-05 / INF-08 | CMP-28 | TCP | New |
| INF-05 / INF-10 | CMP-29 | TCP/TLS 1.2 | New |
| INF-05 / INF-09 | CMP-26 / CMP-30, CMP-31 | TCP via Kafka | New |
| INF-05 / INF-11 | CMP-32 | IDOC | New |
| INF-05 / INF-11 | CMP-33, CMP-34 | RFC | New |
| INF-06 | CMP-35 | TCP/Kafka | New |
| INF-07 | CMP-36 | Kafka SASL_SSL | New |

Every boundary crossing passes a firewall. Plant↔central links are LNK-01
(site to US DC) and LNK-02 (site to NA DC, backup); central backbone is LNK-03;
cloud attach is LNK-04.

## 4. Constraints

- **Plant autonomy**: the plant stack must keep producing with the WAN down; no
  plant runtime dependency on central services (integration is async).
- Plant↔central integration via Kafka only; no direct DB or API calls
  (FLOW-07 / FLOW-08 are the only plant egress).
- SAP access only via IDOC (CMP-32) and RFC (CMP-33, CMP-34) from INF-11 —
  never from the plant directly.
- CMP-19 / CMP-20 stays plant-local (FLOW-05); no central DB dependency.
- TLS everywhere; credentials in K8s Secrets.

## 5. Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | Cut-over sequence for NEW interfaces | Yes (migration) |
| TBD-02 | Kafka topic naming convention per plant | No |
