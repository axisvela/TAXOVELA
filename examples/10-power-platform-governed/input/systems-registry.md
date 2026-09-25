# Systems Registry — Expense Approval App (EXP) on Power Platform

Single source of truth for every system / service name in this example.

- **参考图不做脱敏**：`input/diagrams/` 下的参考图保留原名。
- **文档只引用编号**：`prompt.md`、`documents/`、`README.md`、`config.yaml`
  中所有系统/服务均以类型化编号引用（`INF-` 基础设施、`APP-` 系统、
  `CMP-` 组件，以及 `DEP`/`FLOW`/`LNK`/`AUTH` 派生层），不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **建模规则**：SaaS 租户按黑盒建模——租户是容器、环境是 zone，客户侧网络分区
  不得画进租户；Entra ID、DLP 策略、企业密钥库按 `INF` L4 节点建模；
  本地数据网关按边界组件建模，是公司侧唯一入口。

## R1 — Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | Power Platform tenant | saas | saas | prod_network | - | SG | pp-tenant | Microsoft-operated; no customer network inside |
| INF-02 | Production environment | subnet | saas | prod_network | INF-01 | SG | pp-prod-env | Managed environment |
| INF-03 | Governance and identity | subnet | saas | prod_network | INF-01 | SG | pp-governance | DLP and identity |
| INF-04 | Entra ID | identity_provider | saas | prod_network | INF-03 | SG | entra-id | Only identity source |
| INF-05 | DLP policy | policy_service | saas | prod_network | INF-03 | SG | pp-dlp | Connector classification |
| INF-06 | Primary DC | data_center | private_cloud | prod_network | - | CN | dc-primary | Existing corporate boundary |
| INF-07 | Primary DC DMZ | network_zone | private_cloud | dmz | INF-06 | CN | dc-dmz | Only inbound termination point |
| INF-08 | Boundary firewall | security_gateway | private_cloud | dmz | INF-07 | CN | dc-firewall | Deny by default |
| INF-09 | Primary DC App Zone | network_zone | private_cloud | prod_network | INF-06 | CN | dc-app-zone | Application and data |
| INF-10 | Enterprise vault | key_management | private_cloud | prod_network | INF-09 | CN | enterprise-vault | HSM-backed, automated rotation |

## R2 — Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | Expense approval app | new | biz_owned | Microsoft | expense-approval-app | Business-authored on Power Platform |
| APP-02 | Expense backend | existing | org_it | - | expense-backend | Company API and database |

## R3 — Components / services

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | Expense approval app | APP-01 | ui | component | fe | application_service | - | expense-app | Canvas app, standard connectors only |
| CMP-02 | Approval flow | APP-01 | flow | service | be | backend_service | - | approval-flow | Calls the company backend through the gateway |
| CMP-03 | Dataverse table | APP-01 | state | component | db | database | Managed | dataverse-state | Approval state only, no restricted data |
| CMP-04 | On-premises data gateway | APP-02 | - | component | ip | integration_service | - | onprem-gateway | Sole inbound path from Power Platform |
| CMP-05 | Expense service | APP-02 | - | service | be | backend_service | - | expense-service | Company API; not in the gateway's direct path |
| CMP-06 | Expense database | APP-02 | - | component | db | database | AES-256 | expense-db | Reached by the gateway's service account only |

## R4 — Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|-----------|--------------|--------|----------|------|
| DEP-01 | Expense app | CMP-01 | prod | saas | saas | INF-02 | serverless | - | app-pp | Managed environment |
| DEP-02 | Approval flow | CMP-02 | prod | saas | saas | INF-02 | serverless | - | flow-pp | Managed environment |
| DEP-03 | Dataverse tables | CMP-03 | prod | saas | saas | INF-02 | serverless | - | dataverse-pp | Environment-scoped |
| DEP-04 | Gateway host | CMP-04 | prod | private_cloud | data_center | INF-07 | vm | 2 | gateway-onprem | Hardened host in the DMZ |
| DEP-05 | Expense service | CMP-05 | prod | private_cloud | data_center | INF-09 | container | 2 | service-onprem | Internal K8s |
| DEP-06 | Expense database | CMP-06 | prod | private_cloud | data_center | INF-09 | physical | 1 | db-onprem | AES-256 |

## R5 — Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | app -> flow | CMP-01 | CMP-02 | HTTPS | 443 | none | TLS1.3 | 否 | - | User context forwarded; sign-in declared in AUTH-01 |
| FLOW-02 | flow -> Dataverse | CMP-02 | CMP-03 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | - | Approval state only |
| FLOW-03 | flow -> gateway | CMP-02 | CMP-04 | HTTPS | 443 | UserPassword | TLS1.2 | 否 | - | Scoped service account from the vault |
| FLOW-04 | gateway -> database | CMP-04 | CMP-06 | JDBC | 1433 | UserPassword | TLS1.2 | 否 | INF-08 | Least-privilege account; only client of this schema |

## R6 — Infra network links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | Power Platform tenant -> Primary DC DMZ gateway relay | INF-01 | INF-07 | internet | TBD | TLS1.2 | Microsoft / InfraSec | Outbound-only relay from the tenant; no inbound listener and no private circuit |

## R7 — Auth

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | Entra ID sign-in | user | CMP-01 | INF-04 | OIDC | RBAC | 是 | Conditional access; privileged roles via PIM |
| AUTH-02 | Gateway relay | application | CMP-04 | INF-04 | OIDC | RBAC | - | Service account scoped to the expense schema |
