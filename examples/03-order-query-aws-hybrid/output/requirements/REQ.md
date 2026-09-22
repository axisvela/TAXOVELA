# Requirements Document - Order Query Platform (OQP ROW)
**Version**: 1.0  |  **Date**: 2026-09-14  |  **Author**: OpenCode
**Scope**: E2E cross-system solution. Existing applications are black boxes; full internal detail is required only for the new AWS-hosted application.
**Classification**: Acme Confidential

## 1. Project Overview

OQP ROW provides internal employees and external partners with a global order-query view. The new application is hosted in an AWS US VPC in N. Virginia and federates data from existing systems in US and China private data centers and Azure services. All cross-system integration is mediated by approved API gateways or Kafka; direct cross-system calls are prohibited.

The human source is `input/prompt.md`. The prompt-indexed diagram, structured requirements document, CMDB CSV, systems registry, `project.yaml`, and project `config.yaml` were used as supporting sources. Registry document names are authoritative for resolving stable `SYS-nn` identifiers.

## 2. Applications in Scope

| ID | Resolved name | System type | New / Existing | Owner | Scope / CMDB ID |
|---|---|---|---|---|---|
| SYS-01 | ADFS | Identity | Existing | TBD | Integration boundary |
| SYS-02 | Enterprise ID | Identity | Existing | TBD | Integration boundary |
| SYS-03 | SOWB(sales operation workbench) | Portal | Existing | TBD | Integration boundary |
| SYS-04 | external OP(order portal) site | Portal | Existing | TBD | Integration boundary |
| SYS-05 | OP(order portal)-row-web | Frontend | New | TBD | Full stack |
| SYS-06 | Gateway | Backend gateway | New | TBD | Full stack |
| SYS-07 | Order Portal | Backend | New | TBD | Full stack |
| SYS-08 | Order Report | Backend | New | TBD | Full stack |
| SYS-09 | Order Notification | Backend | New | TBD | Full stack |
| SYS-10 | Transform Service | Backend | New | TBD | Full stack |
| SYS-11 | Task Service | Backend | New | TBD | Full stack |
| SYS-12 | Order Web | Frontend | New | TBD | Full stack |
| SYS-13 | D365 Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-14 | OFS(order fulfill service) Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-15 | PRC Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-16 | SOS(salse order servie) Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-17 | IC(invoice service) Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-18 | LOS(logistics operation servie) Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-19 | SDS(service data service) Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-20 | SIS(supply intelligence service) Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-21 | NA Consumer | Kafka consumer | New | TBD | Full stack |
| SYS-22 | Consumer Task | Backend | New | TBD | Full stack |
| SYS-23 | XXL-Job scheduler | Scheduler | New | TBD | Full stack |
| SYS-24 | SOS(salse order servie) | Backend | Modified | IT Org | Full stack; A-XXXX-05 |
| SYS-25 | PostgreSQL ODS | Database | New | TBD | Full stack |
| SYS-26 | PostgreSQL DWS | Database | New | TBD | Full stack |
| SYS-27 | Redis | Cache | New | TBD | Full stack |
| SYS-28 | S3 | Object storage | New | TBD | Full stack |
| SYS-29 | DMZ-APIM | Integration gateway | Existing | TBD | Integration boundary |
| SYS-30 | APIM | Integration gateway | Existing | TBD | Integration boundary |
| SYS-31 | APIH | Integration gateway | Existing | TBD | Integration boundary |
| SYS-32 | kafka-us | Messaging | Existing | TBD | Integration boundary |
| SYS-33 | kafka-cn | Messaging | Existing | TBD | Integration boundary |
| SYS-34 | kafka-ikp | Messaging | Existing | TBD | Integration boundary |
| SYS-35 | kafka-us-na | Messaging | Existing | TBD | Integration boundary |
| SYS-36 | kafka-us-log | Messaging | Existing | TBD | Integration boundary |
| SYS-37 | OP(order portal) ES | Database | Existing | TBD | Integration boundary |
| SYS-38 | SDS(service data service) | Backend | Existing | IT Org | Integration boundary; A-XXXX-01 |
| SYS-39 | 2b service portal | Backend | Existing | IT Org | Integration boundary; A-XXXX-02 |
| SYS-40 | OOP(order open platform) | Backend | Existing | IT Org | Integration boundary; A-XXXX-03 |
| SYS-41 | order orchestration | Backend | Existing | IT Org | Integration boundary; A-XXXX-04 |
| SYS-42 | CSP(cload servie portal) | Backend | Existing | IT Org | Integration boundary; A-XXXX-10 |
| SYS-43 | IC(invoice service) | Backend | Existing | IT Org | Integration boundary; A-XXXX-11 |
| SYS-44 | LOS(logistics operation servie) | Backend | Existing | IT Org | Integration boundary; A-XXXX-12 |
| SYS-45 | Lakehouse | Data | Existing | Data Org | Integration boundary; A-XXXX-13 |
| SYS-46 | OP(order portal)-PRC | Backend | Existing | IT Org | Integration boundary; A-XXXX-14 |
| SYS-47 | SIS(supply intelligence service) | Backend | Existing | IT Org | Integration boundary; A-XXXX-15 |
| SYS-48 | GAP(general account platform)-OTC | Backend | Existing | IT Org | Integration boundary; A-XXXX-16 |
| SYS-49 | ECC | ERP | Existing | SAP Team | Black box; A-XXXX-17 |
| SYS-50 | IC(invoice service)-NA | Backend | Existing | IT Org | Integration boundary; A-XXXX-18 |
| SYS-51 | SIS(supply intelligence service)-NA | Backend | Existing | IT Org | Integration boundary; A-XXXX-19 |
| SYS-52 | GAP(general account platform)-OTC-NA | Backend | Existing | IT Org | Integration boundary; A-XXXX-20 |
| SYS-53 | Lakehouse-ROW | Data | Existing | Data Org | Integration boundary; A-XXXX-21 |
| SYS-54 | D365 | SaaS | Existing | IT Org | Integration boundary; A-XXXX-06 |
| SYS-55 | edge-cache | Backend | Existing | IT Org | Integration boundary; A-XXXX-07 |
| SYS-56 | ROW DWP(data warehosue platform) | Data | Existing | Data Org | Integration boundary; A-XXXX-08 |
| SYS-57 | PRC DWP(data warehosue platform) | Data | Existing | Data Org | Integration boundary; A-XXXX-09 |
| SYS-58 | Internal K8s Platform | Platform | Existing | TBD | Platform substrate |

