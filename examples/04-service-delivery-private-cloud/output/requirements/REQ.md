# Requirements Document - Service Delivery Platform (SSOC), NA Migration
**Version**: 1.0 Draft | **Date**: 2026-09-14 | **Author**: ArchHarness
**Project ID**: SSOC-NA-001 | **Classification**: Acme Confidential
**Scope**: E2E modification. SSOC is the modified platform; connected enterprise, SaaS, identity, and partner systems are existing black boxes whose integration boundaries are in scope.

## 1. Project Overview

SSOC is the service supply-chain operations platform, comprising approximately 40 Java and Spring Cloud microservices. The program extends the existing platform to serve North America while retaining the primary deployment in the CN primary data center and integrating four private data centers, Azure-hosted satellite systems, SAP, and external logistics partners.

All names below are the stable document names defined by `input/systems-registry.md`. The corresponding `SYS-nn` identifiers remain authoritative.

## 2. Applications in Scope

| App | Type | New/Existing | Owner | Scope |
|-----|------|--------------|-------|-------|
| SYS-01 F5; SYS-02 Service-Supply-Chain-dmz-nginx-proxy; SYS-03 Service-Supply-Chain-gateway; SYS-04 Service-Supply-Chain-web | SSOC ingress and DMZ tier | Modified | InfraSec / TBD business owner | Full deployment and integration boundary |
| SYS-05 WSO2; SYS-06 Kafka (primary); SYS-07 Service-Supply-Chain-int-nginx-proxy; SYS-08 Service-Supply-Chain-main; SYS-09 Service-Supply-Chain-websocket; SYS-10 Service-Supply-Chain-* group (10 services); SYS-11 Service-Supply-Chain-* group (22 services) | SSOC integration and application tier | Modified | InfraSec / TBD business owner | Full deployment and integration boundary |
| SYS-12 MySQL TMS; SYS-13 MySQL Main; SYS-14 MySQL WMS; SYS-15 MySQL MDS; SYS-16 MySQL OMS; SYS-17 Redis HA; SYS-18 RabbitMQ HA; SYS-19 Elasticsearch HA | SSOC persistence tier | Modified | InfraSec / TBD business owner | Full deployment and integration boundary |
| SYS-20 S4; SYS-21 SECC; SYS-22 LSCRM; SYS-23 CECC; SYS-24 S3 | SAP landscape | Existing | TBD | Black-box boundary only |
| SYS-25 Account-Service; SYS-26 Service-customer-master-data; SYS-27 Serice-Data-serviceE; SYS-28 Price-master-ROW | US satellite applications | Existing | TBD | Black-box boundary only |
| SYS-29 ADFS; SYS-30 Enterprise ID | Identity services | Existing | InfraSec / TBD | Authentication boundary only |
| SYS-31 Reverse-Management-System; SYS-32 procurement-service; SYS-33 lakehouse; SYS-34 Kafka (secondary); SYS-35 support-hub | CN secondary systems | Existing | TBD | Black-box boundary only |
| SYS-36 support-portal; SYS-37 support-gateway | CN support systems | Existing | TBD | Black-box boundary only |
| SYS-38 analytics-a; SYS-39 analytics-b; SYS-40 analytics-c; SYS-41 edge-cache | Azure satellite systems | Existing | TBD | Black-box boundary only |
| SYS-42 logistics partner A; SYS-43 logstics-vendor-1; SYS-44 logistics partner B; SYS-45 logistics partner C; SYS-46 logistics partner D; SYS-47 logistics partner E | External 3PL systems | Existing third party | Respective partners | Black-box boundary only |
| SYS-48 file partner A; SYS-49 file partner B; SYS-50 file partner C | External file-transfer partners | Existing third party | Respective partners | Black-box boundary only |
| SYS-51 MFT platform | Managed file transfer | Modified integration platform | InfraSec | Integration boundary |
| SYS-52 Edge router | Network ingress | Modified network component | InfraSec | Network boundary |

## 3. Physical Deployment

