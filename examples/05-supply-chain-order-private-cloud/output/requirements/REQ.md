# Requirements Document - Supply-Chain Order Platform (OSP)
**Version**: 1.0 Draft | **Date**: 2026-09-14 | **Author**: TBD
**Project ID**: OSP-001 | **Classification**: Acme Confidential
**Scope**: Modification of an existing active-active platform. OSP-owned components are documented as a full internal stack; ERP, identity, integration platforms, and peer applications are treated as existing integration boundaries where their internals are not evidenced.

## 1. Project Overview
OSP provides supply-chain order processing for employees in China (CN) and North America (NA). The existing platform operates active-active across `dc-cn-primary` and `dc-us`, integrates with the local ERP landscape, exchanges data with regional and cloud peer applications, and uses CDC-based synchronization without direct cross-region database replication.

The design must preserve regional symmetry where the source architecture is symmetric while retaining deliberate differences: CN has `SYS-14` through `SYS-16` and five persistence technologies, whereas NA uses `SYS-41` as its sole API mediator and has no MySQL equivalent.

## 2. Applications in Scope
| App/System IDs | Type | New/Existing | Owner | Scope |
|---|---|---|---|---|
| `SYS-01`-`SYS-26` | CN OSP ingress, application, integration, middleware, ERP, and persistence stack | Existing, modified design baseline | TBD | Full stack except ERP boundaries `SYS-20`/`SYS-21` |
| `SYS-27` | Enterprise identity service | Existing | TBD | Authentication boundary only |
| `SYS-28`-`SYS-49` | NA OSP ingress, application, integration, middleware, ERP, and persistence stack | Existing, modified design baseline | TBD | Full stack except ERP boundary `SYS-45` |
| `SYS-50`-`SYS-54` | CN peer applications | Existing | TBD | Integration boundary only |
| `SYS-55` | AWS US peer application | Existing | Third party/TBD | Integration boundary only |
| `SYS-56`-`SYS-57` | Azure US peer applications | Existing | Third party/TBD | Integration boundary only |
| `SYS-58`-`SYS-60` | NA peer backends | Existing | TBD | Integration boundary only |

## 3. Physical Deployment
| App/Component | Country/Region | DC / Cloud Region | Zone/Subnet | Infrastructure Owner |
|---|---|---|---|---|
| `SYS-01`-`SYS-03` | CN | `dc-cn-primary` | `Intranet` | TBD |
| `SYS-04` | CN | `dc-cn-primary` | `Intranet` web tier | TBD |
| `SYS-05`-`SYS-17` | CN | `dc-cn-primary` | `App Zone` | TBD |
| `SYS-18`-`SYS-19` | CN | `dc-cn-primary` | `App Zone` middleware | TBD |
| `SYS-20`-`SYS-21` | CN | `dc-cn-primary` | `App Zone` SAP boundary | Third party/TBD |
| `SYS-22`-`SYS-26` | CN | `dc-cn-primary` | `DB Zone` | TBD |
| `SYS-27` | US/NA | `dc-us-identity` | `App Zone` | TBD |
| `SYS-28`-`SYS-30` | US/NA | `dc-us` | `NA-PROD-INA-EARTH` | TBD |
| `SYS-31`-`SYS-40` | US/NA | `dc-us` | `NA-PROD-INA-K8S` | TBD |
| `SYS-41`-`SYS-42` | US/NA | `dc-us` | `NA-PROD-INA-INTEGRATION` | TBD |
| `SYS-43`-`SYS-44` | US/NA | `dc-us` | `NA-PROD-INA-SERVER` | TBD |
| `SYS-45` | US/NA | `dc-us` | `NA-PROD-INA-SAP` | Third party/TBD |
| `SYS-46`-`SYS-49` | US/NA | `dc-us` | `NA-PROD-INA-DB` | TBD |
| `SYS-50`-`SYS-54` | CN | `dc-cn-primary` | `App Zone` peer application boundary | TBD |
| `SYS-55` | US/NA | AWS US, N. Virginia | `Private subnet (APP)` | Third party/TBD |
| `SYS-56`-`SYS-57` | US/NA | Azure US | `APP Zone` | Third party/TBD |
| `SYS-58`-`SYS-60` | US/NA | `dc-us` | `NA-PROD-INA-K8S` | TBD |

