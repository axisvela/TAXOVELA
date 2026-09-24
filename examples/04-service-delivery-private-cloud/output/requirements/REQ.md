# Requirements Document - Service Delivery Platform (SDP), NA Migration
**Version**: 1.0 Draft | **Date**: 2026-09-14 | **Author**: ArchHarness
**Project ID**: SDP-NA-001 | **Classification**: Acme Confidential
**Scope**: E2E modification. SDP is the modified platform; connected enterprise, SaaS, identity, and partner systems are existing black boxes whose integration boundaries are in scope.

## 1. Project Overview

SDP is the service supply-chain operations platform, comprising approximately 40 Java and Spring Cloud microservices. The program extends the existing platform to serve North America while retaining the primary deployment in the CN primary data center and integrating four private data centers, Azure-hosted satellite systems, SAP, and external logistics partners.

All names below are the stable document names defined by `input/systems-registry.md`. The corresponding `SYS-nn` identifiers remain authoritative.

## 2. Applications in Scope

| App | Type | New/Existing | Owner | Scope |
|-----|------|--------------|-------|-------|
| INF-04 F5; CMP-01 Service-Supply-Chain-dmz-nginx-proxy; CMP-02 Service-Supply-Chain-gateway; CMP-03 Service-Supply-Chain-web | SDP ingress and DMZ tier | Modified | InfraSec / TBD business owner | Full deployment and integration boundary |
| CMP-04 WSO2; CMP-05 Kafka (primary); CMP-06 Service-Supply-Chain-int-nginx-proxy; CMP-07 Service-Supply-Chain-main; CMP-08 Service-Supply-Chain-websocket; CMP-09 Service-Supply-Chain-* group (10 services); CMP-10 Service-Supply-Chain-* group (22 services) | SDP integration and application tier | Modified | InfraSec / TBD business owner | Full deployment and integration boundary |
| CMP-12 MySQL TMS; CMP-13 MySQL Main; CMP-14 MySQL WMS; CMP-15 MySQL MDS; CMP-16 MySQL OMS; CMP-17 Redis HA; CMP-18 RabbitMQ HA; CMP-19 Elasticsearch HA | SDP persistence tier | Modified | InfraSec / TBD business owner | Full deployment and integration boundary |
| CMP-31 S4; CMP-32 SECC; CMP-33 LSCRM; CMP-34 CECC; CMP-35 S3 | SAP landscape | Existing | TBD | Black-box boundary only |
| CMP-20 Account-Service; CMP-21 Service-customer-master-data; CMP-22 Serice-Data-serviceE; CMP-23 Price-master-ROW | US satellite applications | Existing | TBD | Black-box boundary only |
| INF-09 ADFS; INF-10 Enterprise ID | Identity services | Existing | InfraSec / TBD | Authentication boundary only |
| CMP-24 Reverse-Management-System; CMP-25 procurement-service; CMP-26 lakehouse; CMP-27 Kafka (secondary); CMP-28 support-hub | CN secondary systems | Existing | TBD | Black-box boundary only |
| CMP-29 support-portal; CMP-30 support-gateway | CN support systems | Existing | TBD | Black-box boundary only |
| CMP-36 d365-service-delivery-bu1; CMP-37 d365-service-delivery-bu2; CMP-38 d365-service-delivery-bu3; CMP-39 edge-cache | Azure satellite systems | Existing | TBD | Black-box boundary only |
| CMP-40 logistics partner A; CMP-41 logstics-vendor-1; CMP-42 logistics partner B; CMP-43 logistics partner C; CMP-44 logistics partner D; CMP-45 logistics partner E | External 3PL systems | Existing third party | Respective partners | Black-box boundary only |
| CMP-46 file partner A; CMP-47 file partner B; CMP-48 file partner C | External file-transfer partners | Existing third party | Respective partners | Black-box boundary only |
| CMP-11 MFT platform | Managed file transfer | Modified integration platform | InfraSec | Integration boundary |
| INF-03 Edge router | Network ingress | Modified network component | InfraSec | Network boundary |

## 3. Physical Deployment

