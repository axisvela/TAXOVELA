# Requirements Document — Order Query Platform (OVP ROW)
**Version**: 1.0  |  **Project ID**: OVP-ROW-001  |  **Classification**: Acme Confidential
**Scope**: New AWS-hosted application federating multi-DC data (textual names scrubbed; reference image unchanged)

> All systems/services are referenced by SYS-nn codes — resolve every code
> via `input/systems-registry.md` (single source of truth).

---

## 1. Project Overview

OVP ROW provides a single global order-query view. The platform is hosted on
AWS US; order data is federated from source systems in four private DCs and
two Azure EDW platforms. All integration is mediated — no direct
system-to-system calls.

## 2. Applications in Scope

| System | Type | Location | Scope |
|--------|------|----------|-------|
| SYS-05 | Frontend | AWS US, Public subnet (DMZ) | Full stack |
| SYS-06 – SYS-23 | Backend | AWS US, Private subnet (App Zone) | Full stack |
| SYS-25 / SYS-26 | Database | AWS US, Private subnet (DB Zone) | Full |
| SYS-27 | Cache | AWS US, Private subnet (DB Zone) | Full |
| SYS-28 | Object store | AWS US | Full |
| SYS-24 | Backend | AWS US, App Zone | Full stack |
| SYS-01 / SYS-02 | Identity | dc-us | Integration boundary only |
| SYS-03 / SYS-04 | Portal | dc-us, DMZ | Integration boundary only |
| SYS-29 / SYS-30 / SYS-31 | Integration | dc-us / dc-us-na | Integration boundary only |
| SYS-32 – SYS-36 | Message bus | all DCs | Integration boundary only |
| SYS-37 | Database | dc-us-na, DB zone | Existing (integration boundary) |
| SYS-38 – SYS-53 | Mixed | 4 DCs | See `input/api/cmdb-export.csv` |
| SYS-54 – SYS-57 | SaaS / data | Azure | Integration boundary only |
| SYS-58 | Platform | all K8s clusters | Internal K8s platform substrate |

## 3. Backend Services (App Zone K8s)

SYS-07, SYS-08, SYS-09, SYS-10, SYS-11, SYS-12, SYS-13, SYS-14, SYS-15,
SYS-16, SYS-17, SYS-18, SYS-19, SYS-20, SYS-21, SYS-22, SYS-23
(all Java/Spring; SYS-12 is React; SYS-13–SYS-21 are Kafka consumers).

## 4. Integration Points

| # | From | To | Protocol | Auth | Notes |
|---|------|----|----------|------|-------|
| 1 | Internal user | SYS-01 | HTTPS/SAML | SAML 2.0 | Via dc-us |
| 2 | External user | SYS-02 | HTTPS/SAML | SAML 2.0 | Via dc-us |
| 3 | User browser | SYS-05 | HTTPS | OAuth2 | Public subnet DMZ |
| 4 | SYS-05 | SYS-06 | HTTPS | OAuth2 | WAF in path |
| 5 | External system apps | SYS-29 | HTTPS | OAuth2 | External entry |
| 6 | Backend services | SYS-30 / SYS-31 | HTTPS | OAuth2 | All API calls mediated |
| 7 | SYS-13 – SYS-21 | Kafka clusters | TCP | SASL/SCRAM | Per-source topics |
| 8 | Services | SYS-25/SYS-26 | TCP/JDBC | User/Password | DB Zone only |
| 9 | Services | SYS-27 | TCP | Password | Cache |
| 10 | Services | SYS-28 | HTTPS | IAM | Object store |
| 11 | SYS-15 | SYS-57 (Azure CN North) | HTTPS | OAuth2 | Data stays in-country |
| 12 | Every DC | AWS VPC | MPLS | — | Firewall on each boundary |

## 5. Data Residency & Security

- PRC-sourced order rows are queried in-place against SYS-57 (Azure CN
  North); no cross-border replication.
- DB credentials in AWS Secrets Manager; Kafka SASL/SCRAM credentials
  likewise.
- TLS 1.2+ on every hop; MPLS links are carrier-encrypted.

## 6. Constraints

- Integration only via SYS-29 / SYS-30 / SYS-31 / SYS-32–SYS-36
  (InfraSec mandate).
- In the NA-DC (multi-zone model), SYS-35/SYS-36 and SYS-31 must sit in
  the NA-PROD-INA-INTEGRATION zone.
- SYS-37 remains in dc-us-na DB zone (existing).

## 7. Open Items

| ID | Item | Blocking |
|----|------|----------|
| TBD-01 | SYS-25/SYS-26 sizing for ROW order volume | No |
| TBD-02 | SYS-23 HA topology | No |