No IP addresses or CIDR ranges are required or recorded. City and state values remain intentionally generalized by the project configuration.

## 4. Network Topology
| Connection | Type | Encryption | Notes |
|---|---|---|---|
| CN office network to `dc-cn-primary` ingress | Private enterprise network, exact carrier `TBD` | TLS 1.2+ | Employees enter through `SYS-01`, optional `SYS-02`, and `SYS-03` |
| NA office network to `dc-us` ingress | Private enterprise network, exact carrier `TBD` | TLS 1.2+ | Employees enter through `SYS-28`, optional `SYS-29`, and `SYS-30` |
| `dc-cn-primary` and `dc-us` | Type `TBD` | TLS 1.2+ | CDC is the only order-data synchronization mechanism; direct database replication is prohibited |
| OSP to `dc-us-identity` | Type `TBD` | HTTPS/TLS 1.2+ | SAML authentication through `SYS-27` |
| `dc-us` to AWS US | Internet/private cloud connectivity `TBD` | TLS 1.2+ | HTTPS and Kafka traffic; final route type is `TBD` |
| `dc-us` to Azure US | Internet/private cloud connectivity `TBD` | TLS 1.2+ | HTTPS and messaging; final route type is `TBD` |

## 5. Technical Components
| Component IDs | Type | Language | Framework/Product | Runtime | Sensitivity |
|---|---|---|---|---|---|
| `SYS-01`, `SYS-28` | Load balancer/ingress | N/A | F5 | Appliance/platform, version `TBD` | Company Confidential |
| `SYS-02`, `SYS-29` | Web application firewall, optional | N/A | WAF product `TBD` | Appliance/platform `TBD` | Company Confidential |
| `SYS-03`, `SYS-30` | Edge routing | N/A | Edge router | Network platform `TBD` | Company Confidential |
| `SYS-04`, `SYS-31` | Web frontend | N/A | Nginx, version `TBD` | CN web tier / NA internal K8s platform | Company Confidential |
| `SYS-05`, `SYS-32` | API gateway | Java, version `TBD` | Spring Cloud Gateway, version `TBD` | Internal K8s Platform | Company Confidential |
| `SYS-06`-`SYS-13`, `SYS-33`-`SYS-40` | Backend services | Java, version `TBD` | Spring, version `TBD` | Internal K8s Platform | Company Confidential |
| `SYS-14` | API management | N/A | APIM, version `TBD` | Platform `TBD` | Company Confidential |
| `SYS-15` | API gateway/integration | N/A | WSO2 API Gateway, version `TBD` | Platform `TBD` | Company Confidential |
| `SYS-16`, `SYS-41` | API mediation | N/A | APIH, version `TBD` | Platform `TBD` | Company Confidential |
| `SYS-17`, `SYS-42` | Event messaging | N/A | Kafka, version `TBD` | Platform `TBD` | Company Confidential |
| `SYS-18`, `SYS-43` | CDC messaging | N/A | RabbitMQ, version `TBD` | Platform `TBD` | Company Confidential |
| `SYS-19`, `SYS-44` | CDC connector | `TBD` | Debezium, version `TBD` | Platform `TBD` | Company Confidential |
| `SYS-20`, `SYS-21`, `SYS-45` | ERP function and SLT boundary | N/A | SAP product/version `TBD` | Existing ERP platform | Company Confidential |
| `SYS-22`, `SYS-46` | Search HA group | N/A | Elasticsearch, version `TBD` | HA platform `TBD` | Company Confidential |
| `SYS-23`, `SYS-47` | Cache HA group | N/A | Redis, version `TBD` | HA platform `TBD` | Company Confidential |
| `SYS-24` | Relational database HA group, CN only | N/A | MySQL, version `TBD` | HA platform `TBD` | Company Confidential |
| `SYS-25`, `SYS-48` | Relational database HA group | N/A | PostgreSQL, version `TBD` | HA platform `TBD` | Company Confidential |
| `SYS-26`, `SYS-49` | Relational database HA group | N/A | SQL Server, version `TBD` | HA platform `TBD` | Company Confidential |
| `SYS-27` | Identity provider | N/A | ADFS, version `TBD` | Existing identity platform | Company Confidential |
| `SYS-50`-`SYS-60` | Peer application boundaries | `TBD` | Existing products, versions `TBD` | Existing regional/cloud platforms | Company Confidential |