| App/Component | Country/Region | DC / Cloud Region | Zone/Subnet | Owner |
|---------------|----------------|-------------------|-------------|-------|
| INF-04, INF-03 | CN / APAC-CN | CN Primary DC, City A | Ingress edge | InfraSec |
| CMP-01, CMP-02, CMP-03 | CN / APAC-CN | CN Primary DC, City A | DMZ, Internal K8s | InfraSec |
| CMP-04, CMP-05, CMP-06, CMP-07, CMP-08, CMP-09, CMP-10, CMP-11 | CN / APAC-CN | CN Primary DC, City A | Intranet; CMP-06 through CMP-10 on Internal K8s | InfraSec |
| CMP-12, CMP-13, CMP-14, CMP-15, CMP-16, CMP-17, CMP-18, CMP-19 | CN / APAC-CN | CN Primary DC, City A | DB Zone | InfraSec |
| CMP-31, CMP-32, CMP-33, CMP-34, CMP-35 | TBD | SAP landscape, exact hosting location TBD | TBD | TBD |
| CMP-20, CMP-21, CMP-22, CMP-23, INF-09, INF-10 | US / NA | US DC, City C | App Zone or Intranet; per-system allocation TBD | InfraSec / TBD app owners |
| CMP-24, CMP-25, CMP-26, CMP-27, CMP-28 | CN / APAC-CN | CN Secondary DC, City B | Intranet | InfraSec / TBD app owners |
| CMP-29, CMP-30 | CN / APAC-CN | Support DC, City F | App Zone | InfraSec / TBD app owners |
| CMP-36, CMP-37, CMP-38, CMP-39 | US / NA | Azure, exact region TBD | SaaS apps; exact network placement TBD | Third party / TBD |
| CMP-40 through CMP-45 | External / TBD | Partner hosted | Internet 3PL boundary | Respective partners |
| CMP-46 through CMP-48 | External / TBD | Partner hosted | Internet file-transfer boundary | Respective partners |

## 4. Network Topology

| Connection | Type | Encryption | Notes |
|------------|------|------------|-------|
| External users and partners to CN Primary DC | Internet | TLS 1.2 or later | Traffic terminates at INF-04 in the DMZ; no direct Intranet access |
| CN Primary DC to US DC | VPN/MPLS | VPN encryption method TBD; MPLS encryption TBD | Cross-application API calls are mediated by CMP-04 |
| CN Primary DC to CN Secondary DC | VPN/MPLS | Encryption method TBD | HTTPS traffic uses OAuth2; events use SASL/SCRAM |
| CN Primary DC to Support DC | VPN/MPLS | Encryption method TBD | HTTPS with OAuth2 |
| CN Primary DC to Azure satellites | Internet or private connectivity TBD | TLS 1.2 or later for HTTPS; event transport encryption TBD | Exact Azure region and connectivity type are TBD |
| CN Primary DC to SAP landscape | Private connectivity type TBD | TLS protection for RFC is TBD; HTTPS uses TLS 1.2 or later | SAP is not exposed to the DMZ |
| CN Primary DC to external file partners | Internet | SFTP/SSH | Managed through CMP-11; detailed routing is TBD |

## 5. Technical Components (New/Modified Only)

| Component | Type | Language | Framework | Runtime | Sensitivity |
|-----------|------|----------|-----------|---------|-------------|
| INF-04 F5 | Load balancer / ingress | N/A | F5 | Private DC appliance | Acme Confidential |
| INF-03 Edge router | Network router | N/A | TBD | Private DC network platform | Acme Confidential |
| CMP-01 Service-Supply-Chain-dmz-nginx-proxy | Reverse proxy | N/A | Nginx, version TBD | Internal K8s, DMZ | Acme Confidential |
| CMP-02 Service-Supply-Chain-gateway | Backend API gateway service | Java, version TBD | Spring Cloud, version TBD | Internal K8s, DMZ | Acme Confidential |
| CMP-03 Service-Supply-Chain-web | Web frontend | Java, version TBD | Spring Cloud, version TBD | Internal K8s, DMZ | Acme Confidential |
| CMP-04 WSO2 | API integration platform | TBD | WSO2 API Gateway, version TBD | Private DC, Intranet | Acme Confidential |
| CMP-05 Kafka (primary) | Message bus | TBD | Kafka, version TBD | Private DC, Intranet | Acme Confidential |
| CMP-06 Service-Supply-Chain-int-nginx-proxy | Reverse proxy | N/A | Nginx, version TBD | Internal K8s, Intranet | Acme Confidential |
| CMP-07 Service-Supply-Chain-main | Backend service | Java, version TBD | Spring Cloud, version TBD | Internal K8s, Intranet | Acme Confidential |
| CMP-08 Service-Supply-Chain-websocket | WebSocket backend | Java, version TBD | Spring Cloud, version TBD | Internal K8s, Intranet | Acme Confidential |
| CMP-09 Service-Supply-Chain-* group (10 services) | Backend service group | Java, version TBD | Spring Cloud, version TBD | Internal K8s, Intranet | Acme Confidential |
| CMP-10 Service-Supply-Chain-* group (22 services) | Backend service group | Java, version TBD | Spring Cloud, version TBD | Internal K8s, Intranet | Acme Confidential |
| CMP-12 through CMP-16 MySQL HA groups | Relational databases | N/A | MySQL, version TBD | Private DC HA, each 1 primary and 2 replicas | Acme Confidential |
| CMP-17 Redis HA | Cache | N/A | Redis, version TBD | Private DC HA, 3 primary and 3 replica nodes | Acme Confidential |
| CMP-18 RabbitMQ HA | Message queue | N/A | RabbitMQ, version TBD | Private DC HA, 3 replicas | Acme Confidential |
| CMP-19 Elasticsearch HA | Search datastore | N/A | Elasticsearch, version TBD | Private DC HA, 3 nodes | Acme Confidential |
| CMP-11 MFT platform | Managed file transfer | TBD | MFT platform, version TBD | Private DC, Intranet | Acme Confidential |

