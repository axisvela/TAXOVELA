# Systems Registry — Analytics API (ANA) on Google Cloud

Single source of truth for every system / service name in this example.

- **参考图不做脱敏**：`input/diagrams/` 下的参考图保留原名。
- **文档只引用编号**：`prompt.md`、`documents/`、`README.md`、`config.yaml`
  中所有系统/服务均以类型化编号引用（`INF-` 基础设施、`APP-` 系统、
  `CMP-` 组件，以及 `DEP`/`FLOW`/`LNK`/`AUTH` 派生层），不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **范围标记**：默认全部纳入设计范围；有意不纳入的行，在「备注」列写上 `OUT-OF-SCOPE`。
- **建模规则**：Shared VPC 中网络边界是 **host project**，service project 只承载工作负载，
  不为它单独画 VPC；Cloud Armor / LB / NAT / Interconnect / Secret Manager / IdP 是 `INF` L4 节点，
  GKE 是组件的 runtime（不建 INF 节点）。

## R1 — Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | Google Cloud host project | iaas_vpc_vnet | public_cloud | prod_network | - | TBD | gcp-host-project | Shared VPC host; region TBD |
| INF-02 | Shared ingress subnet | subnet | public_cloud | dmz | INF-01 | TBD | gcp-ingress-subnet | Public entry, WAF and LB only |
| INF-03 | Shared egress subnet | subnet | public_cloud | prod_network | INF-01 | TBD | gcp-egress-subnet | Cloud NAT and Interconnect |
| INF-04 | Private runtime subnet | subnet | public_cloud | prod_network | INF-01 | TBD | gcp-runtime-subnet | GKE private cluster |
| INF-05 | Private data subnet | subnet | public_cloud | prod_network | INF-01 | TBD | gcp-data-subnet | Warehouse and staging |
| INF-06 | Primary DC | data_center | private_cloud | prod_network | - | CN | dc-primary | Existing corporate boundary |
| INF-07 | Primary DC Intranet | network_zone | private_cloud | prod_network | INF-06 | CN | dc-intranet | ERP and identity |
| INF-08 | Cloud Armor | waf | public_cloud | dmz | INF-02 | TBD | gcp-cloud-armor | OWASP rules, rate limiting |
| INF-09 | Global HTTPS load balancer | load_balancer | public_cloud | dmz | INF-02 | TBD | gcp-https-lb | Global external LB |
| INF-10 | Cloud NAT | router | public_cloud | prod_network | INF-03 | TBD | gcp-cloud-nat | Only egress path |
| INF-11 | Cloud Interconnect | vpn_gateway | public_cloud | prod_network | INF-03 | TBD | gcp-interconnect | Private path to the DC with IPSec |
| INF-12 | Secret Manager | key_management | public_cloud | prod_network | INF-05 | TBD | gcp-secret-manager | Runtime credentials |
| INF-13 | Enterprise directory | identity_provider | private_cloud | prod_network | INF-07 | CN | enterprise-directory | Federated to Cloud Identity |

## R2 — Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | Analytics API platform | new | org_it | Google Cloud | analytics-api-platform | Query API and loader |
| APP-02 | On-premises ERP landscape | existing | org_it | - | erp-landscape | System of record, black box |

## R3 — Components / services

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | Analytics API | APP-01 | api | service | be | backend_service | - | analytics-api | Serves internal consumers |
| CMP-02 | Analytics worker | APP-01 | loader | service | be | backend_service | - | analytics-worker | Ingests ERP extracts |
| CMP-03 | BigQuery warehouse | APP-01 | data | component | db | data_warehouse | CMEK | bigquery-warehouse | Inside the VPC-SC perimeter |
| CMP-04 | Cloud Storage stage | APP-01 | data | component | db | object_storage | CMEK | gcs-stage | Staging bucket for extracts |
| CMP-05 | ERP extract service | APP-02 | - | component | ip | integration_service | - | erp-extract | Only boundary into the ERP zone |
| CMP-06 | ERP core | APP-02 | - | component | be | application_service | AES-256 | erp-core | Read by the extract service only |

## R4 — Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|-----------|--------------|--------|----------|------|
| DEP-01 | Analytics API pods | CMP-01 | prod | public_cloud | public_cloud_region | INF-04 | container | 2 | api-gcp | GKE private cluster |
| DEP-02 | Analytics worker pods | CMP-02 | prod | public_cloud | public_cloud_region | INF-04 | container | 2 | worker-gcp | GKE private cluster |
| DEP-03 | BigQuery dataset | CMP-03 | prod | public_cloud | public_cloud_region | INF-05 | serverless | - | bigquery-gcp | Managed; CMEK |
| DEP-04 | Cloud Storage bucket | CMP-04 | prod | public_cloud | public_cloud_region | INF-05 | serverless | - | gcs-gcp | Managed; CMEK |
| DEP-05 | ERP extract service | CMP-05 | prod | private_cloud | data_center | INF-07 | container | 2 | extract-onprem | Internal K8s |
| DEP-06 | ERP core | CMP-06 | prod | private_cloud | data_center | INF-07 | physical | 1 | erp-onprem | System of record |

## R5 — Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | internet -> analytics API | internet | CMP-01 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | INF-08 INF-09 | Cloud Armor and LB are entry hops |
| FLOW-02 | analytics API -> warehouse | CMP-01 | CMP-03 | gRPC | 443 | IAM_Role | TLS1.3 | 否 | - | Inside the perimeter |
| FLOW-03 | worker -> stage bucket | CMP-02 | CMP-04 | HTTPS | 443 | IAM_Role | TLS1.3 | 否 | - | Least-privilege bucket role |
| FLOW-04 | worker -> ERP extract | CMP-02 | CMP-05 | HTTPS | 443 | ClientCertificate | IPSec | 是 | INF-11 | Minimized and classified extracts |
| FLOW-05 | ERP extract -> ERP core | CMP-05 | CMP-06 | JDBC | 5432 | UserPassword | TLS1.3 | 否 | - | Single reader of the ERP schema |

## R6 — Infra network links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | Primary DC -> Google Cloud host project | INF-06 | INF-01 | leased_line | TBD | IPSec | InfraSec | Cloud Interconnect; no direct database replication |

## R7 — Auth

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | Internal employee sign-in | user | CMP-01 | INF-13 | SAML2 | RBAC | 是 | Federated to Cloud Identity; role mapping TBD |
| AUTH-02 | Partner API sign-in | user | CMP-01 | INF-13 | OIDC | RBAC | 是 | OAuth2.0 authorization code with PKCE; scopes TBD |