## 6. Integration Points
| # | From | To | Protocol | Port | Auth Method | Notes |
|---|---|---|---|---|---|---|
| INT-01 | CN employee browser | `SYS-01` -> optional `SYS-02` -> `SYS-03` -> `SYS-04` | HTTPS | 443 | SAML 2.0 session via `SYS-27`; ingress device-to-device auth `TBD` | Internal employee entry |
| INT-02 | NA employee browser | `SYS-28` -> optional `SYS-29` -> `SYS-30` -> `SYS-31` | HTTPS | 443 | SAML 2.0 session via `SYS-27`; ingress device-to-device auth `TBD` | Internal employee entry |
| INT-03 | `SYS-04` | `SYS-05` | HTTPS | 443 | Session token, exact token profile `TBD` | CN web to gateway |
| INT-04 | `SYS-31` | `SYS-32` | HTTPS | 443 | Session token, exact token profile `TBD` | NA web to gateway |
| INT-05 | `SYS-05` | `SYS-06`-`SYS-13` | HTTPS | 443 | Service authentication method `TBD` | CN gateway fan-out |
| INT-06 | `SYS-32` | `SYS-33`-`SYS-40` | HTTPS | 443 | Service authentication method `TBD` | NA gateway fan-out |
| INT-07 | `SYS-06`-`SYS-13` | `SYS-14`-`SYS-16` | HTTPS | 443 | OAuth 2.0 Client Credentials or Basic Auth, endpoint mapping `TBD` | Basic Auth is weak and must be eliminated or formally accepted |
| INT-08 | `SYS-33`-`SYS-40` | `SYS-41` | HTTPS | 443 | OAuth 2.0 Client Credentials or Basic Auth, endpoint mapping `TBD` | `SYS-41` is the only NA cross-application API mediator |
| INT-09 | `SYS-06`-`SYS-13` | `SYS-17` | Kafka over TLS | `TBD` | SASL/SCRAM | CN events |
| INT-10 | `SYS-33`-`SYS-40` | `SYS-42` | Kafka over TLS | `TBD` | SASL/SCRAM | NA events |
| INT-11 | `SYS-06`-`SYS-13` | `SYS-20`/`SYS-21` | RFC over TLS or HTTPS | `TBD`/443 | SAP Logon Ticket | CN ERP function calls; endpoint protocol selection `TBD` |
| INT-12 | `SYS-33`-`SYS-40` | `SYS-45` | RFC over TLS or HTTPS | `TBD`/443 | SAP Logon Ticket | NA ERP function calls; endpoint protocol selection `TBD` |
| INT-13 | `SYS-21` SLT | `SYS-19`/`SYS-18` | RFC over TLS or HTTPS | `TBD`/443 | SAP authentication, exact mechanism `TBD` | CN SLT/CDC boundary |
| INT-14 | `SYS-45` SLT | `SYS-44`/`SYS-43` | RFC over TLS or HTTPS | `TBD`/443 | SAP authentication, exact mechanism `TBD` | NA SLT/CDC boundary |
| INT-15 | `SYS-19` | `SYS-18` | TCP over TLS | `TBD` | User/password from K8s Secrets | CN CDC delivery |
| INT-16 | `SYS-44` | `SYS-43` | TCP over TLS | `TBD` | User/password from K8s Secrets | NA CDC delivery |
| INT-17 | `SYS-18` | `SYS-17` | Kafka over TLS | `TBD` | SASL/SCRAM | CN CDC event publication |
| INT-18 | `SYS-43` | `SYS-42` | Kafka over TLS | `TBD` | SASL/SCRAM | NA CDC event publication |
| INT-19 | `SYS-06`-`SYS-13` | `SYS-22` | HTTPS | 443 | User/password from K8s Secrets | CN search |
| INT-20 | `SYS-06`-`SYS-13` | `SYS-23`-`SYS-26` | TLS/JDBC as applicable | `TBD` | User/password from K8s Secrets | CN persistence access |
| INT-21 | `SYS-33`-`SYS-40` | `SYS-46` | HTTPS | 443 | User/password from K8s Secrets | NA search |
| INT-22 | `SYS-33`-`SYS-40` | `SYS-47`-`SYS-49` | TLS/JDBC as applicable | `TBD` | User/password from K8s Secrets | NA persistence access |
| INT-23 | `SYS-04`/`SYS-31` | `SYS-27` | HTTPS/SAML 2.0 | 443 | SAML 2.0 | Employee SSO |
| INT-24 | CN OSP through `SYS-14`-`SYS-17` | `SYS-50`-`SYS-54` | HTTPS or Kafka over TLS | 443/`TBD` | OAuth 2.0 Client Credentials or SASL/SCRAM | Per-peer protocol mapping `TBD` |
| INT-25 | NA OSP through `SYS-41`/`SYS-42` | `SYS-55`-`SYS-60` | HTTPS or Kafka over TLS | 443/`TBD` | OAuth 2.0 Client Credentials or SASL/SCRAM | Per-peer protocol mapping `TBD`; cross-app calls must traverse integration zone |

