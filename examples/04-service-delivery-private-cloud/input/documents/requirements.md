# Requirements Document — Service Delivery Platform (SSOC, NA Migration)
**Version**: 1.0  |  **Project ID**: SSOC-NA-001  |  **Classification**: Acme Confidential

> System codes SYS-01..SYS-52 resolve via `input/systems-registry.md`.

**Scope**: Existing platform extended to NA (reverse-engineered, scrubbed)

---

## 1. Project Overview

SSOC is the service supply-chain operations platform (~40 Java/SpringCloud
microservices). This program migrates/extends it to serve NA while keeping
the primary deployment in the CN primary DC. The platform integrates with
SAP, three satellite DCs, Azure-hosted systems, and external 3PL partners.

## 2. Deployment — CN Primary DC (three-tier)

| Zone | Contents |
|------|----------|
| Ingress | SYS-01 (TLS termination, OAuth2), SYS-52 |
| DMZ | K8s cluster: SYS-02, SYS-03, SYS-04 |
| Intranet | SYS-05, SYS-06, SYS-07, SYS-08, SYS-09, SYS-10 group (10 svc), SYS-11 group (22 svc) |
| DB Zone | SYS-12, SYS-13, SYS-14, SYS-15, SYS-16 (1M+2S each), SYS-17 (3M+3S), SYS-18 (3 replicas), SYS-19 (3 nodes) |

Group membership (listed once; all flows below use codes only):

- SYS-10 members: rms, tms, oms, wms, mds, ips, autopilot, ves, cfs, scs
- SYS-11 members: wms, oms, pps, eta, scs, auth, pbs, rns, vrs, ibs, cfs, lvr, tms, pms, mds, rms, ws-stock, rms-xdoc, data, sys, wms-xdoc

## 3. Satellite Locations

| Location | Systems | Connectivity |
|----------|---------|--------------|
| dc-us (US DC) | SYS-25, SYS-26, SYS-27, SYS-28, SYS-29, SYS-30 | SYS-05 (HTTPS/BasicAuth), VPN/MPLS |
| dc-cn-secondary | SYS-31, SYS-32, SYS-33, SYS-34, SYS-35 | HTTPS/OAuth2, TCP SASL/SCRAM |
| dc-cn-support | SYS-36, SYS-37 | HTTPS/OAuth2 |
| Azure | SYS-38, SYS-39, SYS-40, SYS-41 | HTTPS/OAuth2, TCP SASL/SCRAM |
| SAP landscape | SYS-20 → SYS-21 / SYS-22 / SYS-23; SYS-24 | TCP/RFC; HTTPS/BasicAuth |
| 3PL (Internet) | SYS-42, SYS-43, SYS-44, SYS-45, SYS-46, SYS-47 | HTTPS/OAuth2, TCP/EDI |
| partner file hub (Internet) | SYS-48, SYS-49, SYS-50 | SFTP |

## 4. Integration Points (key flows)

| # | From | To | Protocol | Port | Auth |
|---|------|----|----------|------|------|
| 1 | External client | SYS-01 | HTTPS | 443 | OAuth2 |
| 2 | SYS-01 | SYS-02 | HTTPS | 443 | — |
| 3 | SYS-04 | SYS-03 | HTTPS | 443 | OAuth2 |
| 4 | SYS-03 | SYS-05 | HTTPS | 443 | BasicAuth |
| 5 | SYS-05 | SYS-10 / SYS-11 | HTTPS | 443 | BasicAuth |
| 6 | SYS-07..SYS-11 | SYS-06 | TCP | 9093 | SASL/SCRAM |
| 7 | SYS-07..SYS-11 | SYS-12..SYS-16 | TCP/JDBC | 3306 | User/Password (K8s Secret) |
| 8 | SYS-07..SYS-11 | SYS-17 | TCP | 6379 | BasicAuth |
| 9 | SYS-07..SYS-11 | SYS-19 | HTTPS | 19200 | BasicAuth |
| 10 | SYS-07..SYS-11 | SYS-18 | TCP | 5672 | BasicAuth |
| 11 | SYS-51 | partner files | TCP | — | SASL/SCRAM |
| 12 | SYS-07..SYS-11 | SYS-20 | TCP/RFC | 33xx | SAP Logon Ticket |
| 13 | SYS-07..SYS-11 | SYS-24 | HTTPS | 443 | BasicAuth |
| 14 | SYS-07..SYS-11 | SYS-42..SYS-47 | HTTPS / TCP | 443 / EDI | OAuth2 / — |
| 15 | SYS-07..SYS-11 | SYS-48..SYS-50 | SFTP | 22 | SSH key |

## 5. User Authentication

| Entry | Roles | Auth Server | Protocol |
|-------|-------|-------------|----------|
| SYS-04 | Internal ops, BU users | SYS-29 | SAML 2.0 |
| External portals | Partners, carriers | SYS-30 | OAuth2/OIDC |

Authorization via the central AuthZ Platform (RBAC).

## 6. Constraints

- All cross-app traffic must traverse SYS-05 or SYS-06 (InfraSec mandate).
- SYS-20..SYS-23 access only via RFC from the Intranet zone; no SAP exposure to DMZ.
- DB Zone reachable only from Intranet services; every DB link is a HA group.
- 3PL/partner file hub traffic terminates at SYS-01 (DMZ) — never directly at Intranet.
- TLS 1.2+ everywhere; no hardcoded credentials.

## 7. Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | NA cut-over sequence for SYS-11 group | Yes (program) |
| TBD-02 | SYS-51 → SYS-06 replacement roadmap | No |