| App/Component | Country/Region | DC / Cloud Region | Zone/Subnet | Owner |
|---------------|----------------|-------------------|-------------|-------|
| SYS-01, SYS-52 | CN / APAC-CN | CN Primary DC, City A | Ingress edge | InfraSec |
| SYS-02, SYS-03, SYS-04 | CN / APAC-CN | CN Primary DC, City A | DMZ, Internal K8s | InfraSec |
| SYS-05, SYS-06, SYS-07, SYS-08, SYS-09, SYS-10, SYS-11, SYS-51 | CN / APAC-CN | CN Primary DC, City A | Intranet; SYS-07 through SYS-11 on Internal K8s | InfraSec |
| SYS-12, SYS-13, SYS-14, SYS-15, SYS-16, SYS-17, SYS-18, SYS-19 | CN / APAC-CN | CN Primary DC, City A | DB Zone | InfraSec |
| SYS-20, SYS-21, SYS-22, SYS-23, SYS-24 | TBD | SAP landscape, exact hosting location TBD | TBD | TBD |
| SYS-25, SYS-26, SYS-27, SYS-28, SYS-29, SYS-30 | US / NA | US DC, City C | App Zone or Intranet; per-system allocation TBD | InfraSec / TBD app owners |
| SYS-31, SYS-32, SYS-33, SYS-34, SYS-35 | CN / APAC-CN | CN Secondary DC, City B | Intranet | InfraSec / TBD app owners |
| SYS-36, SYS-37 | CN / APAC-CN | Support DC, City F | App Zone | InfraSec / TBD app owners |
| SYS-38, SYS-39, SYS-40, SYS-41 | US / NA | Azure, exact region TBD | SaaS apps; exact network placement TBD | Third party / TBD |
| SYS-42 through SYS-47 | External / TBD | Partner hosted | Internet 3PL boundary | Respective partners |
| SYS-48 through SYS-50 | External / TBD | Partner hosted | Internet file-transfer boundary | Respective partners |

## 4. Network Topology

| Connection | Type | Encryption | Notes |
|------------|------|------------|-------|
| External users and partners to CN Primary DC | Internet | TLS 1.2 or later | Traffic terminates at SYS-01 in the DMZ; no direct Intranet access |
| CN Primary DC to US DC | VPN/MPLS | VPN encryption method TBD; MPLS encryption TBD | Cross-application API calls are mediated by SYS-05 |
| CN Primary DC to CN Secondary DC | VPN/MPLS | Encryption method TBD | HTTPS traffic uses OAuth2; events use SASL/SCRAM |
| CN Primary DC to Support DC | VPN/MPLS | Encryption method TBD | HTTPS with OAuth2 |
| CN Primary DC to Azure satellites | Internet or private connectivity TBD | TLS 1.2 or later for HTTPS; event transport encryption TBD | Exact Azure region and connectivity type are TBD |
| CN Primary DC to SAP landscape | Private connectivity type TBD | TLS protection for RFC is TBD; HTTPS uses TLS 1.2 or later | SAP is not exposed to the DMZ |
| CN Primary DC to external file partners | Internet | SFTP/SSH | Managed through SYS-51; detailed routing is TBD |

## 5. Technical Components (New/Modified Only)

| Component | Type | Language | Framework | Runtime | Sensitivity |
|-----------|------|----------|-----------|---------|-------------|
| SYS-01 F5 | Load balancer / ingress | N/A | F5 | Private DC appliance | Acme Confidential |
| SYS-52 Edge router | Network router | N/A | TBD | Private DC network platform | Acme Confidential |
| SYS-02 Service-Supply-Chain-dmz-nginx-proxy | Reverse proxy | N/A | Nginx, version TBD | Internal K8s, DMZ | Acme Confidential |
| SYS-03 Service-Supply-Chain-gateway | Backend API gateway service | Java, version TBD | Spring Cloud, version TBD | Internal K8s, DMZ | Acme Confidential |
| SYS-04 Service-Supply-Chain-web | Web frontend | Java, version TBD | Spring Cloud, version TBD | Internal K8s, DMZ | Acme Confidential |
| SYS-05 WSO2 | API integration platform | TBD | WSO2 API Gateway, version TBD | Private DC, Intranet | Acme Confidential |
| SYS-06 Kafka (primary) | Message bus | TBD | Kafka, version TBD | Private DC, Intranet | Acme Confidential |
| SYS-07 Service-Supply-Chain-int-nginx-proxy | Reverse proxy | N/A | Nginx, version TBD | Internal K8s, Intranet | Acme Confidential |
| SYS-08 Service-Supply-Chain-main | Backend service | Java, version TBD | Spring Cloud, version TBD | Internal K8s, Intranet | Acme Confidential |
| SYS-09 Service-Supply-Chain-websocket | WebSocket backend | Java, version TBD | Spring Cloud, version TBD | Internal K8s, Intranet | Acme Confidential |
| SYS-10 Service-Supply-Chain-* group (10 services) | Backend service group | Java, version TBD | Spring Cloud, version TBD | Internal K8s, Intranet | Acme Confidential |
| SYS-11 Service-Supply-Chain-* group (22 services) | Backend service group | Java, version TBD | Spring Cloud, version TBD | Internal K8s, Intranet | Acme Confidential |
| SYS-12 through SYS-16 MySQL HA groups | Relational databases | N/A | MySQL, version TBD | Private DC HA, each 1 primary and 2 replicas | Acme Confidential |
| SYS-17 Redis HA | Cache | N/A | Redis, version TBD | Private DC HA, 3 primary and 3 replica nodes | Acme Confidential |
| SYS-18 RabbitMQ HA | Message queue | N/A | RabbitMQ, version TBD | Private DC HA, 3 replicas | Acme Confidential |
| SYS-19 Elasticsearch HA | Search datastore | N/A | Elasticsearch, version TBD | Private DC HA, 3 nodes | Acme Confidential |
| SYS-51 MFT platform | Managed file transfer | TBD | MFT platform, version TBD | Private DC, Intranet | Acme Confidential |