## 7. User Authentication
| Entry Point | User Roles | Auth Server | Protocol | Authorization |
|---|---|---|---|---|
| `SYS-04` CN web | Internal employees; detailed roles `TBD` | `SYS-27` (ADFS) | SAML 2.0 over HTTPS | RBAC through AuthZ Platform; role matrix `TBD` |
| `SYS-31` NA web | Internal employees; detailed roles `TBD` | `SYS-27` (ADFS) | SAML 2.0 over HTTPS | RBAC through AuthZ Platform; role matrix `TBD` |

## 8. Credential and Key Protection
| Environment | Solution | Notes |
|---|---|---|
| CN private DC | K8s Secrets | No hardcoded credentials; encryption-at-rest configuration, external secret integration, rotation interval, and ownership are `TBD` |
| NA private DC | K8s Secrets | No hardcoded credentials; encryption-at-rest configuration, external secret integration, rotation interval, and ownership are `TBD` |
| Existing appliances, databases, ERP, and cloud peers | `TBD` | Credential vault and rotation controls require confirmation |

## 9. Data Encryption
| Component | At Rest | In Transit | Cross-Border | Compliance |
|---|---|---|---|---|
| `SYS-22`-`SYS-26` CN persistence | Method `TBD` | TLS 1.2+ | No direct database replication | PRC residency/control basis `TBD` |
| `SYS-46`-`SYS-49` NA persistence | Method `TBD` | TLS 1.2+ | No direct database replication | US privacy/control basis `TBD` |
| `SYS-17`-`SYS-19`, `SYS-42`-`SYS-44` CDC/event pipeline | Method `TBD` | TLS 1.2+ | Yes, where order events synchronize CN and NA | Dataset classification, minimization, and legal basis `TBD` |
| All application and integration components | Platform method `TBD` | TLS 1.2+ | Depends on flow | Applicable retention and privacy controls `TBD` |