## 3. Physical Deployment

| Systems | Country / Region | DC / Cloud region | Zone / Subnet | Infrastructure owner |
|---|---|---|---|---|
| SYS-05 | US / NA | AWS US, N. Virginia | Public subnet (DMZ), frontend K8s | TBD |
| SYS-06-SYS-24 | US / NA | AWS US, N. Virginia | Private subnet (App Zone), backend K8s; SYS-24 beside cluster | IT Org for SYS-24; others TBD |
| SYS-25-SYS-27 | US / NA | AWS US, N. Virginia | Private subnet (DB Zone) | TBD |
| SYS-28 | US / NA | AWS US, N. Virginia | AWS object storage; exact network endpoint placement TBD | TBD |
| SYS-01-SYS-02, SYS-29-SYS-30, SYS-32, SYS-38-SYS-41 | US / NA | dc-us, City C / State X | App/integration zone TBD; SYS-38-SYS-41 are App Zone | IT Org for SYS-38-SYS-41; others TBD |
| SYS-03-SYS-04 | US / NA | dc-us, City C / State X | Public subnet (DMZ) | TBD |
| SYS-31, SYS-35-SYS-36 | US / NA | dc-us-na, City C / State X | NA-PROD-INA-INTEGRATION | TBD |
| SYS-37 | US / NA | dc-us-na, City C / State X | NA-PROD-INA-DB | TBD |
| SYS-50-SYS-52 | US / NA | dc-us-na, City C / State X | NA-PROD-INA-K8S | IT Org |
| SYS-53 | US / NA | dc-us-na, City C / State X | NA-PROD-INA-DB | Data Org |
| SYS-33, SYS-48-SYS-49 | CN / APAC-CN | dc-cn-primary, City A / Province A | Intranet; exact SYS-33 segment TBD | IT Org / SAP Team as listed above |
| SYS-34, SYS-42-SYS-47 | CN / APAC-CN | dc-cn-secondary, City B / Province B | Intranet; exact SYS-34 segment TBD | IT Org / Data Org as listed above |
| SYS-54-SYS-56 | US / NA | Azure US, exact region TBD | SaaS | IT Org / Data Org as listed above |
| SYS-57 | CN / APAC-CN | Azure CN North, exact numbered region TBD | EDW | Data Org |
| SYS-58 | US / NA | All OQP ROW K8s clusters in AWS US | Public and private application subnets | TBD |