CMP-09 members are `rms`, `tms`, `oms`, `wms`, `mds`, `ips`, `autopilot`, `ves`, `cfs`, and `scs`. CMP-10 members are `wms`, `oms`, `pps`, `eta`, `scs`, `auth`, `pbs`, `rns`, `vrs`, `ibs`, `cfs`, `lvr`, `tms`, `pms`, `mds`, `rms`, `ws-stock`, `rms-xdoc`, `data`, `sys`, and `wms-xdoc`; the source states 22 services but lists 21 names, so reconciliation is TBD.

## 6. Integration Points

| # | From | To | Protocol | Port | Auth Method | Notes |
|---|------|----|----------|------|-------------|-------|
| INT-001 | External client | INF-04 F5 | HTTPS | 443 | OAuth2, flow TBD | TLS termination at ingress |
| INT-002 | INF-04 F5 | CMP-01 Service-Supply-Chain-dmz-nginx-proxy | HTTPS | 443 | TBD | Internal ingress authentication is not specified |
| INT-003 | CMP-03 Service-Supply-Chain-web | CMP-02 Service-Supply-Chain-gateway | HTTPS | 443 | OAuth2 | DMZ flow |
| INT-004 | CMP-02 Service-Supply-Chain-gateway | CMP-04 WSO2 | HTTPS | 443 | Basic Auth | Weak mechanism; migration and rotation controls TBD |
| INT-005 | CMP-04 WSO2 | CMP-09 and CMP-10 service groups | HTTPS | 443 | Basic Auth | All cross-application calls must be mediated |
| INT-006 | CMP-06 through CMP-10 | CMP-05 Kafka (primary) | TCP | 9093 | SASL/SCRAM | Transport encryption configuration TBD |
| INT-007 | CMP-06 through CMP-10 | CMP-12 through CMP-16 | JDBC over TCP | 3306 | User/password from K8s Secrets | DB Zone permits Intranet services only |
| INT-008 | CMP-06 through CMP-10 | CMP-17 Redis HA | TCP | 6379 | Basic Auth | TLS configuration and stronger auth TBD |
| INT-009 | CMP-06 through CMP-10 | CMP-19 Elasticsearch HA | HTTPS | 19200 | Basic Auth | TLS 1.2 or later |
| INT-010 | CMP-06 through CMP-10 | CMP-18 RabbitMQ HA | TCP | 5672 | Basic Auth | TLS configuration and stronger auth TBD |
| INT-011 | CMP-06 through CMP-10 | CMP-31 S4 | TCP/RFC | 33xx | SAP Logon Ticket | Exact port and RFC transport protection TBD |
| INT-012 | CMP-31 S4 | CMP-32 SECC | TCP/RFC | 33xx | SAP Logon Ticket, confirmation TBD | Exact port TBD |
| INT-013 | CMP-31 S4 | CMP-33 LSCRM | TCP/RFC | 33xx | SAP Logon Ticket, confirmation TBD | Exact port TBD |
| INT-014 | CMP-31 S4 | CMP-34 CECC | TCP/RFC | 33xx | SAP Logon Ticket, confirmation TBD | Exact port TBD |
| INT-015 | CMP-06 through CMP-10 | CMP-35 S3 | HTTPS | 443 | Basic Auth | Object-storage credential rotation TBD |
| INT-016 | CMP-04 WSO2 | CMP-20 Account-Service | HTTPS | 443 | Basic Auth | CN Primary to US DC mediated API |
| INT-017 | CMP-04 WSO2 | CMP-21 Service-customer-master-data | HTTPS | 443 | Basic Auth | CN Primary to US DC mediated API |
| INT-018 | CMP-04 WSO2 | CMP-22 Serice-Data-serviceE | HTTPS | 443 | Basic Auth | CN Primary to US DC mediated API |
| INT-019 | CMP-04 WSO2 | CMP-23 Price-master-ROW | HTTPS | 443 | Basic Auth | CN Primary to US DC mediated API |
| INT-020 | CMP-04 WSO2 | CMP-24 Reverse-Management-System | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-021 | CMP-04 WSO2 | CMP-25 procurement-service | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-022 | CMP-04 WSO2 | CMP-26 lakehouse | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-023 | CMP-05 Kafka (primary) | CMP-27 Kafka (secondary) | TCP | 9093 | SASL/SCRAM | Direction and TLS configuration TBD |
| INT-024 | CMP-04 WSO2 | CMP-28 support-hub | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-025 | CMP-04 WSO2 | CMP-29 support-portal | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-026 | CMP-04 WSO2 | CMP-30 support-gateway | HTTPS | 443 | OAuth2 | Exact OAuth2 flow TBD |
| INT-027 | CMP-04 WSO2 | CMP-36 d365-service-delivery-bu1 | HTTPS | 443 | OAuth2 | Exact Azure endpoint and OAuth2 flow TBD |
| INT-028 | CMP-04 WSO2 | CMP-37 d365-service-delivery-bu2 | HTTPS | 443 | OAuth2 | Exact Azure endpoint and OAuth2 flow TBD |
| INT-029 | CMP-04 WSO2 | CMP-38 d365-service-delivery-bu3 | HTTPS | 443 | OAuth2 | Exact Azure endpoint and OAuth2 flow TBD |
| INT-030 | CMP-05 Kafka (primary) | CMP-39 edge-cache | TCP | 9093 | SASL/SCRAM | Direction and TLS configuration TBD |
| INT-031 | CMP-04 WSO2 | CMP-40 logistics partner A | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-032 | CMP-04 WSO2 | CMP-41 logstics-vendor-1 | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-033 | CMP-04 WSO2 | CMP-42 logistics partner B | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-034 | CMP-04 WSO2 | CMP-43 logistics partner C | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-035 | CMP-04 WSO2 | CMP-44 logistics partner D | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-036 | CMP-04 WSO2 | CMP-45 logistics partner E | HTTPS or TCP/EDI | 443 or TBD | OAuth2 for HTTPS; EDI authentication TBD | Exact protocol selection TBD |
| INT-037 | CMP-11 MFT platform | CMP-46 file partner A | SFTP | 22 | SSH key | Partner file flow; key rotation TBD |
| INT-038 | CMP-11 MFT platform | CMP-47 file partner B | SFTP | 22 | SSH key | Partner file flow; key rotation TBD |
| INT-039 | CMP-11 MFT platform | CMP-48 file partner C | SFTP | 22 | SSH key | Partner file flow; key rotation TBD |
| INT-040 | CMP-03 Service-Supply-Chain-web | INF-09 ADFS | SAML 2.0 over HTTPS | 443 | SAML assertion | Internal employees and BU users |
| INT-041 | External portals, exact component TBD | INF-10 Enterprise ID | OIDC/OAuth2 over HTTPS | 443 | OAuth2 Authorization Code / OIDC, confirmation TBD | Partners and carriers |