## 10. Open Items / TBDs
| ID | Item | Owner | Target Date | Blocking Design |
|---|---|---|---|---|
| TBD-01 | Decide whether `SYS-02` and `SYS-29` are enabled | Security owner `TBD` | TBD | No; model as optional |
| TBD-02 | Define cross-region failover RTO and RPO | Program owner `TBD` | TBD | No for baseline design; required before production approval |
| TBD-03 | Confirm the physical carrier/connection types among CN, NA, identity, AWS, and Azure | Network owner `TBD` | TBD | No; do not infer network products |
| TBD-04 | Confirm Java, Spring, Nginx, platform, database, and middleware versions | Application/platform owners `TBD` | TBD | No |
| TBD-05 | Confirm non-HTTPS ports and per-endpoint RFC/HTTPS selections | Application/network owners `TBD` | TBD | No; labels remain `TBD` |
| TBD-06 | Replace or formally accept Basic Auth and define every endpoint's exact service-auth profile | Security/application owners `TBD` | TBD | No for topology; required before production approval |
| TBD-07 | Confirm K8s Secrets encryption at rest, vault integration, rotation, and ownership | Platform/security owners `TBD` | TBD | No for topology; required before production approval |
| TBD-08 | Confirm encryption-at-rest methods for all persisted data | Data/security owners `TBD` | TBD | No for topology; required before production approval |
| TBD-09 | Confirm cross-border dataset, minimization, residency, and legal basis | Privacy/data owners `TBD` | TBD | No for topology; required before production approval |
| TBD-10 | Confirm department, infrastructure owners, user role matrix, go-live date, capacity, availability targets, backup, monitoring, and DR operations | Program owner `TBD` | TBD | No for baseline design |

## 11. Architecture Constraints
- Preserve active-active deployment in `dc-cn-primary` and `dc-us`; each region serves its local employee population.
- Preserve all `SYS-01` through `SYS-60` identifiers and the regional placements stated in Section 3.
- Use `NA-PROD-INA-K8S`, `NA-PROD-INA-INTEGRATION`, `NA-PROD-INA-SAP`, `NA-PROD-INA-SERVER`, and `NA-PROD-INA-DB` exactly as configured. `NA-PROD-INA-EARTH` is retained from the indexed diagram for NA ingress/network placement.
- Only `SYS-41` and `SYS-42` in `NA-PROD-INA-INTEGRATION` may mediate NA cross-application API and event flows.
- Isolate `SYS-45` in `NA-PROD-INA-SAP`; isolate `SYS-43`/`SYS-44` in `NA-PROD-INA-SERVER`; isolate `SYS-46`-`SYS-49` in `NA-PROD-INA-DB`.
- Permit database-zone access only from the corresponding regional OSP backend services.
- Use CDC through `SYS-19`/`SYS-44`, `SYS-18`/`SYS-43`, and `SYS-17`/`SYS-42` for order-data synchronization. Do not introduce direct cross-region database replication or IDOC.
- Encrypt every data path with TLS 1.2 or later. Do not hardcode credentials.
- Do not place IP addresses or CIDR ranges in requirements or generated architecture artifacts.

## 12. Requirements Gate Assessment
No critical requirements gap blocks architecture design: every component has a physical DC/cloud region and zone, external-facing employee access uses SAML 2.0 through `SYS-27`, cloud/service integrations have stated authentication families, no hardcoded credentials are permitted, and no source states a known residency violation. The open items above remain explicit `TBD`s and must be resolved at the indicated lifecycle point.

