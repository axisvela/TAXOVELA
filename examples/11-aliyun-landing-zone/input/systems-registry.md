# Systems Registry — Order Service Platform (ORD) on Alibaba Cloud

Single source of truth for every system / service name in this example.

- **参考图不做脱敏**：`input/diagrams/` 下的参考图保留原名。
- **文档只引用编号**：`prompt.md`、`documents/`、`README.md`、`config.yaml`
  中所有系统/服务均以类型化编号引用（`INF-` 基础设施、`APP-` 系统、
  `CMP-` 组件，以及 `DEP`/`FLOW`/`LNK`/`AUTH` 派生层），不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **建模规则**：中心 VPC 与业务 VPC 各自是一个 region，vSwitch 是其中的 zone；
  Anti-DDoS、WAF、SLB、云防火墙、NAT 网关、CEN、KMS 凭据管家、IdP 是 `INF` L4 节点；
  ACK 是组件的 runtime，不单独作为组件。

## R1 — Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | Alibaba Cloud central VPC | iaas_vpc_vnet | public_cloud | prod_network | - | CN | ali-central-vpc | Hub VPC owned by the central account |
| INF-02 | Edge vSwitch | subnet | public_cloud | dmz | INF-01 | CN | ali-edge-vswitch | Public edge vSwitch, AZ-A |
| INF-03 | Shared services vSwitch | subnet | public_cloud | prod_network | INF-01 | CN | ali-shared-vswitch | Inspection, egress, CEN |
| INF-04 | Alibaba Cloud business VPC | iaas_vpc_vnet | public_cloud | prod_network | - | CN | ali-business-vpc | Workload VPC |
| INF-05 | Application vSwitch (AZ-A) | subnet | public_cloud | prod_network | INF-04 | CN | ali-app-vswitch-a | Primary application zone |
| INF-06 | Application vSwitch (AZ-B) | subnet | public_cloud | prod_network | INF-04 | CN | ali-app-vswitch-b | Second availability zone |
| INF-07 | Data vSwitch (AZ-A) | subnet | public_cloud | prod_network | INF-04 | CN | ali-data-vswitch | Database and object storage |
| INF-08 | Primary DC | data_center | private_cloud | prod_network | - | CN | dc-primary | Existing corporate boundary |
| INF-09 | Primary DC Intranet | network_zone | private_cloud | prod_network | INF-08 | CN | dc-intranet | ERP and identity |
| INF-10 | Anti-DDoS | security_gateway | public_cloud | dmz | INF-02 | CN | ali-ddos | Traffic scrubbing |
| INF-11 | Web application firewall | waf | public_cloud | dmz | INF-02 | CN | ali-waf | OWASP rules, rate limiting |
| INF-12 | Server load balancer | load_balancer | public_cloud | dmz | INF-02 | CN | ali-slb | ALB/SLB in front of the app vSwitches |
| INF-13 | Cloud firewall | firewall | public_cloud | prod_network | INF-03 | CN | ali-cloud-firewall | East-west inspection |
| INF-14 | NAT gateway | router | public_cloud | prod_network | INF-03 | CN | ali-nat | Only egress path |
| INF-15 | Cloud Enterprise Network | router | public_cloud | prod_network | INF-03 | CN | ali-cen | Cross-VPC and hybrid hub |
| INF-16 | Log service | logging_service | public_cloud | prod_network | INF-03 | CN | ali-sls | Central audit collection |
| INF-17 | KMS secret manager | key_management | public_cloud | prod_network | INF-07 | CN | ali-kms | Database passwords and rotation |
| INF-18 | Enterprise IdP | identity_provider | private_cloud | prod_network | INF-09 | CN | enterprise-idp | Federated to RAM SSO |

## R2 — Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | Order service platform | new | org_it | Alibaba Cloud | order-service-platform | Runs in the business VPC |
| APP-02 | On-premises ERP landscape | existing | org_it | - | erp-landscape | System of record, black box |

## R3 — Components / services

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | Order service | APP-01 | api | service | be | backend_service | - | order-service | Primary instance, AZ-A |
| CMP-02 | Order service (AZ-B) | APP-01 | api | service | be | backend_service | - | order-service-b | Second availability zone |
| CMP-03 | Order database | APP-01 | data | component | db | database | KMS | order-database | Private endpoint only |
| CMP-04 | Object storage bucket | APP-01 | data | component | db | object_storage | KMS | order-archive | Document archive |
| CMP-05 | ERP integration boundary | APP-02 | - | component | ip | integration_service | - | erp-boundary | Only boundary into the ERP zone |
| CMP-06 | ERP core | APP-02 | - | component | be | application_service | AES-256 | erp-core | Read by the boundary service only |

## R4 — Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|-----------|--------------|--------|----------|------|
| DEP-01 | Order service pods (AZ-A) | CMP-01 | prod | public_cloud | public_cloud_region | INF-05 | container | 2 | order-deploy-a | ACK, AZ-A |
| DEP-02 | Order service pods (AZ-B) | CMP-02 | prod | public_cloud | public_cloud_region | INF-06 | container | 2 | order-deploy-b | ACK, AZ-B |
| DEP-03 | PolarDB instance | CMP-03 | prod | public_cloud | public_cloud_region | INF-07 | serverless | - | db-deploy | KMS-encrypted |
| DEP-04 | OSS bucket | CMP-04 | prod | public_cloud | public_cloud_region | INF-07 | serverless | - | oss-deploy | KMS-encrypted |
| DEP-05 | ERP boundary service | CMP-05 | prod | private_cloud | data_center | INF-09 | container | 2 | boundary-onprem | Internal K8s |
| DEP-06 | ERP core | CMP-06 | prod | private_cloud | data_center | INF-09 | physical | 1 | erp-onprem | System of record |

## R5 — Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | order service -> database | CMP-01 | CMP-03 | JDBC | 3306 | UserPassword | TLS1.3 | 否 | - | Credentials from INF-17 |
| FLOW-02 | order service AZ-B -> database | CMP-02 | CMP-03 | JDBC | 3306 | UserPassword | TLS1.3 | 否 | - | Cross-AZ inside the business VPC |
| FLOW-03 | order service -> archive | CMP-01 | CMP-04 | HTTPS | 443 | IAM_Role | TLS1.3 | 否 | - | RAM role with STS token |
| FLOW-04 | order service -> ERP boundary | CMP-01 | CMP-05 | HTTPS | 443 | ClientCertificate | IPSec | 否 | INF-13 INF-15 | Via CEN and Express Connect |
| FLOW-05 | ERP boundary -> ERP core | CMP-05 | CMP-06 | JDBC | 1433 | UserPassword | TLS1.2 | 否 | - | Only reader of the ERP schema |

## R6 — Infra network links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | Business VPC -> Central VPC | INF-04 | INF-01 | vpc_peering | TBD | 是 | Cloud Platform | Attached through CEN, not a direct peering |
| LNK-02 | Primary DC -> Central VPC | INF-08 | INF-01 | leased_line | TBD | IPSec | InfraSec | Express Connect with IPsec |

## R7 — Auth

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | Internal employee sign-in | user | CMP-01 | INF-18 | SAML2 | RBAC | 是 | Federated to RAM SSO; privilege policy TBD |
| AUTH-02 | Workload access to storage | application | CMP-04 | INF-18 | OIDC | RBAC | - | RAM role assumed with STS tokens |