No IP addresses or CIDR ranges are specified or required by the available sources.

## 4. Network Topology

| Connection | Type | Encryption | Notes |
|---|---|---|---|
| dc-us to AWS US VPC | MPLS | Carrier-encrypted plus TLS 1.2+ application traffic | Firewall at both boundaries |
| dc-us-na to AWS US VPC | MPLS | Carrier-encrypted plus TLS 1.2+ application traffic | Firewall at both boundaries |
| dc-cn-primary to AWS US VPC | MPLS | Carrier-encrypted plus TLS 1.2+ application traffic | Firewall at both boundaries; PRC rows must not traverse this link |
| dc-cn-secondary to AWS US VPC | MPLS | Carrier-encrypted plus TLS 1.2+ application traffic | Firewall at both boundaries; PRC rows must not traverse this link |
| Azure services to approved mediation boundary | Network path TBD | TLS 1.2+ | No direct application-to-source calls |

## 5. Technical Components (New / Modified Only)

| ID / Component | Type | Language | Framework | Runtime | Sensitivity |
|---|---|---|---|---|---|
| SYS-05 - OP(order portal)-row-web | FE | JavaScript/TypeScript version TBD | Nginx and React versions TBD | SYS-58 frontend K8s cluster | Acme Confidential |
| SYS-06 - Gateway | API | TBD | TBD | SYS-58 backend K8s cluster | Acme Confidential |
| SYS-07-SYS-11 | BE | Java version TBD | Spring version TBD | SYS-58 backend K8s cluster | Acme Confidential |
| SYS-12 - Order Web | FE | JavaScript/TypeScript version TBD | React version TBD | SYS-58 backend K8s cluster | Acme Confidential |
| SYS-13-SYS-23 | BE / MQ consumers / scheduler | Java version TBD | Spring version TBD | SYS-58 backend K8s cluster | Acme Confidential |
| SYS-24 - SOS(salse order servie) | BE | TBD | TBD | AWS US Private subnet (App Zone), outside backend cluster | Acme Confidential |
| SYS-25-SYS-26 | DB | SQL | PostgreSQL version TBD | AWS managed/self-managed selection TBD | Acme Confidential |
| SYS-27 | DB / cache | TBD | Redis version TBD | AWS managed/self-managed selection TBD | Acme Confidential |
| SYS-28 | Storage | N/A | Amazon S3 | AWS managed service | Acme Confidential |

## 6. Integration Points

Every integration must carry protocol, port, and authentication metadata. Ports not supplied by source material remain `TBD`; design must not silently infer them.

