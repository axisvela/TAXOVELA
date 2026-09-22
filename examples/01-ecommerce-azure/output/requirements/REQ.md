# Requirements Document - E-commerce Platform (Azure Multi-Region Hub-Spoke)
**Version**: 1.0 Draft  |  **Date**: 2026-09-14  |  **Author**: TBD
**Project ID**: 01-ecommerce-azure  |  **Business Project ID**: ECOM-AZ-001
**Classification**: Acme Confidential
**Scope**: E2E cross-system solution. The Azure network and hosting platform is new; US HQ DC systems and Japan DC systems are existing applications treated as black boxes.

## 1. Project Overview
The project provides network and application hosting architecture for an e-commerce platform serving the US business unit from Azure East US and the AP market from Azure Japan East. Each Azure region must use the corporate hub-spoke pattern, centralized firewall inspection, and hybrid connectivity to its local on-premises data center. The available inputs define infrastructure topology but do not define business ownership, application protocols, application authentication, detailed application stacks, or recovery objectives; those facts remain TBD.

## 2. Applications in Scope
| ID | Resolved Name | Type | New/Existing | Owner | Scope |
|----|---------------|------|--------------|-------|-------|
| SYS-01 | vnet-ecom-coreservice-eus | Network | New | TBD | East US hub VNet |
| SYS-02 | vnet-ecom-bu-eus | Network | New | TBD | East US BU spoke VNet |
| SYS-03 | vnet-ecom-common-eus | Network | New | TBD | East US shared-services spoke VNet |
| SYS-04 | vnet-ecom-coreservice-ap | Network | New | TBD | Japan East hub VNet |
| SYS-05 | vnet-ecom-ap-prod | Network | New | TBD | Japan East AP spoke VNet |
| SYS-06 | Azure Firewall (EastUS) | Security | New | TBD | East US centralized inspection and forced egress |
| SYS-07 | ExpressRoute gateway (EastUS) | Network | New | TBD | East US hybrid gateway |
| SYS-08 | Azure Firewall (JapanEast) | Security | New | TBD | Japan East centralized inspection and forced egress |
| SYS-09 | ExpressRoute gateway (JapanEast) | Network | New | TBD | Japan East hybrid gateway |
| SYS-10 | Application Gateway | Security | New | TBD | Public ingress with WAF |
| SYS-11 | AKS (BU) | Platform | New | TBD | US BU workload cluster |
| SYS-12 | App VMs | Backend | New | TBD | US BU application servers |
| SYS-13 | DB (BU) | Database | New | TBD | US BU database tier |
| SYS-14 | Common AKS | Platform | New | TBD | Shared workload cluster |
| SYS-15 | Shared services | Backend | New | TBD | Shared backend services |
| SYS-16 | Storage | Storage | New | TBD | Storage private endpoints |
| SYS-17 | AKS (AP) | Platform | New | TBD | AP workload cluster |
| SYS-18 | App (AP) | Backend | New | TBD | AP application tier |
| SYS-19 | DB (AP) | Database | New | TBD | AP database tier |
| SYS-20 | US HQ DC systems | External application boundary | Existing | TBD | Black-box US corporate systems |
| SYS-21 | Japan DC systems | External application boundary | Existing | TBD | Black-box Japan local systems |
| SYS-22 | Carrier A ExpressRoute | Network circuit | New | Carrier A | Primary US dedicated circuit |
| SYS-23 | Carrier B ExpressRoute | Network circuit | New | Carrier B | Secondary US dedicated circuit |
| SYS-24 | MPLS | Network circuit | Existing/TBD | TBD | Backup US WAN path |
| SYS-25 | Internet VPN | Network circuit | Existing/TBD | TBD | Backup US VPN path |
| SYS-26 | Carrier C ExpressRoute | Network circuit | New | Carrier C | Primary Japan dedicated circuit |

