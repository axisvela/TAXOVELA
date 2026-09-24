# Systems Registry - E-commerce Platform (Azure)

Single source of truth for literal entity names in this req/v2 example.

- Documents outside this registry cite typed codes only.
- INF holds topology and appliances; APP holds systems; CMP holds application artifacts.
- Kubernetes is deployment runtime detail, not an INF or CMP row. ExpressRoute, MPLS, VPN, and peering are LNK rows.

## R1 - Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | vNet-eCom-CoreService-EUS | iaas_vpc_vnet | public_cloud | prod_network | - | US | eus-hub | East US hub VNet |
| INF-02 | EastUS-VNET-A-BU | iaas_vpc_vnet | public_cloud | prod_network | - | US | eus-bu-spoke | East US business-unit spoke |
| INF-03 | EastUS-VNET-Common | iaas_vpc_vnet | public_cloud | prod_network | - | US | eus-common-spoke | East US shared-services spoke |
| INF-04 | VNET-Flash-CoreService-AP-Prod | iaas_vpc_vnet | public_cloud | prod_network | - | JP | jpe-hub | Japan East hub VNet |
| INF-05 | Vnet-Flash-AP-Prod | iaas_vpc_vnet | public_cloud | prod_network | - | JP | jpe-spoke | Japan East application spoke |
| INF-06 | AzureFirewallSubnet firewall | firewall | public_cloud | prod_network | INF-01 | US | eus-firewall | Forced east-west, hybrid, and egress inspection |
| INF-07 | GatewaySubnet gateway | vpn_gateway | public_cloud | prod_network | INF-01 | US | eus-hybrid-gateway | ExpressRoute termination gateway |
| INF-08 | AzureFirewallSubnet firewall | firewall | public_cloud | prod_network | INF-04 | JP | jpe-firewall | Forced hybrid and egress inspection |
| INF-09 | GatewaySubnet gateway | vpn_gateway | public_cloud | prod_network | INF-04 | JP | jpe-hybrid-gateway | ExpressRoute termination gateway |
| INF-10 | APPGW subnet App Gateway | waf | public_cloud | dmz | INF-02 | US | eus-waf | Public ingress WAF-enabled application gateway |
| INF-11 | AKS subnet cluster | subnet | public_cloud | prod_network | INF-02 | US | eus-bu-runtime-zone | Kubernetes runtime location only |
| INF-12 | APP subnet VMs | subnet | public_cloud | prod_network | INF-02 | US | eus-bu-app-zone | VM application location |
| INF-13 | DB subnet | subnet | public_cloud | prod_network | INF-02 | US | eus-bu-db-zone | Database location |
| INF-14 | Common-AKS subnet | subnet | public_cloud | prod_network | INF-03 | US | eus-common-runtime-zone | Kubernetes runtime location only |
| INF-15 | Common subnet shared services | subnet | public_cloud | prod_network | INF-03 | US | eus-shared-zone | Shared-service location |
| INF-16 | Storage-Endpoint subnet | subnet | public_cloud | prod_network | INF-03 | US | eus-storage-zone | Private endpoint location |
| INF-17 | Subnet-Flash-AP-AKS | subnet | public_cloud | prod_network | INF-05 | JP | jpe-runtime-zone | Kubernetes runtime location only |
| INF-18 | Subnet-Flash-AP-APP | subnet | public_cloud | prod_network | INF-05 | JP | jpe-app-zone | Application location |
| INF-19 | Subnet-Flash-AP-DB | subnet | public_cloud | prod_network | INF-05 | JP | jpe-db-zone | Database location |
| INF-20 | dc-us | data_center | private_cloud | prod_network | - | US | us-dc | Existing corporate boundary |
| INF-21 | dc-jp | data_center | private_cloud | prod_network | - | JP | jp-dc | Existing local boundary |

## R2 - Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | E-commerce US | new | biz_owned | - | us-commerce | East US workload |
| APP-02 | E-commerce AP | new | biz_owned | - | ap-commerce | Japan East workload |
| APP-03 | US HQ DC systems | existing | org_it | - | us-corporate | Black-box integration boundary |
| APP-04 | Japan DC systems | existing | org_it | - | jp-corporate | Black-box integration boundary |

## R3 - Components

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | AKS (BU) workload | APP-01 | runtime | service | be | backend_service | - | us-k8s-workload | AKS is runtime detail |
| CMP-02 | App VMs | APP-01 | app | component | be | backend_service | - | us-vm-app | Private VM tier |
| CMP-03 | DB (BU) | APP-01 | data | component | db | database | TBD | us-db | Engine TBD |
| CMP-04 | Common AKS workload | APP-01 | shared | service | be | backend_service | - | common-k8s-workload | AKS is runtime detail |
| CMP-05 | Shared services | APP-01 | shared | service | be | backend_service | - | shared-services | Interface TBD |
| CMP-06 | Storage | APP-01 | data | component | db | object_storage | Azure platform encryption | storage | Private endpoint only |
| CMP-07 | AKS (AP) workload | APP-02 | runtime | service | be | backend_service | - | ap-k8s-workload | AKS is runtime detail |
| CMP-08 | App (AP) | APP-02 | app | component | be | backend_service | - | ap-app | Private application tier |
| CMP-09 | DB (AP) | APP-02 | data | component | db | database | TBD | ap-db | Engine TBD |
| CMP-10 | US HQ integration boundary | APP-03 | boundary | component | ip | integration_service | - | us-boundary | Black-box boundary component |
| CMP-11 | Japan integration boundary | APP-04 | boundary | component | ip | integration_service | - | jp-boundary | Black-box boundary component |