| ID | From | To | Protocol | Port | Auth method | Notes |
|---|---|---|---|---|---|---|
| INT-001 | Internal employee | SYS-01 - ADFS | HTTPS / SAML 2.0 | TBD | SAML 2.0 | User authentication |
| INT-002 | External partner | SYS-02 - Enterprise ID | HTTPS / SAML 2.0 | TBD | SAML 2.0 | User authentication |
| INT-003 | SYS-01 - ADFS | SYS-03 - SOWB(sales operation workbench) | HTTPS / SAML 2.0 | TBD | SAML 2.0 | Internal portal SSO |
| INT-004 | SYS-02 - Enterprise ID | SYS-04 - external OP(order portal) site | HTTPS / SAML 2.0 | TBD | SAML 2.0 | External portal SSO |
| INT-005 | User browser | SYS-05 - OP(order portal)-row-web | HTTPS | TBD | OAuth 2.0; flow TBD | Public entry; WAF required |
| INT-006 | SYS-05 - OP(order portal)-row-web | SYS-06 - Gateway | HTTPS | TBD | OAuth 2.0 | Cross-subnet via security controls |
| INT-007 | SYS-06 - Gateway | SYS-07-SYS-24 application services | HTTPS | TBD | OAuth 2.0 | Exact service call matrix TBD |
| INT-008 | External system applications | SYS-29 - DMZ-APIM | HTTPS | TBD | OAuth 2.0 Client Credentials | Mandatory external mediation |
| INT-009 | OQP ROW backend services | SYS-30 - APIM | HTTPS | TBD | OAuth 2.0 Client Credentials | Mandatory internal mediation |
| INT-010 | OQP ROW backend services | SYS-31 - APIH | HTTPS | TBD | OAuth 2.0 Client Credentials | Mandatory NA mediation |
| INT-011 | SYS-13-SYS-21 consumers | SYS-32-SYS-36 designated Kafka clusters | TCP / Kafka | TBD | SASL/SCRAM | Exact consumer/topic/cluster matrix TBD |
| INT-012 | OQP ROW application services | SYS-25 - PostgreSQL ODS | TCP / JDBC | TBD | User/password from AWS Secrets Manager | DB Zone only |
| INT-013 | OQP ROW application services | SYS-26 - PostgreSQL DWS | TCP / JDBC | TBD | User/password from AWS Secrets Manager | DB Zone only |
| INT-014 | OQP ROW application services | SYS-27 - Redis | TCP / Redis | TBD | Password from AWS Secrets Manager | DB Zone only |
| INT-015 | OQP ROW application services | SYS-28 - S3 | HTTPS | TBD | AWS IAM role | Object storage |
| INT-016 | SYS-15 - PRC Consumer | SYS-57 - PRC DWP(data warehosue platform) | HTTPS | TBD | OAuth 2.0 Client Credentials | Query in China; no row replication to AWS |
| INT-017 | SYS-38-SYS-41 | SYS-30 / SYS-32 | HTTPS or TCP / Kafka as designated | TBD | OAuth 2.0 Client Credentials or SASL/SCRAM | Exact mediation mapping TBD; no direct calls |
| INT-018 | SYS-42-SYS-47 | SYS-34 | TCP / Kafka | TBD | SASL/SCRAM | Per-source topics TBD |
| INT-019 | SYS-48-SYS-49 | SYS-33 | TCP / Kafka | TBD | SASL/SCRAM | Per-source topics TBD |
| INT-020 | SYS-50-SYS-53 | SYS-31 / SYS-35 / SYS-36 | HTTPS or TCP / Kafka as designated | TBD | OAuth 2.0 Client Credentials or SASL/SCRAM | Exact mediation mapping TBD; no direct calls |
| INT-021 | SYS-54-SYS-56 | Approved SYS-29/SYS-30 or designated Kafka boundary | HTTPS or TCP / Kafka as designated | TBD | OAuth 2.0 Client Credentials or SASL/SCRAM | Exact source mediation mapping TBD; no direct calls |

## 7. User Authentication

| Entry point | User roles | Auth server | Protocol | Authorization |
|---|---|---|---|---|
| SYS-03 / SYS-05 internal path | Internal employees | SYS-01 - ADFS | SAML 2.0 | RBAC via AuthZ Platform; role model TBD |
| SYS-04 / SYS-05 external path | External partners | SYS-02 - Enterprise ID | SAML 2.0 | RBAC via AuthZ Platform; role model TBD |