SYS-10 members are `rms`, `tms`, `oms`, `wms`, `mds`, `ips`, `autopilot`, `ves`, `cfs`, and `scs`. SYS-11 members are `wms`, `oms`, `pps`, `eta`, `scs`, `auth`, `pbs`, `rns`, `vrs`, `ibs`, `cfs`, `lvr`, `tms`, `pms`, `mds`, `rms`, `ws-stock`, `rms-xdoc`, `data`, `sys`, and `wms-xdoc`; the source states 22 services but lists 21 names, so reconciliation is TBD.

## 6. Integration Points

| # | From | To | Protocol | Port | Auth Method | Notes |
|---|------|----|----------|------|-------------|-------|
| INT-001 | External client | SYS-01 F5 | HTTPS | 443 | OAuth2, flow TBD | TLS termination at ingress |
| INT-002 | SYS-01 F5 | SYS-02 Service-Supply-Chain-dmz-nginx-proxy | HTTPS | 443 | TBD | Internal ingress authentication is not specified |
| INT-003 | SYS-04 Service-Supply-Chain-web | SYS-03 Service-Supply-Chain-gateway | HTTPS | 443 | OAuth2 | DMZ flow |
| INT-004 | SYS-03 Service-Supply-Chain-gateway | SYS-05 WSO2 | HTTPS | 443 | Basic Auth | Weak mechanism; migration and rotation controls TBD |
| INT-005 | SYS-05 WSO2 | SYS-10 and SYS-11 service groups | HTTPS | 443 | Basic Auth | All cross-application calls must be mediated |
| INT-006 | SYS-07 through SYS-11 | SYS-06 Kafka (primary) | TCP | 9093 | SASL/SCRAM | Transport encryption configuration TBD |
| INT-007 | SYS-07 through SYS-11 | SYS-12 through SYS-16 | JDBC over TCP | 3306 | User/password from K8s Secrets | DB Zone permits Intranet services only |
| INT-008 | SYS-07 through SYS-11 | SYS-17 Redis HA | TCP | 6379 | Basic Auth | TLS configuration and stronger auth TBD |
| INT-009 | SYS-07 through SYS-11 | SYS-19 Elasticsearch HA | HTTPS | 19200 | Basic Auth | TLS 1.2 or later |
| INT-010 | SYS-07 through SYS-11 | SYS-18 RabbitMQ HA | TCP | 5672 | Basic Auth | TLS configuration and stronger auth TBD |
| INT-011 | SYS-07 through SYS-11 | SYS-20 S4 | TCP/RFC | 33xx | SAP Logon Ticket | Exact port and RFC transport protection TBD |
| INT-012 | SYS-20 S4 | SYS-21 SECC | TCP/RFC | 33xx | SAP Logon Ticket, confirmation TBD | Exact port TBD |
| INT-013 | SYS-20 S4 | SYS-22 LSCRM | TCP/RFC | 33xx | SAP Logon Ticket, confirmation TBD | Exact port TBD |
| INT-014 | SYS-20 S4 | SYS-23 CECC | TCP/RFC | 33xx | SAP Logon Ticket, confirmation TBD | Exact port TBD |
| INT-015 | SYS-07 through SYS-11 | SYS-24 S3 | HTTPS | 443 | Basic Auth | Object-storage credential rotation TBD |
| INT-016 | SYS-05 WSO2 | SYS-25 Account-Service | HTTPS | 443 | Basic Auth | CN Primary to US DC mediated API |
| INT-017 | SYS-05 WSO2 | SYS-26 Service-customer-master-data | HTTPS | 443 | Basic Auth | CN Primary to US DC mediated API |
| INT-018 | SYS-05 WSO2 | SYS-27 Serice-Data-serviceE | HTTPS | 443 | Basic Auth | CN Primary to US DC mediated API |
| INT-019 | SYS-05 WSO2 | SYS-28 Price-master-ROW | HTTPS | 443 | Basic Auth | CN Primary to US DC mediated API |
| INT-020 | SYS-05 WSO2 | SYS-31 Reverse-Management-System | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-021 | SYS-05 WSO2 | SYS-32 procurement-service | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-022 | SYS-05 WSO2 | SYS-33 lakehouse | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-023 | SYS-06 Kafka (primary) | SYS-34 Kafka (secondary) | TCP | 9093 | SASL/SCRAM | Direction and TLS configuration TBD |
| INT-024 | SYS-05 WSO2 | SYS-35 support-hub | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-025 | SYS-05 WSO2 | SYS-36 support-portal | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-026 | SYS-05 WSO2 | SYS-37 support-gateway | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-027 | SYS-05 WSO2 | SYS-38 analytics-a | HTTPS | 443 | OAuth2 | Exact Azure endpoint and OAuth2 flow TBD |
| INT-028 | SYS-05 WSO2 | SYS-39 analytics-b | HTTPS | 443 | OAuth2 | Exact Azure endpoint and OAuth2 flow TBD |
| INT-029 | SYS-05 WSO2 | SYS-40 analytics-c | HTTPS | 443 | OAuth2 | Exact Azure endpoint and OAuth2 flow TBD |
| INT-030 | SYS-06 Kafka (primary) | SYS-41 edge-cache | TCP | 9093 | SASL/SCRAM | Direction and TLS configuration TBD |
| INT-031 | SYS-05 WSO2 | SYS-42 logistics partner A | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-032 | SYS-05 WSO2 | SYS-43 logstics-vendor-1 | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-033 | SYS-05 WSO2 | SYS-44 logistics partner B | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-034 | SYS-05 WSO2 | SYS-45 logistics partner C | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-035 | SYS-05 WSO2 | SYS-46 logistics partner D | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-036 | SYS-05 WSO2 | SYS-47 logistics partner E | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-037 | SYS-51 MFT platform | SYS-48 file partner A | SFTP | 22 | SSH key | Partner file flow; key rotation TBD |
| INT-038 | SYS-51 MFT platform | SYS-49 file partner B | SFTP | 22 | SSH key | Partner file flow; key rotation TBD |
| INT-039 | SYS-51 MFT platform | SYS-50 file partner C | SFTP | 22 | SSH key | Partner file flow; key rotation TBD |
| INT-040 | SYS-04 Service-Supply-Chain-web | SYS-29 ADFS | SAML 2.0 over HTTPS | 443 | SAML assertion | Internal employees and BU users |
| INT-041 | External portals, exact component TBD | SYS-30 Enterprise ID | OIDC/OAuth2 over HTTPS | 443 | OAuth2 Authorization Code / OIDC, confirmation TBD | Partners and carriers |