## 7. User Authentication

| Entry Point | User Roles | Auth Server | Protocol | Authorization |
|-------------|------------|-------------|----------|---------------|
| CMP-03 Service-Supply-Chain-web | Internal operations; BU users | INF-09 ADFS | SAML 2.0 | Central AuthZ Platform, RBAC |
| External portals, exact component TBD | Partners; carriers | INF-10 Enterprise ID | OAuth2/OIDC, exact flow TBD | Central AuthZ Platform, RBAC |

## 8. Credential and Key Protection

| Environment | Solution | Notes |
|-------------|----------|-------|
| Private DC Internal K8s | Kubernetes Secrets | Encryption at rest, external secret integration, access policy, and rotation schedule are TBD; hardcoded credentials are prohibited |
| Private DC non-K8s platforms | TBD enterprise secret store | Applies to INF-04, CMP-04, CMP-05, CMP-12 through CMP-19, CMP-11, and INF-03 |
| Azure | TBD | Secret-storage ownership and controls for CMP-36 through CMP-39 are not supplied |
| Partner SFTP | SSH keys managed by CMP-11, detailed vault TBD | Rotation schedule and partner key lifecycle are TBD |

## 9. Data Encryption

| Component | At Rest | In Transit | Cross-Border | Compliance |
|-----------|---------|------------|--------------|------------|
| CMP-12 through CMP-16 MySQL HA | TBD | TLS 1.2 or later required; JDBC TLS configuration TBD | Potential CN-US flow; data fields TBD | Classification policy; cross-border basis TBD |
| CMP-17 Redis HA | TBD | TLS 1.2 or later required; configuration TBD | Potential CN-US flow; data fields TBD | Classification policy; cross-border basis TBD |
| CMP-18 RabbitMQ HA | TBD | TLS 1.2 or later required; configuration TBD | Potential CN-US flow; event fields TBD | Classification policy; cross-border basis TBD |
| CMP-19 Elasticsearch HA | TBD | TLS 1.2 or later | Potential CN-US flow; indexed fields TBD | Classification policy; cross-border basis TBD |
| CMP-05 and CMP-27 Kafka | TBD | TLS 1.2 or later required; configuration TBD | Yes, if events cross CN-US; event fields TBD | Cross-border basis TBD |
| CMP-11 managed files | TBD | SFTP/SSH | Yes where partner location is outside CN; file contents TBD | Cross-border basis TBD |