## 8. Credential and Key Protection

| Environment | Solution | Notes |
|---|---|---|
| AWS | AWS Secrets Manager and AWS KMS | Store DB, Redis, OAuth client, and Kafka SASL/SCRAM secrets; rotation periods TBD; no hardcoded credentials |
| Private DC | Existing enterprise secret-management solution TBD | Gateway and Kafka secret storage/rotation ownership TBD |
| Azure | Existing Azure secret-management solution TBD | Credentials remain behind approved mediation boundaries |

## 9. Data Encryption

| Component / flow | At rest | In transit | Cross-border | Compliance |
|---|---|---|---|---|
| SYS-25-SYS-28 AWS data stores | Encryption required; methods TBD | TLS 1.2+ | Non-PRC data only | Acme Confidential controls |
| API gateway and application flows | N/A | TLS 1.2+ | Subject to source residency | Acme Confidential controls |
| Kafka flows | Broker encryption at rest TBD | TLS 1.2+ with SASL/SCRAM | PRC row payloads must not leave China | PRC data-residency constraint |
| SYS-57 PRC data | Existing at-rest method TBD | TLS 1.2+ | No; query executes in-country and rows are not replicated | PRC data-residency constraint; legal basis TBD |

## 10. Open Items / TBDs

| ID | Item | Owner | Target date | Blocking |
|---|---|---|---|---|
| TBD-01 | Size SYS-25 and SYS-26 for ROW order volume. | TBD | TBD | No |
| TBD-02 | Define SYS-23 high-availability topology. | TBD | TBD | No |
| TBD-03 | Confirm exact Azure US and Azure China numbered regions. | Cloud / Data Org | TBD | No |
| TBD-04 | Confirm all service ports; every design edge must retain an explicit `TBD` until confirmed. | Network / application owners | TBD | No |
| TBD-05 | Define exact consumer/topic/Kafka-cluster and API gateway/source mappings. | Integration owner | TBD | No |
| TBD-06 | Confirm runtime/framework versions and managed-service selections for new components. | Application owner | TBD | No |
| TBD-07 | Confirm at-rest encryption methods, secret rotation periods, and non-AWS secret platforms. | Security / platform owners | TBD | No |
| TBD-08 | Define internal and partner RBAC roles and confirm AuthZ Platform ownership. | Security / application owner | TBD | No |
| TBD-09 | Resolve the OQP/OVP acronym discrepancy; use OQP ROW from the human source until confirmed. | Project owner | TBD | No |

No critical requirements gap remains: each component has a physical location identifier, external connections have explicit authentication, no hardcoded credentials are permitted, and the PRC residency constraint is explicit. Remaining `TBD` items constrain detailed design but do not prevent architecture design from starting.

## 11. Architecture Constraints

- Host the new application in the AWS US N. Virginia VPC using public DMZ, private App Zone, and private DB Zone subnets.
- Place SYS-05 in the frontend K8s cluster and SYS-06-SYS-23 in the backend K8s cluster on SYS-58; place SYS-24 beside the backend cluster.
- Keep SYS-25-SYS-27 in the private DB subnet and access SYS-28 over HTTPS with AWS IAM.
- Mediate every cross-system interaction through SYS-29, SYS-30, SYS-31, or SYS-32-SYS-36. Direct cross-system calls are prohibited.
- Place SYS-31 and SYS-35-SYS-36 in NA-PROD-INA-INTEGRATION and retain SYS-37 in NA-PROD-INA-DB.
- Use MPLS between each private DC and AWS, firewalls at every boundary, and TLS 1.2+ on every application hop.
- Keep PRC-sourced rows in China. SYS-15 queries SYS-57 in-country; no PRC row replication to AWS is allowed.
- Use only masked `A-XXXX-nn` CMDB identifiers in outputs. Do not include IP addresses or CIDR ranges.