## 7. User Authentication

| Entry Point | User Roles | Auth Server | Protocol | Authorization |
|-------------|------------|-------------|----------|---------------|
| SYS-04 Service-Supply-Chain-web | Internal operations; BU users | SYS-29 ADFS | SAML 2.0 | Central AuthZ Platform, RBAC |
| External portals, exact component TBD | Partners; carriers | SYS-30 Enterprise ID | OAuth2/OIDC, exact flow TBD | Central AuthZ Platform, RBAC |

## 8. Credential and Key Protection

| Environment | Solution | Notes |
|-------------|----------|-------|
| Private DC Internal K8s | Kubernetes Secrets | Encryption at rest, external secret integration, access policy, and rotation schedule are TBD; hardcoded credentials are prohibited |
| Private DC non-K8s platforms | TBD enterprise secret store | Applies to SYS-01, SYS-05, SYS-06, SYS-12 through SYS-19, SYS-51, and SYS-52 |
| Azure | TBD | Secret-storage ownership and controls for SYS-38 through SYS-41 are not supplied |
| Partner SFTP | SSH keys managed by SYS-51, detailed vault TBD | Rotation schedule and partner key lifecycle are TBD |

## 9. Data Encryption

| Component | At Rest | In Transit | Cross-Border | Compliance |
|-----------|---------|------------|--------------|------------|
| SYS-12 through SYS-16 MySQL HA | TBD | TLS 1.2 or later required; JDBC TLS configuration TBD | Potential CN-US flow; data fields TBD | Classification policy; cross-border basis TBD |
| SYS-17 Redis HA | TBD | TLS 1.2 or later required; configuration TBD | Potential CN-US flow; data fields TBD | Classification policy; cross-border basis TBD |
| SYS-18 RabbitMQ HA | TBD | TLS 1.2 or later required; configuration TBD | Potential CN-US flow; event fields TBD | Classification policy; cross-border basis TBD |
| SYS-19 Elasticsearch HA | TBD | TLS 1.2 or later | Potential CN-US flow; indexed fields TBD | Classification policy; cross-border basis TBD |
| SYS-06 and SYS-34 Kafka | TBD | TLS 1.2 or later required; configuration TBD | Yes, if events cross CN-US; event fields TBD | Cross-border basis TBD |
| SYS-51 managed files | TBD | SFTP/SSH | Yes where partner location is outside CN; file contents TBD | Cross-border basis TBD |

