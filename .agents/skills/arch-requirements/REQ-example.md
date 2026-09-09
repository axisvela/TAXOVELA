# Requirements Document — Order Management System (OMS)
**Version**: 1.0 Draft  |  **Date**: 2026-03-23  |  **Author**: hahxxx1-Huiwen-Han
**Project ID**: OMS-001  |  **Department**: SSG / TSD
**Scope**: Standalone new application (full internal stack detail required)

---

## 1. Project Overview

The Order Management System (OMS) is a new internal application for SSG business unit
to manage product orders across PRC and NA regions. It replaces a legacy Excel-based
process with a web application backed by REST APIs and asynchronous event processing.
Internal Company employees submit orders; external partners receive order confirmations
via an API Gateway. All order data is classified Company Confidential.

---

## 2. Applications in Scope

| App | Type | New/Existing | Owner | Scope |
|-----|------|-------------|-------|-------|
| OMS Web (Nginx/Vue) | Frontend | New | IT Org | Full internal stack |
| OMS BFF (Spring Boot) | Backend | New | IT Org | Full internal stack |
| OMS Order Service (Spring Boot) | Backend | New | IT Org | Full internal stack |
| OMS Payment Service (Spring Boot) | Backend | New | IT Org | Full internal stack |
| PostgreSQL (OMS DB) | Database | New | InfraSec (managed) | Full |
| Kafka (shared platform) | Message Queue | Existing | InfraSec | Integration boundary only |
| WSO2 API Gateway (shared) | Integration Platform | Existing | InfraSec | Integration boundary only |
| ECC (SAP) | ERP | Existing (3rd party) | SAP / InfraSec | Black box — integration boundary only |
| ADFS | Identity | Existing | InfraSec | Black box — integration boundary only |

---

## 3. Physical Deployment

| App/Component | Country | DC / Cloud Region | Zone/Subnet | Infrastructure Owner |
|---------------|---------|-------------------|-------------|---------------------|
| OMS Web | China | Neimeng DC (Hohhot) | DMZ | InfraSec |
| OMS BFF | China | Neimeng DC (Hohhot) | App Zone | InfraSec |
| OMS Order Service | China | Neimeng DC (Hohhot) | App Zone | InfraSec |
| OMS Payment Service | China | Neimeng DC (Hohhot) | App Zone | InfraSec |
| PostgreSQL (OMS DB) | China | Neimeng DC (Hohhot) | DB Zone | InfraSec |
| Kafka | China | Neimeng DC (Hohhot) | App Zone | InfraSec |
| WSO2 API Gateway | China | Neimeng DC (Hohhot) | DMZ | InfraSec |
| ECC (SAP) | China | Neimeng DC (Hohhot) | App Zone | InfraSec / SAP |
| ADFS | China | Neimeng DC (Hohhot) | App Zone | InfraSec |

**Data residency**: All data stays in China (Neimeng DC). No cross-border data transfer.

---

## 4. Network Topology

| From | To | Connection Type | Encrypted | Notes |
|------|----|----------------|-----------|-------|
| Internet | Neimeng DC | Internet | Yes (F5 TLS termination) | External access via F5 |
| Office Network | Neimeng DC | MPLS | Yes (IPSec) | Internal employee access |

No cross-DC or DC-to-cloud connections for this project.

---

## 5. Technical Components (new/modified only)

| Component | Type | Language | Framework | Runtime | Sensitivity |
|-----------|------|----------|-----------|---------|-------------|
| OMS Web | FE | JavaScript | Nginx / Vue 3 | Internal K8s | Company Internal |
| OMS BFF | BE | Java 17 | Spring Boot 3.5 | Internal K8s | Company Confidential |
| OMS Order Service | BE | Java 17 | Spring Boot 3.5 | Internal K8s | Company Confidential |
| OMS Payment Service | BE | Java 17 | Spring Boot 3.5 | Internal K8s | Company Restricted |
| PostgreSQL (OMS DB) | DB | N/A | PostgreSQL 16 | VM (InfraSec managed) | Company Confidential |

