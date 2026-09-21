# Requirements Document — Order Management System (OMS)
**Version**: 1.0 Draft  |  **Date**: 2026-03-23  |  **Author**: hahxxx1-Huiwen-Han
**Project ID**: OMS-001  |  **Department**: SSG / TSD
**Scope**: Standalone new application (full internal stack detail required)
**Model**: `req/v2` — entity-separated (see `standards/requirements-model-v2.yaml`)

---

## 1. Project Overview

The Order Management System (OMS) is a new internal application for the SSG
business unit to manage product orders. It replaces a legacy Excel-based process
with a web application backed by REST APIs and asynchronous event processing.
Internal Company employees submit orders; external partners receive order
confirmations via the API Gateway. The most sensitive data (payment data) is
classified **Company Confidential** / **Company Restricted**.

Data residency: all data stays in China (Neimeng DC). No cross-border transfer.

---

## 2. Infrastructure Topology

`node_kind` (topology role), `infra_type` (hosting category) and `network_type`
(network/security domain) are three independent fields.

| ID | Name | node_kind | infra_type | network_type | Parent | Country | Owner |
|----|------|-----------|------------|--------------|--------|---------|-------|
| INF-01 | Neimeng DC (Hohhot) | `data_center` | `private_cloud` | `prod_network` | — | CN | InfraSec |
| INF-02 | DMZ Zone | `network_zone` | `private_cloud` | `dmz` | INF-01 | CN | InfraSec |
| INF-03 | App Zone | `network_zone` | `private_cloud` | `prod_network` | INF-01 | CN | InfraSec |
| INF-04 | DB Zone | `network_zone` | `private_cloud` | `prod_network` | INF-01 | CN | InfraSec |
| INF-05 | Office Network | `office_network` | `office` | `office_network` | — | CN | InfraSec |
| INF-06 | Internet | `internet_network` | — | — | — | — | — |
| INF-07 | F5 BigIP | `load_balancer` | `private_cloud` | `dmz` | INF-02 | CN | InfraSec |
| INF-08 | ADFS | `identity_provider` | `private_cloud` | `prod_network` | INF-03 | CN | InfraSec |
| INF-09 | Internal K8s Secret Store | `key_management` | `private_cloud` | `prod_network` | INF-03 | CN | InfraSec |

> F5 and ADFS are **infrastructure appliances** (`INF-nn`), not components.

---

## 3. Systems in Scope

| ID | System | Type | Owner | Vendor | Scope |
|----|--------|------|-------|--------|-------|
| APP-01 | Order Management System | New | IT Org | — | Full internal stack |
| APP-02 | Integration Platform | Existing | IT Org | — | Boundary only (WSO2) |
| APP-03 | Messaging Platform | Existing | IT Org | — | Boundary only (Kafka) |
| APP-04 | ECC (SAP) | Existing | Third party | SAP | Black box — RFC boundary only |

---

## 4. Components & Services

Infrastructure and security appliances do not appear here; they are `infra` L4
nodes in §2.

| ID | System | Name | kind | component_role | Stack | At-rest enc | Sensitivity |
|----|--------|------|------|----------------|-------|-------------|-------------|
| CMP-01 | APP-01 | OMS Web | component | `web_frontend` | Vue 3.4 | — | Company Internal |
| CMP-02 | APP-01 | OMS BFF | service | `bff` | Java 17 / Spring Boot 3.5 | — | Company Confidential |
| CMP-03 | APP-01 | OMS Order Service | service | `backend_service` | Java 17 / Spring Boot 3.5 | — | Company Confidential |
| CMP-04 | APP-01 | OMS Payment Service | service | `backend_service` | Java 17 / Spring Boot 3.5 | AES-256 | Company Restricted |
| CMP-05 | APP-01 | PostgreSQL (OMS DB) | component | `database` | PostgreSQL 16 | AES-256 (TDE) | Company Confidential |
| CMP-06 | APP-02 | WSO2 API Gateway | component | `api_gateway` | — | — | Company Internal |
| CMP-07 | APP-03 | Kafka | component | `message_bus` | — | — | Company Confidential |
| CMP-08 | APP-04 | ECC RFC Interface | component | `integration_service` | — | — | Company Confidential |

CMP-08 is the single **black-box boundary component** for the external ECC
system: flows need a component endpoint, so an existing black-box system still
exposes one boundary component.

Stack bindings (`STK-nn`): `STK-01` Vue 3.4.0, `STK-02` Spring Boot 3.5.0,
`STK-03` Java 17, `STK-04` PostgreSQL 16 (EOL 2028-11-09).

---

## 5. Deployments

One component with N environments has N deployments; each deployment references
an `INF-nn` and never copies infra dictionaries.