## 3. Physical Deployment
| App/Component | Country/Region | DC / Cloud Region | Zone/Subnet | Owner |
|---------------|----------------|-------------------|-------------|-------|
| SYS-01 vnet-ecom-coreservice-eus | United States / NA | Azure East US | Hub VNet (CoreService) | TBD |
| SYS-02 vnet-ecom-bu-eus | United States / NA | Azure East US | BU spoke VNet | TBD |
| SYS-03 vnet-ecom-common-eus | United States / NA | Azure East US | Common spoke VNet | TBD |
| SYS-04 vnet-ecom-coreservice-ap | Japan / APAC-JP | Azure Japan East | Hub VNet (CoreService-AP) | TBD |
| SYS-05 vnet-ecom-ap-prod | Japan / APAC-JP | Azure Japan East | AP spoke VNet | TBD |
| SYS-06 Azure Firewall (EastUS) | United States / NA | Azure East US | AzureFirewallSubnet in SYS-01 | TBD |
| SYS-07 ExpressRoute gateway (EastUS) | United States / NA | Azure East US | GatewaySubnet in SYS-01 | TBD |
| SYS-08 Azure Firewall (JapanEast) | Japan / APAC-JP | Azure Japan East | AzureFirewallSubnet in SYS-04 | TBD |
| SYS-09 ExpressRoute gateway (JapanEast) | Japan / APAC-JP | Azure Japan East | GatewaySubnet in SYS-04 | TBD |
| SYS-10 Application Gateway | United States / NA | Azure East US | Application Gateway subnet in SYS-02 | TBD |
| SYS-11 AKS (BU) | United States / NA | Azure East US | AKS subnet in SYS-02 | TBD |
| SYS-12 App VMs | United States / NA | Azure East US | Application subnet in SYS-02 | TBD |
| SYS-13 DB (BU) | United States / NA | Azure East US | Database subnet in SYS-02 | TBD |
| SYS-14 Common AKS | United States / NA | Azure East US | Common AKS subnet in SYS-03 | TBD |
| SYS-15 Shared services | United States / NA | Azure East US | Shared-backend subnet in SYS-03 | TBD |
| SYS-16 Storage | United States / NA | Azure East US | Private-endpoint subnet in SYS-03 | TBD |
| SYS-17 AKS (AP) | Japan / APAC-JP | Azure Japan East | AKS subnet in SYS-05 | TBD |
| SYS-18 App (AP) | Japan / APAC-JP | Azure Japan East | Application subnet in SYS-05 | TBD |
| SYS-19 DB (AP) | Japan / APAC-JP | Azure Japan East | Database subnet in SYS-05 | TBD |
| SYS-20 US HQ DC systems | United States / NA | US HQ DC, City C, State X | Exact zone TBD | TBD |
| SYS-21 Japan DC systems | Japan / APAC-JP | Japan DC, Osaka | Exact zone TBD | TBD |

No IP addresses or CIDR ranges are specified or required by these requirements.

