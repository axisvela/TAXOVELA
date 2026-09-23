# Systems Registry — Data Agent Platform (Hybrid)

Single source of truth for every system / service name in this example.

- **参考图不做脱敏**：`input/diagrams/reference-architecture.png` 保留原名。
- **文档只引用编号**：`prompt.md`、`requirements.md`、`README.md`、`config.yaml`
  中所有系统/服务均以类型化编号引用（`INF-` 基础设施、`APP-` 系统、
  `CMP-` 组件，以及 `DEP`/`FLOW`/`LNK`/`AUTH` 派生层），不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **范围标记**：本表默认全部纳入设计范围；若某系统有意不纳入，在其「备注」列写上 `OUT-OF-SCOPE`，`registry_check` 便不再要求 `prompt.md` 引用它。
- **手动脱敏流程**：直接修改下表「文档用名」列即可；编号不变，所有引用自动跟随，无需全局替换。

The reference diagram itself is NOT scrubbed — that is why 参考图原名 keeps originals.

## R1 — Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | dc-cn-primary | data_center | private_cloud | prod_network | - | CN | cn-primary-dc | three-tier private DC |
| INF-02 | dc-cn-primary App Zone | network_zone | private_cloud | prod_network | INF-01 | CN | cn-app-zone | agent runtime zone |
| INF-03 | dc-cn-primary DB Zone | network_zone | private_cloud | prod_network | INF-01 | CN | cn-db-zone | data zone, App Zone access only |
| INF-04 | dc-cn-primary DMZ | network_zone | private_cloud | dmz | INF-01 | CN | cn-dmz | inbound path TBD |
| INF-05 | ADFS | identity_provider | private_cloud | prod_network | INF-01 | CN | adfs | internal STS fallback |
| INF-06 | Azure Global Identity boundary | saas | saas | prod_network | - | TBD | azure-identity-boundary | cloud identity service boundary |
| INF-07 | Microsoft Entra ID | identity_provider | saas | prod_network | INF-06 | TBD | entra-id | primary user IdP |
| INF-08 | azure-eastus | iaas_vpc_vnet | public_cloud | prod_network | - | US | azure-us | governed EDW region |
| INF-09 | azure-eastus2 | iaas_vpc_vnet | public_cloud | prod_network | - | US | azure-us2 | model service region, TBD |
| INF-10 | Office Network | office_network | office | office_network | - | CN | office-net | administrator access |

The internal container platform (参考图原名 `Earth K8S`) is not an infra node: it
carries no network boundary of its own, so it is modelled as the `runtime` of
the components it hosts and, in the diagram, as the App Zone's platform frame.

## R2 — Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | Data Agent Platform (GDA) | new | org_it | - | data-agent-platform | private-DC runtime, new build |
| APP-02 | Magellan EDW Data | existing | org_it | Databricks | magellan-edw | governed data source, black box |
| APP-03 | LLM Gateway (overseas / China pool) | existing | org_it | - | model-gateway-service | model service boundary, black box |

## R3 — Components / services

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | GDA Gateway + Dashboard UI (nginx) | APP-01 | web | component | fe | web_frontend | - | gda-gateway | static hosting, API proxy, SSE client |
| CMP-02 | GDA Agent API, SSE, Agent Tools (Node.js) | APP-01 | agent | service | be | ai_agent | - | gda-agent-api | agent runtime with streaming |
| CMP-03 | GDA Scheduler Worker (Node.js) | APP-01 | ops | service | be | backend_service | - | gda-scheduler-worker | alerts and digests |
| CMP-04 | PostgreSQL | APP-01 | db | component | db | database | TBD | postgresql | App Zone access only |
| CMP-05 | Nginx outbound gateway (Rocky 9.8 VM) | APP-01 | egress | component | ip | integration_service | - | outbound-gateway | sole private-DC to Azure egress |
| CMP-06 | Magellan EDW boundary | APP-02 | - | component | ip | integration_service | - | edw-boundary | governed namespace access |
| CMP-07 | LLM Gateway boundary | APP-03 | - | component | ip | integration_service | - | model-boundary | private-endpoint-only access |

## R4 — Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|-----------|--------------|--------|----------|------|
| DEP-01 | GDA gateway pods | CMP-01 | prod | private_cloud | data_center | INF-02 | container | 2 | gateway-cn | internal K8s |
| DEP-02 | Agent API pods | CMP-02 | prod | private_cloud | data_center | INF-02 | container | 2 | agent-api-cn | internal K8s |
| DEP-03 | scheduler worker pods | CMP-03 | prod | private_cloud | data_center | INF-02 | container | 1 | worker-cn | internal K8s |
| DEP-04 | PostgreSQL instance | CMP-04 | prod | private_cloud | data_center | INF-03 | vm | 1 | postgres-cn | HA model TBD |
| DEP-05 | outbound gateway VM | CMP-05 | prod | private_cloud | data_center | INF-02 | vm | 1 | egress-cn | Rocky Linux 9.8 |
| DEP-06 | EDW access boundary | CMP-06 | prod | public_cloud | public_cloud_region | INF-08 | serverless | - | edw-us | provider-managed |
| DEP-07 | model gateway boundary | CMP-07 | prod | public_cloud | public_cloud_region | INF-09 | serverless | - | model-us | private endpoint only |

## R5 — Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | office client → gateway | internet | CMP-01 | HTTPS | 443 | none | TLS1.2 | 否 | INF-04 | office network only; inbound path TBD; user auth = AUTH-01 |
| FLOW-02 | gateway → agent API | CMP-01 | CMP-02 | HTTPS_SSE | 443 | none | TLS1.2 | 否 | - | forwarded user token |
| FLOW-03 | gateway → scheduler worker | CMP-01 | CMP-03 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.2 | 否 | - | mechanism TBD; platform default |
| FLOW-04 | agent API → PostgreSQL | CMP-02 | CMP-04 | PostgreSQL | 5432 | UserPassword | TLS1.2 | 否 | - | creds in K8s Secret |
| FLOW-05 | scheduler worker → PostgreSQL | CMP-03 | CMP-04 | PostgreSQL | 5432 | UserPassword | TLS1.2 | 否 | - | creds in K8s Secret |
| FLOW-06 | agent API → outbound gateway | CMP-02 | CMP-05 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.2 | 否 | - | mandatory egress hop; mechanism TBD |
| FLOW-07 | outbound gateway → EDW boundary | CMP-05 | CMP-06 | HTTPS | 443 | mTLS | TLS1.2 | 是 | INF-08 | governed namespaces only; credential TBD |
| FLOW-08 | outbound gateway → model boundary | CMP-05 | CMP-07 | HTTPS | 443 | ApiKey | TLS1.2 | 是 | INF-09 | private endpoint only; delivery TBD |

## R6 — Infra network links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | dc-cn-primary → azure-eastus | INF-01 | INF-08 | vpn | TBD | 是 | TBD | private connectivity type TBD; VPN assumed until the carrier is selected |
| LNK-02 | dc-cn-primary → azure-eastus2 | INF-01 | INF-09 | vpn | TBD | 是 | TBD | private connectivity type TBD; VPN assumed until the carrier is selected |

## R7 — Auth

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | Entra ID sign-in | user | CMP-01 | INF-07 | OIDC | RBAC | 是 | primary path; tenant and role claims TBD |
| AUTH-02 | ADFS federation | user | CMP-01 | INF-05 | SAML2 | RBAC | 是 | internal STS fallback; role mapping TBD |