## 10. Open Items / TBDs

| ID | Item | Owner | Target Date |
|----|------|-------|-------------|
| TBD-001 | Confirm NA cut-over sequence for SYS-11 group | Program | TBD |
| TBD-002 | Confirm SYS-51 to SYS-06 replacement roadmap | Integration owner | TBD |
| TBD-003 | Reconcile SYS-11 stated count of 22 with the 21 supplied member names | Application owner | TBD |
| TBD-004 | Define authentication between SYS-01 and SYS-02 | Security / platform owner | TBD |
| TBD-005 | Select HTTPS or TCP/EDI per SYS-42 through SYS-47 and define EDI authentication | Integration / partner owners | TBD |
| TBD-006 | Confirm exact SAP hosting location, RFC ports, authentication, and transport encryption | SAP owner | TBD |
| TBD-007 | Confirm Azure region, network placement, and connectivity type | Cloud owner | TBD |
| TBD-008 | Confirm encryption for every VPN/MPLS path and all non-HTTPS protocols | InfraSec | TBD |
| TBD-009 | Define non-K8s secret stores and credential/key rotation controls | InfraSec | TBD |
| TBD-010 | Confirm at-rest encryption methods for databases, caches, queues, indexes, events, and managed files | Data / platform owners | TBD |
| TBD-011 | Identify cross-border data elements and establish the applicable transfer compliance basis | Privacy / legal | TBD |
| TBD-012 | Confirm business owner, department, and target go-live date | Program | TBD |
| TBD-013 | Replace or formally risk-accept Basic Auth integrations | Security / integration owner | TBD |

## 11. Architecture Constraints

- Private cloud is mandatory for the SSOC platform; Azure systems are existing satellites only.
- The primary SSOC deployment remains in the CN Primary DC using separate DMZ, Intranet, and DB zones.
- All cross-application API traffic must traverse SYS-05 WSO2; event traffic must traverse SYS-06 Kafka. Direct application-to-application connections are prohibited.
- Managed partner file transfer must traverse SYS-51 MFT platform.
- SAP SYS-20 through SYS-23 may be reached only by RFC from the Intranet zone and must not be exposed to the DMZ.
- The DB Zone is reachable only from SSOC Intranet services, and each persistence service uses the stated HA topology.
- External 3PL and file-transfer traffic must terminate at SYS-01 in the DMZ and must never connect directly to the Intranet.
- TLS 1.2 or later is required for all applicable traffic. Equivalent encrypted transport must be defined for non-TLS protocols.
- Credentials must not be hardcoded. Workload database credentials are stored in Kubernetes Secrets.
- No IP addresses or CIDR ranges are specified by the approved sources; architecture outputs must use named zones and locations until network allocations are approved.