## 4. Network Topology
| Connection | Type | Encryption | Notes |
|------------|------|------------|-------|
| SYS-01 vnet-ecom-coreservice-eus to SYS-02 vnet-ecom-bu-eus | VNet peering | Azure backbone; payload encryption method TBD | All routed traffic must be inspected by SYS-06; UDR forced tunneling required |
| SYS-01 vnet-ecom-coreservice-eus to SYS-03 vnet-ecom-common-eus | VNet peering | Azure backbone; payload encryption method TBD | All routed traffic must be inspected by SYS-06; UDR forced tunneling required |
| SYS-02 vnet-ecom-bu-eus to SYS-03 vnet-ecom-common-eus | Peering stated in source; permitted implementation TBD | TBD | Source also prohibits direct spoke-to-spoke bypass; routing must hairpin through SYS-06 |
| SYS-04 vnet-ecom-coreservice-ap to SYS-05 vnet-ecom-ap-prod | VNet peering | Azure backbone; payload encryption method TBD | All routed traffic must be inspected by SYS-08; UDR forced tunneling required |
| SYS-01 vnet-ecom-coreservice-eus to SYS-20 US HQ DC systems via SYS-22 Carrier A ExpressRoute | ExpressRoute | Encryption method TBD | Primary dedicated circuit; reference RTT approximately 4 ms |
| SYS-01 vnet-ecom-coreservice-eus to SYS-20 US HQ DC systems via SYS-23 Carrier B ExpressRoute | ExpressRoute | Encryption method TBD | Secondary dedicated circuit from a different carrier |
| SYS-01 vnet-ecom-coreservice-eus to SYS-20 US HQ DC systems via SYS-24 MPLS | MPLS | Encryption method TBD | Backup WAN path |
| SYS-01 vnet-ecom-coreservice-eus to SYS-20 US HQ DC systems via SYS-25 Internet VPN | Internet VPN | VPN encryption required; method TBD | Backup VPN path |
| SYS-04 vnet-ecom-coreservice-ap to SYS-21 Japan DC systems via SYS-26 Carrier C ExpressRoute | ExpressRoute | Encryption method TBD | Primary dedicated circuit; second circuit is TBD |
| Azure East US to Azure Japan East | TBD | Encryption in transit required | No inter-region topology or application/data flow is specified |

## 5. Technical Components (New/Modified Only)
| Component | Type | Language | Framework | Runtime | Sensitivity |
|-----------|------|----------|-----------|---------|-------------|
| SYS-06 Azure Firewall (EastUS) | SEC | N/A | Azure Firewall | Azure managed service | Acme Confidential |
| SYS-07 ExpressRoute gateway (EastUS) | Network gateway | N/A | Azure ExpressRoute gateway | Azure managed service | Acme Confidential |
| SYS-08 Azure Firewall (JapanEast) | SEC | N/A | Azure Firewall | Azure managed service | Acme Confidential |
| SYS-09 ExpressRoute gateway (JapanEast) | Network gateway | N/A | Azure ExpressRoute gateway | Azure managed service | Acme Confidential |
| SYS-10 Application Gateway | LB/SEC | N/A | Application Gateway with WAF | Azure managed service | Acme Confidential |
| SYS-11 AKS (BU) | Platform | Workload language TBD | Workload framework TBD | AKS | Acme Confidential |
| SYS-12 App VMs | BE | TBD | TBD | Azure VMs | Acme Confidential |
| SYS-13 DB (BU) | DB | TBD | Database engine TBD | Azure hosting model TBD | Acme Confidential |
| SYS-14 Common AKS | Platform | Workload language TBD | Workload framework TBD | AKS | Acme Confidential |
| SYS-15 Shared services | BE | TBD | TBD | Runtime TBD | Acme Confidential |
| SYS-16 Storage | Storage | N/A | Azure storage service SKU TBD | Azure managed service with private endpoint | Acme Confidential |
| SYS-17 AKS (AP) | Platform | Workload language TBD | Workload framework TBD | AKS | Acme Confidential |
| SYS-18 App (AP) | BE | TBD | TBD | Runtime TBD | Acme Confidential |
| SYS-19 DB (AP) | DB | TBD | Database engine TBD | Azure hosting model TBD | Acme Confidential |