| ID | Component | Env | deployment_type | location_type | Infra | runtime_type | Instances |
|----|-----------|-----|-----------------|---------------|-------|--------------|-----------|
| DEP-01 | CMP-01 OMS Web | prod | `private_cloud` | `data_center` | INF-02 (DMZ) | `container` | 2 |
| DEP-02 | CMP-02 OMS BFF | prod | `private_cloud` | `data_center` | INF-03 (App Zone) | `container` | 2 |
| DEP-03 | CMP-03 Order Svc | prod | `private_cloud` | `data_center` | INF-03 (App Zone) | `container` | 2 |
| DEP-04 | CMP-04 Payment Svc | prod | `private_cloud` | `data_center` | INF-03 (App Zone) | `container` | 2 |
| DEP-05 | CMP-05 OMS DB | prod | `private_cloud` | `data_center` | INF-04 (DB Zone) | `vm` | 1 |
| DEP-06 | CMP-06 WSO2 | prod | `private_cloud` | `data_center` | INF-02 (DMZ) | `container` | 2 |
| DEP-07 | CMP-07 Kafka | prod | `private_cloud` | `data_center` | INF-03 (App Zone) | `container` | 3 |

---

## 6. Component Communication Flows

Directed (caller → provider). Endpoints are always components; the external
sentinel `internet` is a source. Appliances are recorded in `via`, never as an
endpoint. Service-to-service auth is an **inline enum** on the flow.

| ID | From | To | Protocol | Port | auth_method | Encryption | Cross-border | via |
|----|------|----|----------|------|-------------|------------|--------------|-----|
| FLOW-01 | internet | CMP-01 | HTTPS | 443 | `none` | TLS1.3 | false | INF-07 (F5) |
| FLOW-02 | CMP-01 | CMP-02 | HTTPS | 443 | `none` | TLS1.3 | false | — |
| FLOW-03 | CMP-02 | CMP-06 | HTTPS | 443 | `OAuth2_ClientCredentials` | TLS1.3 | false | — |
| FLOW-04 | CMP-06 | CMP-03 | HTTPS | 8080 | `OAuth2_ClientCredentials` | TLS1.3 | false | — |
| FLOW-05 | CMP-06 | CMP-04 | HTTPS | 8081 | `OAuth2_ClientCredentials` | TLS1.3 | false | — |
| FLOW-06 | CMP-06 | CMP-08 | TCP/RFC | 3300 | `Kerberos` | TLS1.3 | false | — |
| FLOW-07 | CMP-03 | CMP-07 | Kafka | 9093 | `SASL_SCRAM` | TLS1.3 | false | — |
| FLOW-08 | CMP-03 | CMP-05 | JDBC | 5432 | `UserPassword` | TLS1.3 | false | — |
| FLOW-09 | CMP-04 | CMP-05 | JDBC | 5432 | `UserPassword` | TLS1.3 | false | — |

**Rule verified**: every flow has an `auth_method`. ✓

Note on FLOW-06: the SAP Logon Ticket is a ticket-based SSO mechanism that does
not map exactly onto the enum; it is recorded as `Kerberos` with the exact
mechanism in `notes`, and tracked as TBD-04.

---

## 7. Infra Network Links

Undirected infrastructure interconnections (`INF-nn` ↔ `INF-nn`). A carrier
circuit is a link, not a node.

| ID | Source infra | Target infra | method | Bandwidth | Encrypted | Redundancy |
|----|--------------|--------------|--------|-----------|-----------|------------|
| LNK-01 | INF-05 Office Network | INF-01 Neimeng DC | `mpls` | — | Yes (IPSec) | primary |
| LNK-02 | INF-06 Internet | INF-01 Neimeng DC | `internet` | — | No (TLS terminated at INF-07 F5) | primary |

No cross-DC or DC-to-cloud links for this project.

---

## 8. User / Entry Authentication

This entity is **user / entry authentication only** — service-to-service auth is
inline on the flows in §6. An identity-provider redirect (Web → ADFS SAML) is
captured here, not as a flow.

| ID | Subject | Entry Point | auth_server | Protocol | Authorization | Roles | MFA |
|----|---------|-------------|-------------|----------|---------------|-------|-----|
| AUTH-01 | user | CMP-01 OMS Web | INF-08 ADFS | SAML2 | RBAC (AuthZ Platform) | SSG Employees (PRC), BU Managers | — |

No external customer access in this project.

---

## 9. Credential & Key Protection

| Environment | Solution | Notes |
|-------------|----------|-------|
| Private DC (Hohhot) | Kubernetes Secrets (encrypted at rest) | DB passwords, OAuth client secrets |
| Private DC (Hohhot) | Internal K8s Secret (INF-09) | Additional encryption layer for Restricted data |

No Azure Key Vault or AWS Secrets Manager (private DC only project).
No hardcoded credentials. ✓

---

## 10. Open Items / TBDs

| ID | Item | Owner | Blocking |
|----|------|-------|----------|
| TBD-01 | Exact Kafka topic names and partition count | InfraSec Platform Team | No |
| TBD-02 | WSO2 API registration process and timeline | InfraSec Integration Team | No |
| TBD-03 | PostgreSQL VM specifications (CPU/memory) | InfraSec Infra | No |
| TBD-04 | Confirm the SAP Logon Ticket mapping to `Kerberos` vs a dedicated enum value | Security Architecture | No |

No CRITICAL blocking items. ✓

---

## 11. Architecture Constraints

- All data must remain in China (Neimeng DC). No cross-border transfer permitted.
- All inter-application communication must go through WSO2 API Gateway (InfraSec mandate).
- Runtime must be Internal K8s — no direct VM deployment for new services.
- No hardcoded credentials anywhere (InfraSec security policy).
- TLS 1.3 minimum for all in-transit communication.
- Payment Service data classified Company Restricted — AES-256 at rest mandatory.
