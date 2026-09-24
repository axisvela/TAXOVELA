# Requirements Document — Service Delivery Platform (SDP, NA Migration)
**Version**: 1.0  |  **Project ID**: SDP-NA-001  |  **Classification**: Acme Confidential

> System codes INF-04..INF-03 resolve via `input/systems-registry.md`.

**Scope**: Existing platform extended to NA (reverse-engineered, scrubbed)

---

## 1. Project Overview

SDP is the service supply-chain operations platform (~40 Java/SpringCloud
microservices). This program migrates/extends it to serve NA while keeping
the primary deployment in the CN primary DC. The platform integrates with
SAP, three satellite DCs, Azure-hosted systems, and external 3PL partners.

## 2. Deployment — CN Primary DC (three-tier)

| Zone | Contents |
|------|----------|
| Ingress | INF-04 (TLS termination, OAuth2), INF-03 |
| DMZ | K8s cluster: CMP-01, CMP-02, CMP-03 |
| Intranet | CMP-04, CMP-05, CMP-06, CMP-07, CMP-08, CMP-09 group (10 svc), CMP-10 group (22 svc) |
| DB Zone | CMP-12, CMP-13, CMP-14, CMP-15, CMP-16 (1M+2S each), CMP-17 (3M+3S), CMP-18 (3 replicas), CMP-19 (3 nodes) |

Group membership (listed once; all flows below use codes only):

- CMP-09 members: rms, tms, oms, wms, mds, ips, autopilot, ves, cfs, scs
- CMP-10 members: wms, oms, pps, eta, scs, auth, pbs, rns, vrs, ibs, cfs, lvr, tms, pms, mds, rms, ws-stock, rms-xdoc, data, sys, wms-xdoc

## 3. Satellite Locations

| Location | Systems | Connectivity |
|----------|---------|--------------|
| dc-us (US DC) | CMP-20, CMP-21, CMP-22, CMP-23, INF-09, INF-10 | CMP-04 (HTTPS/BasicAuth), VPN/MPLS |
| dc-cn-secondary | CMP-24, CMP-25, CMP-26, CMP-27, CMP-28 | HTTPS/OAuth2, TCP SASL/SCRAM |
| dc-cn-support | CMP-29, CMP-30 | HTTPS/OAuth2 |
| Azure | CMP-36, CMP-37, CMP-38, CMP-39 | HTTPS/OAuth2, TCP SASL/SCRAM |
| SAP landscape | CMP-31 → CMP-32 / CMP-33 / CMP-34; CMP-35 | TCP/RFC; HTTPS/BasicAuth |
| 3PL (Internet) | CMP-40, CMP-41, CMP-42, CMP-43, CMP-44, CMP-45 | HTTPS/OAuth2, TCP/EDI |
| partner file hub (Internet) | CMP-46, CMP-47, CMP-48 | SFTP |

## 4. Integration Points (key flows)

| # | From | To | Protocol | Port | Auth |
|---|------|----|----------|------|------|
| 1 | External client | INF-04 | HTTPS | 443 | OAuth2 |
| 2 | INF-04 | CMP-01 | HTTPS | 443 | — |
| 3 | CMP-03 | CMP-02 | HTTPS | 443 | OAuth2 |
| 4 | CMP-02 | CMP-04 | HTTPS | 443 | BasicAuth |
| 5 | CMP-04 | CMP-09 / CMP-10 | HTTPS | 443 | BasicAuth |
| 6 | CMP-06..CMP-10 | CMP-05 | TCP | 9093 | SASL/SCRAM |
| 7 | CMP-06..CMP-10 | CMP-12..CMP-16 | TCP/JDBC | 3306 | User/Password (K8s Secret) |
| 8 | CMP-06..CMP-10 | CMP-17 | TCP | 6379 | BasicAuth |
| 9 | CMP-06..CMP-10 | CMP-19 | HTTPS | 19200 | BasicAuth |
| 10 | CMP-06..CMP-10 | CMP-18 | TCP | 5672 | BasicAuth |
| 11 | CMP-11 | partner files | TCP | — | SASL/SCRAM |
| 12 | CMP-06..CMP-10 | CMP-31 | TCP/RFC | 33xx | SAP Logon Ticket |
| 13 | CMP-06..CMP-10 | CMP-35 | HTTPS | 443 | BasicAuth |
| 14 | CMP-06..CMP-10 | CMP-40..CMP-45 | HTTPS / TCP | 443 / EDI | OAuth2 / — |
| 15 | CMP-06..CMP-10 | CMP-46..CMP-48 | SFTP | 22 | SSH key |

## 5. User Authentication

| Entry | Roles | Auth Server | Protocol |
|-------|-------|-------------|----------|
| CMP-03 | Internal ops, BU users | INF-09 | SAML 2.0 |
| External portals | Partners, carriers | INF-10 | OAuth2/OIDC |

Authorization via the central AuthZ Platform (RBAC).

## 6. Constraints

- All cross-app traffic must traverse CMP-04 or CMP-05 (InfraSec mandate).
- CMP-31..CMP-34 access only via RFC from the Intranet zone; no SAP exposure to DMZ.
- DB Zone reachable only from Intranet services; every DB link is a HA group.
- 3PL/partner file hub traffic terminates at INF-04 (DMZ) — never directly at Intranet.
- TLS 1.2+ everywhere; no hardcoded credentials.

## 7. Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | NA cut-over sequence for CMP-10 group | Yes (program) |
| TBD-02 | CMP-11 → CMP-05 replacement roadmap | No |