## 10. Open Items / TBDs

| ID | Item | Owner | Target Date |
|----|------|-------|-------------|
| TBD-001 | Confirm NA cut-over sequence for CMP-10 group | Program | TBD |
| TBD-002 | Confirm CMP-11 to CMP-05 replacement roadmap | Integration owner | TBD |
| TBD-003 | Reconcile CMP-10 stated count of 22 with the 21 supplied member names | Application owner | TBD |
| TBD-004 | Define authentication between INF-04 and CMP-01 | Security / platform owner | TBD |
| TBD-005 | Select HTTPS or TCP/EDI per CMP-40 through CMP-45 and define EDI authentication | Integration / partner owners | TBD |
| TBD-006 | Confirm exact SAP hosting location, RFC ports, authentication, and transport encryption | SAP owner | TBD |
| TBD-007 | Confirm Azure region, network placement, and connectivity type | Cloud owner | TBD |
| TBD-008 | Confirm encryption for every VPN/MPLS path and all non-HTTPS protocols | InfraSec | TBD |
| TBD-009 | Define non-K8s secret stores and credential/key rotation controls | InfraSec | TBD |
| TBD-010 | Confirm at-rest encryption methods for databases, caches, queues, indexes, events, and managed files | Data / platform owners | TBD |
| TBD-011 | Identify cross-border data elements and establish the applicable transfer compliance basis | Privacy / legal | TBD |
| TBD-012 | Confirm business owner, department, and target go-live date | Program | TBD |
| TBD-013 | Replace or formally risk-accept Basic Auth integrations | Security / integration owner | TBD |

## 11. Architecture Constraints

- Private cloud is mandatory for the SDP platform; Azure systems are existing satellites only.
- The primary SDP deployment remains in the CN Primary DC using separate DMZ, Intranet, and DB zones.
- All cross-application API traffic must traverse CMP-04 WSO2; event traffic must traverse CMP-05 Kafka. Direct application-to-application connections are prohibited.
- Managed partner file transfer must traverse CMP-11 MFT platform.
- SAP CMP-31 through CMP-34 may be reached only by RFC from the Intranet zone and must not be exposed to the DMZ.
- The DB Zone is reachable only from SDP Intranet services, and each persistence service uses the stated HA topology.
- External 3PL and file-transfer traffic must terminate at INF-04 in the DMZ and must never connect directly to the Intranet.
- TLS 1.2 or later is required for all applicable traffic. Equivalent encrypted transport must be defined for non-TLS protocols.
- Credentials must not be hardcoded. Workload database credentials are stored in Kubernetes Secrets.
- No IP addresses or CIDR ranges are specified by the approved sources; architecture outputs must use named zones and locations until network allocations are approved.