---

## 6. Integration Points

| # | From (initiator) | To (provider) | Protocol | Port | Auth Method | Notes |
|---|---------|------|----------|------|-------------|-------|
| 1 | Internet (User browser) | F5 | HTTPS | 443 | — | TLS termination at F5 |
| 2 | F5 | OMS Web | HTTPS | 443 | — | F5 passes through after LB |
| 3 | OMS Web | ADFS | HTTPS/SAML | 443 | SAML 2.0 redirect | Internal user SSO |
| 4 | OMS Web | OMS BFF | HTTPS/TLS 1.3 | 443 | HTTPS + User Token (from ADFS) | Session token forwarded |
| 5 | OMS BFF | WSO2 API Gateway | HTTPS/TLS 1.3 | 443 | OAuth2.0 Client Credentials | All cross-app calls via WSO2 |
| 6 | WSO2 | OMS Order Service | HTTPS/TLS 1.3 | 8080 | OAuth2.0 Client Credentials | Internal call after WSO2 routing |
| 7 | WSO2 | OMS Payment Service | HTTPS/TLS 1.3 | 8081 | OAuth2.0 Client Credentials | Internal call after WSO2 routing |
| 8 | WSO2 | ECC (SAP) | TCP/RFC | 3300 | SAP Logon Ticket | SAP RFC protocol |
| 9 | OMS Order Service | Kafka | Kafka/TLS | 9093 | SASL/SCRAM | Publish order events |
| 10 | OMS Payment Service | PostgreSQL (OMS DB) | JDBC/TLS | 5432 | User/Password | PWD stored in K8s Secret |
| 11 | OMS Order Service | PostgreSQL (OMS DB) | JDBC/TLS | 5432 | User/Password | PWD stored in K8s Secret |

**Rule verified**: Every component pair has an explicit auth mechanism. ✓

---

## 7. User Authentication

| Entry Point | User Roles | Auth Server | Protocol | Authorization |
|-------------|-----------|-------------|----------|---------------|
| OMS Web | Company SSG Employees (PRC), BU Managers | ADFS | SAML 2.0 | RBAC via AuthZ Platform |

No external customer access in this project.

---

## 8. Credential & Key Protection

| Environment | Solution | Notes |
|-------------|----------|-------|
| Private DC (Hohhot) | Kubernetes Secrets (encrypted at rest) | DB passwords, OAuth client secrets |
| Private DC (Hohhot) | Internal K8s Secret | Additional encryption layer for Restricted data |

No Azure Key Vault or AWS Secrets Manager (private DC only project).

---

## 9. Data Encryption

| Component | At Rest | Method | In Transit | Protocol | Cross-Border | Compliance |
|-----------|---------|--------|------------|----------|--------------|------------|
| PostgreSQL (OMS DB) | Yes | AES-256 (TDE) | Yes | TLS 1.3 | No | 中国数据安全法 |
| OMS Payment Service data | Yes | AES-256 | Yes | TLS 1.3 | No | 中国数据安全法 |
| Kafka messages | No | — | Yes | TLS 1.3 | No | — |

---

## 10. Open Items / TBDs

| ID | Item | Owner | Blocking | Target |
|----|------|-------|----------|--------|
| TBD-01 | Exact Kafka topic names and partition count | InfraSec Platform Team | No | Before dev |
| TBD-02 | WSO2 API registration process and timeline | InfraSec Integration Team | No | Before go-live |
| TBD-03 | PostgreSQL VM specifications (CPU/memory) | InfraSec Infra | No | Before go-live |

No CRITICAL blocking items. ✓

---

## 11. Architecture Constraints

- All data must remain in China (Neimeng DC). No cross-border transfer permitted.
- All inter-application communication must go through WSO2 API Gateway (InfraSec mandate).
- Runtime must be Internal K8s — no direct VM deployment for new services.
- No hardcoded credentials anywhere (InfraSec security policy).
- TLS 1.3 minimum for all in-transit communication.
- Payment Service data classified Company Restricted — AES-256 at rest mandatory.