## 6. Integration Points
| # | From | To | Protocol | Port | Auth Method | Notes |
|---|------|----|----------|------|-------------|-------|
| INT-01 | External e-commerce users | SYS-10 Application Gateway | HTTPS | 443 | User authentication method TBD | Public WAF-enabled ingress; downstream destination is TBD |
| INT-02 | SYS-10 Application Gateway | SYS-11 AKS (BU) and/or SYS-12 App VMs | HTTPS expected; final protocol TBD | TBD | Service authentication TBD | Backend selection and health-probe details are TBD |
| INT-03 | SYS-11 AKS (BU) and/or SYS-12 App VMs | SYS-13 DB (BU) | TBD | TBD | Database authentication TBD | Exact initiator and database engine are TBD |
| INT-04 | SYS-11 AKS (BU), SYS-12 App VMs, and/or SYS-14 Common AKS | SYS-15 Shared services | TBD | TBD | Service authentication TBD | Exact consumers and interfaces are TBD |
| INT-05 | Authorized East US workloads, exact initiators TBD | SYS-16 Storage | HTTPS expected; final protocol TBD | 443/TBD | Workload identity or other authentication TBD | Access only through the private endpoint |
| INT-06 | SYS-17 AKS (AP) and/or SYS-18 App (AP) | SYS-19 DB (AP) | TBD | TBD | Database authentication TBD | Exact initiator and database engine are TBD |
| INT-07 | SYS-20 US HQ DC systems | East US workloads, exact target TBD | TBD | TBD | Service authentication TBD | Uses SYS-22/SYS-23 with SYS-24/SYS-25 backup; direction may be bidirectional |
| INT-08 | SYS-21 Japan DC systems | SYS-17 AKS (AP) | TBD | TBD | Service authentication TBD | SYS-17 must be routable through SYS-26; direction may be bidirectional |

Network peering, route propagation, firewall transit, and circuit transport are topology relationships rather than application authentication boundaries. Every application interaction above requires a specific authentication mechanism before design approval.

## 7. User Authentication
| Entry Point | User Roles | Auth Server | Protocol | Authorization |
|-------------|------------|-------------|----------|---------------|
| SYS-10 Application Gateway / e-commerce application | External customers; exact roles TBD | TBD | TBD | Model and platform TBD |
| Internal administration entry point TBD | Internal administrators | ADFS | Protocol TBD | Authorization model and platform TBD |
| Azure control plane | Azure administrators; exact roles TBD | Microsoft Entra ID | Protocol TBD | Azure RBAC; role assignments TBD |

## 8. Credential & Key Protection
| Environment | Solution | Notes |
|-------------|----------|-------|
| Azure East US | TBD | Azure Key Vault usage, managed identities, rotation, soft-delete, and purge protection are not specified |
| Azure Japan East | TBD | Azure Key Vault usage, managed identities, rotation, soft-delete, and purge protection are not specified |
| US HQ DC | TBD | Existing systems are black boxes; boundary credential handling is TBD |
| Japan DC | TBD | Existing systems are black boxes; boundary credential handling is TBD |

No source states that credentials are hardcoded. This must be confirmed explicitly.

## 9. Data Encryption
| Component | At Rest | In Transit | Cross-Border | Compliance |
|-----------|---------|------------|--------------|------------|
| SYS-11 AKS (BU), SYS-12 App VMs, SYS-14 Common AKS, SYS-15 Shared services, SYS-17 AKS (AP), SYS-18 App (AP) | Method TBD | Required; protocol/version TBD | No residency constraint; actual flows TBD | Acme Confidential controls; detailed standard TBD |
| SYS-13 DB (BU) | Required status and method TBD | Required; protocol/version TBD | No residency constraint; actual flows TBD | Acme Confidential controls; detailed standard TBD |
| SYS-16 Storage | Required status and method TBD | Required; protocol/version TBD | No residency constraint; actual flows TBD | Acme Confidential controls; private endpoint mandatory |
| SYS-19 DB (AP) | Required status and method TBD | Required; protocol/version TBD | No residency constraint; actual flows TBD | Acme Confidential controls; detailed standard TBD |
| Hybrid links SYS-22 through SYS-26 | N/A | Required; ExpressRoute/MPLS encryption methods TBD, SYS-25 VPN method TBD | No residency constraint; actual data flows TBD | Applicable privacy and sector obligations TBD |

