# Requirements Document — Supply-Chain Order Platform (OSP)
**Version**: 2.0  |  **Project ID**: OSP-001  |  **Classification**: Acme Confidential
**Scope**: Existing platform, active-active CN+NA (reverse-engineered, scrubbed)

> Resolve typed codes via `input/systems-registry.md` (req/v2 entity model).
> CN = INF-01 (three-tier); NA = INF-04 (multi-zone).

---

## 1. Project Overview

APP-01 (OSP) is the supply-chain order platform. It runs active-active in the CN
primary DC (INF-01, three-tier) and the NA DC (INF-04, multi-zone), each
integrated with the local SAP landscape and synchronized via CDC.

The eight logical backends are `CMP-03` through `CMP-10`: **one component with
two deployment units** — CN (INF-02) and NA (INF-05) — not two separate systems.
CN ingress is INF-16 / INF-17 / INF-18; NA ingress is INF-19 / INF-20 / INF-21.

## 2. Components in Scope (per region)

| Component | Role | System | Scope |
|-----------|------|--------|-------|
| CMP-01 | Web tier (Nginx) | APP-01 | Full internal stack; CN + NA |
| CMP-02 | Gateway (K8s) | APP-01 | Full internal stack; CN + NA |
| CMP-03 through CMP-10 | Backend ×8 (Java/Spring) | APP-01 | Full internal stack; CN + NA |
| CMP-15, CMP-16 | Middleware + CDC | APP-01 | Full; CN + NA |
| CMP-17 through CMP-21 | Persistence HA groups | APP-01 | Full; CN + NA |
| CMP-33, CMP-34 | ERP (Function + SLT) | APP-05 | Black box — boundary only |
| CMP-35 | ERP (Function + SLT) | APP-06 | Black box — boundary only |
| CMP-11 through CMP-14 | Integration + messaging | APP-01 | Boundary only |
| INF-22 | Identity (IdP) | — | Black box; infra L4 node |

## 3. Physical Deployment

| Layer | CN (INF-01) | NA (INF-04, multi-zone) |
|-------|-------------|--------------------------|
| Web (Nginx) | CMP-01 in INF-02 | CMP-01 in INF-05 |
| Backend K8s (Java/Spring) | CMP-02 through CMP-10 in INF-02 | CMP-02 through CMP-10 in INF-05 |
| Integration + messaging | CMP-11 through CMP-14 in INF-02 | CMP-13 / CMP-14 in INF-06 |
| CN-only integration | CMP-11, CMP-12 in INF-02 | — |
| Middleware (CDC) | CMP-15, CMP-16 in INF-02 | CMP-15, CMP-16 in INF-07 |
| ERP (Function + SLT) | CMP-33, CMP-34 in INF-01 | CMP-35 in INF-08 |
| Databases (HA groups) | CMP-17 through CMP-21 in INF-03 | CMP-17 through CMP-21 in INF-09 |
| NA K8s peer backends | — | CMP-22 through CMP-24 in INF-05 |

Infra links: LNK-01 / LNK-02 (office to CN/NA), LNK-03 (CN↔NA backbone),
LNK-04 (NA↔AWS), LNK-05 (NA↔Azure).

## 4. Integration Points (key flows)

| # | From | To | Protocol | Auth |
|---|------|----|----------|------|
| 1 | Employee browser | INF-16 / INF-19 → INF-17 / INF-20 → INF-18 / INF-21 | HTTPS | — |
| 2 | INF-18 / INF-21 | CMP-01 | HTTPS | internal access authentication |
| 3 | CMP-01 | CMP-02 | HTTPS | session token |
| 4 | CMP-02 | CMP-03 through CMP-10 | HTTPS | service auth |
| 5 | CMP-03 through CMP-10 | CMP-11 / CMP-12 / CMP-13 | HTTPS | OAuth2_ClientCredentials |
| 6 | CMP-03 through CMP-10 | CMP-14 | TCP (Kafka) | SASL_SCRAM |
| 7 | CMP-13 | CMP-33 / CMP-34 / CMP-35 | TCP/RFC | Kerberos (SAP logon ticket) |
| 8 | CMP-16 | CMP-15 | TCP | UserPassword |
| 9 | CMP-15 | CMP-14 | Kafka | SASL_SCRAM |
| 10 | CMP-03 through CMP-10 | CMP-17 through CMP-21 | JDBC (search: HTTPS) | UserPassword (K8s Secret) |
| 11 | CMP-01 | INF-22 | HTTPS/SAML | SAML 2.0 (AUTH-01) |
| 12 | CMP-03 through CMP-10 | CMP-25 through CMP-32 | HTTPS / messaging | SASL_SCRAM, OAuth2 |

Notes: IDOC-not-present-here; SLT and CDC (CMP-16) are the replication mechanisms.

## 5. Constraints

- NA multi-zone discipline: only INF-06 (CMP-13 / CMP-14) may mediate
  cross-application calls; SAP CMP-35 is isolated in INF-08.
- CDC (CMP-16 in both regions) is the only cross-region data-sync mechanism for
  order data; no direct cross-region DB replication.
- DB zones (INF-03 / INF-09) reachable only from backend services
  (CMP-03 through CMP-10); all DBs are HA groups.
- TLS 1.2+ everywhere; no hardcoded credentials.

## 6. Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | INF-17 / INF-20 (CN/NA WAF) enablement decision (currently optional in both regions) | No |
| TBD-02 | Cross-region failover RTO/RPO targets | Yes (program) |