## 13. System Traceability Inventory
| ID | English Role | Location / Zone |
|---|---|---|
| `SYS-01` | CN ingress load balancer | `dc-cn-primary` / `Intranet` |
| `SYS-02` | CN optional web application firewall | `dc-cn-primary` / `Intranet` |
| `SYS-03` | CN edge router | `dc-cn-primary` / `Intranet` |
| `SYS-04` | CN OSP web tier | `dc-cn-primary` / `Intranet` |
| `SYS-05` | CN application gateway | `dc-cn-primary` / `App Zone` |
| `SYS-06` | CN order creation service | `dc-cn-primary` / `App Zone` |
| `SYS-07` | CN order change service | `dc-cn-primary` / `App Zone` |
| `SYS-08` | CN data distribution service | `dc-cn-primary` / `App Zone` |
| `SYS-09` | CN master data service | `dc-cn-primary` / `App Zone` |
| `SYS-10` | CN order inquiry service | `dc-cn-primary` / `App Zone` |
| `SYS-11` | CN basic operation service | `dc-cn-primary` / `App Zone` |
| `SYS-12` | CN logging service | `dc-cn-primary` / `App Zone` |
| `SYS-13` | CN additional backend service | `dc-cn-primary` / `App Zone` |
| `SYS-14` | CN API management platform | `dc-cn-primary` / `App Zone` |
| `SYS-15` | CN API gateway platform | `dc-cn-primary` / `App Zone` |
| `SYS-16` | CN API mediation platform | `dc-cn-primary` / `App Zone` |
| `SYS-17` | CN event messaging platform | `dc-cn-primary` / `App Zone` |
| `SYS-18` | CN CDC messaging platform | `dc-cn-primary` / `App Zone` |
| `SYS-19` | CN CDC connector | `dc-cn-primary` / `App Zone` |
| `SYS-20` | CN ERP ECC boundary | `dc-cn-primary` / `App Zone` |
| `SYS-21` | CN ERP S4 boundary | `dc-cn-primary` / `App Zone` |
| `SYS-22` | CN search HA group | `dc-cn-primary` / `DB Zone` |
| `SYS-23` | CN cache HA group | `dc-cn-primary` / `DB Zone` |
| `SYS-24` | CN MySQL HA group | `dc-cn-primary` / `DB Zone` |
| `SYS-25` | CN PostgreSQL HA group | `dc-cn-primary` / `DB Zone` |
| `SYS-26` | CN SQL Server HA group | `dc-cn-primary` / `DB Zone` |
| `SYS-27` | Employee identity service | `dc-us-identity` / `App Zone` |
| `SYS-28` | NA ingress load balancer | `dc-us` / `NA-PROD-INA-EARTH` |
| `SYS-29` | NA optional web application firewall | `dc-us` / `NA-PROD-INA-EARTH` |
| `SYS-30` | NA edge router | `dc-us` / `NA-PROD-INA-EARTH` |
| `SYS-31` | NA OSP web tier | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-32` | NA application gateway | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-33` | NA order creation service | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-34` | NA order change service | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-35` | NA data distribution service | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-36` | NA master data service | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-37` | NA order inquiry service | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-38` | NA basic operation service | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-39` | NA logging service | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-40` | NA additional backend service | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-41` | NA API mediation platform | `dc-us` / `NA-PROD-INA-INTEGRATION` |
| `SYS-42` | NA event messaging platform | `dc-us` / `NA-PROD-INA-INTEGRATION` |
| `SYS-43` | NA CDC messaging platform | `dc-us` / `NA-PROD-INA-SERVER` |
| `SYS-44` | NA CDC connector | `dc-us` / `NA-PROD-INA-SERVER` |
| `SYS-45` | NA ERP S4 boundary | `dc-us` / `NA-PROD-INA-SAP` |
| `SYS-46` | NA search HA group | `dc-us` / `NA-PROD-INA-DB` |
| `SYS-47` | NA cache HA group | `dc-us` / `NA-PROD-INA-DB` |
| `SYS-48` | NA PostgreSQL HA group | `dc-us` / `NA-PROD-INA-DB` |
| `SYS-49` | NA SQL Server HA group | `dc-us` / `NA-PROD-INA-DB` |
| `SYS-50` | CN commerce order peer | `dc-cn-primary` / `App Zone` |
| `SYS-51` | CN sales order peer | `dc-cn-primary` / `App Zone` |
| `SYS-52` | CN customer fulfillment peer | `dc-cn-primary` / `App Zone` |
| `SYS-53` | AP customer fulfillment peer | `dc-cn-primary` / `App Zone` |
| `SYS-54` | AP supply-chain service peer | `dc-cn-primary` / `App Zone` |
| `SYS-55` | AWS US sales order peer | AWS US East N. Virginia / `Private subnet (APP)` |
| `SYS-56` | Azure US commerce peer | Azure US / `APP Zone` |
| `SYS-57` | Azure US enterprise SaaS peer | Azure US / `APP Zone` |
| `SYS-58` | NA ERP service peer | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-59` | NA logistics gateway peer | `dc-us` / `NA-PROD-INA-K8S` |
| `SYS-60` | NA install-base service peer | `dc-us` / `NA-PROD-INA-K8S` |