## R4 - Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|------------|--------------|--------|----------|------|
| DEP-01 | BU AKS workload | CMP-01 | prod | public_cloud | public_cloud_region | INF-11 | container | 2 | us-k8s-deployment | Private AKS runtime |
| DEP-02 | BU app VMs | CMP-02 | prod | public_cloud | public_cloud_region | INF-12 | vm | 2 | us-vm-deployment | |
| DEP-03 | BU database | CMP-03 | prod | public_cloud | public_cloud_region | INF-13 | serverless | 1 | us-db-deployment | Hosting model TBD |
| DEP-04 | Common AKS workload | CMP-04 | prod | public_cloud | public_cloud_region | INF-14 | container | 2 | common-k8s-deployment | Private AKS runtime |
| DEP-05 | Shared services | CMP-05 | prod | public_cloud | public_cloud_region | INF-15 | container | 2 | shared-deployment | Runtime TBD |
| DEP-06 | Storage private endpoint | CMP-06 | prod | public_cloud | public_cloud_region | INF-16 | serverless | 1 | storage-deployment | |
| DEP-07 | AP AKS workload | CMP-07 | prod | public_cloud | public_cloud_region | INF-17 | container | 2 | ap-k8s-deployment | Private AKS runtime |
| DEP-08 | AP app | CMP-08 | prod | public_cloud | public_cloud_region | INF-18 | vm | 2 | ap-app-deployment | |
| DEP-09 | AP database | CMP-09 | prod | public_cloud | public_cloud_region | INF-19 | serverless | 1 | ap-db-deployment | Hosting model TBD |
| DEP-10 | US boundary | CMP-10 | prod | private_cloud | data_center | INF-20 | vm | 1 | us-boundary-deployment | Existing |
| DEP-11 | Japan boundary | CMP-11 | prod | private_cloud | data_center | INF-21 | vm | 1 | jp-boundary-deployment | Existing |

## R5 - Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | Internet to ingress | internet | CMP-01 | HTTPS | 443 | OAuth2_AuthorizationCode | TLS1.3 | 否 | INF-10 | AUTH-01 entry |
| FLOW-02 | Ingress to VM app | internet | CMP-02 | HTTPS | 443 | OAuth2_AuthorizationCode | TLS1.3 | 否 | INF-10 | Alternate backend |
| FLOW-03 | BU workload to DB | CMP-01 | CMP-03 | TCP | TBD | ManagedIdentity | TLS1.3 | 否 | INF-06 | Engine and port TBD |
| FLOW-04 | VM app to DB | CMP-02 | CMP-03 | TCP | TBD | ManagedIdentity | TLS1.3 | 否 | INF-06 | Engine and port TBD |
| FLOW-05 | BU workload to shared services | CMP-01 | CMP-05 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | INF-06 | Forced hub inspection |
| FLOW-06 | Common workload to shared services | CMP-04 | CMP-05 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | - | Shared-spoke local |
| FLOW-07 | Shared services to storage | CMP-05 | CMP-06 | HTTPS | 443 | ManagedIdentity | TLS1.3 | 否 | - | Private endpoint |
| FLOW-08 | AP workload to DB | CMP-07 | CMP-09 | TCP | TBD | ManagedIdentity | TLS1.3 | 否 | INF-08 | Engine and port TBD |
| FLOW-09 | AP app to DB | CMP-08 | CMP-09 | TCP | TBD | ManagedIdentity | TLS1.3 | 否 | INF-08 | Engine and port TBD |
| FLOW-10 | US corporate integration | CMP-10 | CMP-05 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | INF-07, INF-06 | Hybrid inspected route |
| FLOW-11 | Japan corporate integration | CMP-11 | CMP-07 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | INF-09, INF-08 | Hybrid inspected route |

## R6 - Infra links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | East US hub to BU spoke | INF-01 | INF-02 | vnet_peering | TBD | 是 | Microsoft | UDR via INF-06 |
| LNK-02 | East US hub to common spoke | INF-01 | INF-03 | vnet_peering | TBD | 是 | Microsoft | UDR via INF-06 |
| LNK-03 | Japan hub to AP spoke | INF-04 | INF-05 | vnet_peering | TBD | 是 | Microsoft | UDR via INF-08 |
| LNK-04 | Azure-US-ER primary circuit | INF-01 | INF-20 | expressroute | TBD | 是 | Carrier A | Primary dedicated circuit |
| LNK-05 | Azure-US-ER secondary circuit | INF-01 | INF-20 | expressroute | TBD | 是 | Carrier B | Secondary dedicated circuit |
| LNK-06 | MPLS | INF-01 | INF-20 | mpls | TBD | 是 | Carrier | Backup WAN |
| LNK-07 | Internet VPN | INF-01 | INF-20 | vpn | TBD | 是 | Carrier | Backup VPN |
| LNK-08 | Azure-JP-ER primary circuit | INF-04 | INF-21 | expressroute | TBD | 是 | Carrier C | Primary dedicated circuit |

## R7 - Auth

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | Customer entry | user | CMP-01 | INF-10 | OIDC | RBAC | 是 | External identity provider remains TBD |