## 10. Open Items / TBDs
| ID | Item | Owner | Target Date |
|----|------|-------|-------------|
| TBD-01 | Decide whether SYS-21 Japan DC requires a second dedicated circuit | TBD | TBD |
| TBD-02 | Complete firewall rule-set and egress FQDN-tag review for SYS-11, SYS-14, and SYS-17 | TBD | TBD |
| TBD-03 | Resolve the source conflict between stated SYS-02-to-SYS-03 peering and the prohibition on direct spoke-to-spoke bypass | Network Architecture | TBD |
| TBD-04 | Identify department, business owner, infrastructure owners, operational owners, and document author | Project Sponsor | TBD |
| TBD-05 | Define application languages, frameworks, versions, runtimes, database engines, and storage SKU | Application Architecture | TBD |
| TBD-06 | Define every application interface, initiator, provider, protocol, port, and authentication mechanism | Application and Security Architecture | TBD |
| TBD-07 | Define customer authentication, internal administration entry point, identity protocols, roles, and authorization model | IAM | TBD |
| TBD-08 | Define secret storage, managed identity use, key ownership, rotation, soft-delete, and purge protection | Security Architecture | TBD |
| TBD-09 | Confirm encryption-at-rest methods and in-transit protocol versions, including hybrid circuit encryption | Security and Network Architecture | TBD |
| TBD-10 | Define inter-region connectivity, replication, failover, RTO, RPO, availability targets, capacity, and scaling | Solution Architecture | TBD |
| TBD-11 | Identify exact zones for SYS-20 US HQ DC systems and SYS-21 Japan DC systems | Infrastructure | TBD |
| TBD-12 | Confirm data types, PII/payment-data handling, data flows, retention, backup, and applicable compliance obligations | Data and Compliance | TBD |
| TBD-13 | Confirm that no credentials are hardcoded | Security Architecture | TBD |

All open items are non-blocking for this draft requirements artifact because physical regions and the public ingress boundary are known. Items concerning authentication, encryption, and routing must be resolved before production design approval.

## 11. Architecture Constraints
- Use Azure East US for the US business unit and Azure Japan East for the AP platform.
- Use a hub-spoke topology in both regions.
- Force all spoke egress and spoke-to-spoke traffic through SYS-06 Azure Firewall (EastUS) or SYS-08 Azure Firewall (JapanEast) using UDRs; no firewall-bypass route is permitted.
- Keep SYS-06 and SYS-07 in SYS-01; keep SYS-08 and SYS-09 in SYS-04.
- Provide a DMZ subnet in SYS-02 and SYS-05.
- Use SYS-10 Application Gateway with WAF for public ingress.
- Permit SYS-16 Storage access only through its private endpoint.
- Provide dual-carrier dedicated US circuits using SYS-22 Carrier A ExpressRoute and SYS-23 Carrier B ExpressRoute, with SYS-24 MPLS and SYS-25 Internet VPN backup paths.
- Provide SYS-26 Carrier C ExpressRoute as the primary Japan hybrid circuit; a second circuit remains TBD.
- Make SYS-17 AKS (AP) routable from SYS-21 Japan DC systems through the dedicated circuit and inspected path.
- Make all east-west traffic inspectable.
- Encrypt all data in transit; exact mechanisms remain TBD where the sources do not specify them.
- Apply Acme Confidential handling. No cross-border data-residency restriction is currently stated.
- Do not introduce IP addresses or CIDR ranges into requirements artifacts.

## 12. Source Traceability
| Source | Resolution / Use |
|--------|------------------|
| `input/prompt.md` | Primary one-shot topology and constraint source |
| `input/prompt-indexed.md` | Stable SYS-numbered companion prompt used with the systems registry |
| `input/systems-registry.md` | Authoritative resolution of stable SYS-01 through SYS-26 identifiers to document names |
| `input/documents/requirements.md` | Existing requirements, security constraints, and open items |
| `project.yaml` | Project identity, Azure platform, and confidential classification |
| `config.yaml` | Physical location details and configured platform/identity names |
