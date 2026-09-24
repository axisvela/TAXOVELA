# Systems Registry — Supply-Chain Order Platform (OSP)

Single source of truth for every entity name in this example (req/v2 model).

- **参考图不做脱敏**：`input/diagrams/reference-architecture.png` 保留原名。
- **文档只引用编号**：`prompt.md`、`requirements.md`、`README.md`、`config.yaml`
  中所有实体均以类型化编号引用，不直接写名字。本注册表是唯一出现具名实体的文件。
- **编号含义（req/v2）**：`INF` 承载/网络节点、`APP` 应用系统、`CMP` 组件/服务、
  `STK` 组件-技术栈、`DEP` 部署、`FLOW` 组件通信、`LNK` 基础设施链路、`AUTH` 用户/入口认证。
- **设备归属**：F5、WAF、Earth Router、ADFS 等网络/安全设备是 `INF` 节点，不是 `CMP` 组件。
- **对称双区**：CN 与 NA 是同一套栈的双活镜像 —— **逻辑组件只有一个 `CMP-nn`，
  每个区域一条 `DEP-nn`**（例如 Order Creation 只有 CMP-03，但有 DEP-03 与 DEP-13）。
- **范围标记**：清单型实体默认全部纳入；有意排除的在其「备注」列写 `OUT-OF-SCOPE`。
  派生行（`DEP`/`FLOW`/`LNK`/`AUTH`）不参与 `prompt.md` 覆盖检查。
- **手动脱敏流程**：直接修改下表「文档用名」列即可；编号不变，所有引用自动跟随。

## R1 — Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | dc-cn-primary | data_center | private_cloud | prod_network | - | CN | cn-primary-dc | CN primary DC, three-tier |
| INF-02 | dc-cn-primary App Zone | network_zone | private_cloud | prod_network | INF-01 | CN | cn-app-zone | CN app zone |
| INF-03 | dc-cn-primary DB Zone | network_zone | private_cloud | prod_network | INF-01 | CN | cn-db-zone | CN DB zone |
| INF-04 | dc-us | data_center | private_cloud | prod_network | - | US | na-dc | NA DC, multi-zone |
| INF-05 | NA-PROD-INA-K8S | network_zone | private_cloud | prod_network | INF-04 | US | na-k8s-zone | NA Kubernetes zone |
| INF-06 | NA-PROD-INA-INTEGRATION | network_zone | private_cloud | prod_network | INF-04 | US | na-med-zone | NA mediation zone |
| INF-07 | NA-PROD-INA-SERVER | network_zone | private_cloud | prod_network | INF-04 | US | na-mw-zone | NA middleware zone |
| INF-08 | NA-PROD-INA-SAP | network_zone | private_cloud | prod_network | INF-04 | US | na-sap-zone | NA SAP zone |
| INF-09 | NA-PROD-INA-DB | network_zone | private_cloud | prod_network | INF-04 | US | na-db-zone | NA DB zone |
| INF-10 | dc-us-identity | data_center | private_cloud | prod_network | - | US | identity-dc | Identity DC |
| INF-11 | AWS US | iaas_vpc_vnet | public_cloud | prod_network | - | US | aws-region | AWS peer hosting |
| INF-12 | Azure US | iaas_vpc_vnet | public_cloud | prod_network | - | US | azure-region | Azure peer hosting |
| INF-13 | Office Network | office_network | office | office_network | - | CN | office-net | employee access |
| INF-14 | dc-cn-primary DMZ | network_zone | private_cloud | dmz | INF-01 | CN | cn-dmz | CN ingress DMZ |
| INF-15 | dc-us DMZ | network_zone | private_cloud | dmz | INF-04 | US | na-dmz | NA ingress DMZ |
| INF-16 | F5 (CN) | load_balancer | private_cloud | dmz | INF-14 | CN | cn-f5 | CN ingress |
| INF-17 | WAF (CN, optional) | waf | private_cloud | dmz | INF-14 | CN | cn-waf | optional |
| INF-18 | Earth Router (CN) | router | private_cloud | dmz | INF-14 | CN | cn-router | CN edge routing |
| INF-19 | F5 (NA) | load_balancer | private_cloud | dmz | INF-15 | US | na-f5 | NA ingress |
| INF-20 | WAF (NA, optional) | waf | private_cloud | dmz | INF-15 | US | na-waf | optional |
| INF-21 | Earth Router (NA) | router | private_cloud | dmz | INF-15 | US | na-router | NA edge routing |
| INF-22 | ADFS | identity_provider | private_cloud | prod_network | INF-10 | US | adfs | employee SSO |

## R2 — Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | Supply-Chain Order Platform | new | org_it | - | osp | active-active CN + NA |
| APP-02 | CN peer applications | existing | org_it | - | cn-peers | integration boundary only |
| APP-03 | AWS peer | existing | org_it | Amazon Web Services | aws-peer | event consumer |
| APP-04 | Azure peers | existing | org_it | Microsoft Azure | azure-peers | eComm + SaaS |
| APP-05 | SAP CN | existing | third_party | SAP | sap-cn | ECC + S4, Function/SLT |
| APP-06 | SAP NA | existing | third_party | SAP | sap-na | S4, Function/SLT |

## R3 — Components / services

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | scop-cn-web / osp-na-web (Nginx) | APP-01 | web | component | fe | web_frontend | - | web-tier | CN + NA |
| CMP-02 | Spring Cloud Gateway (LMP) | APP-01 | gateway | component | ip | api_gateway | - | gateway | CN + NA |
| CMP-03 | Order Creation | APP-01 | order | service | be | backend_service | - | order-creation | CN + NA |
| CMP-04 | Order Change | APP-01 | order | service | be | backend_service | - | order-change | CN + NA |
| CMP-05 | Data Distribution | APP-01 | order | service | be | backend_service | - | data-distribution | CN + NA |
| CMP-06 | Master Data | APP-01 | master | service | be | backend_service | - | master-data | CN + NA |
| CMP-07 | Order Inquiry | APP-01 | order | service | be | backend_service | - | order-inquiry | CN + NA |
| CMP-08 | Basic Operation | APP-01 | ops | service | be | backend_service | - | basic-operation | CN + NA |
| CMP-09 | Logging | APP-01 | ops | service | be | backend_service | - | logging-svc | CN + NA |
| CMP-10 | etc. | APP-01 | ops | service | be | backend_service | - | misc-svc | CN + NA |
| CMP-11 | APIM | APP-01 | integration | component | ip | api_gateway | - | apim | CN only |
| CMP-12 | WSO2 | APP-01 | integration | component | ip | integration_service | - | wso2 | CN only |
| CMP-13 | APIH | APP-01 | integration | component | ip | integration_service | - | apih | CN + NA mediation |
| CMP-14 | Kafka | APP-01 | messaging | component | mq | message_bus | - | kafka | CN + NA events |
| CMP-15 | RabbitMQ | APP-01 | messaging | component | mq | message_bus | - | rabbitmq | CN + NA |
| CMP-16 | Debezium | APP-01 | messaging | service | mq | data_integration | - | debezium | CN + NA CDC |
| CMP-17 | ES HA GRP | APP-01 | search | component | db | database | - | es-ha | CN + NA |
| CMP-18 | Redis HA GRP | APP-01 | cache | component | db | cache | - | redis-ha | CN + NA |
| CMP-19 | MySQL HA GRP | APP-01 | db | component | db | database | AES-256 | mysql-ha | CN only |
| CMP-20 | PostgreSQL HA GRP | APP-01 | db | component | db | database | AES-256 | postgres-ha | CN + NA |
| CMP-21 | SQLServer HA GRP | APP-01 | db | component | db | database | AES-256 | sqlserver-ha | CN + NA |
| CMP-22 | ERPS（ERP service） | APP-01 | na-backend | service | be | backend_service | - | erps | NA only |
| CMP-23 | LGS(logistics gateway service)-NA | APP-01 | na-backend | service | be | backend_service | - | lgs-na | NA only |
| CMP-24 | IBS(Installbase service) | APP-01 | na-backend | service | be | backend_service | - | ibs | NA only |
| CMP-25 | eComm-order-platform | APP-02 | - | component | ip | integration_service | - | ecomm-order-platform | CN peer boundary |
| CMP-26 | SOS(sales order service)-PRC | APP-02 | - | component | ip | integration_service | - | sos-prc | CN peer boundary |
| CMP-27 | CFOS(customer order fullfillment service)-PRC | APP-02 | - | component | ip | integration_service | - | cfos-prc | CN peer boundary |
| CMP-28 | CFOS(customer order fullfillment service)-AP | APP-02 | - | component | ip | integration_service | - | cfos-ap | CN peer boundary |
| CMP-29 | SSCS(Service supply chain service)-AP | APP-02 | - | component | ip | integration_service | - | sscs-ap | CN peer boundary |
| CMP-30 | SOS(sales order service)-ROW | APP-03 | - | component | ip | integration_service | - | sos-row | AWS peer boundary |
| CMP-31 | eComm-platform | APP-04 | - | component | ip | integration_service | - | ecomm-platform | Azure peer boundary |
| CMP-32 | D365 | APP-04 | - | component | ip | integration_service | - | d365 | Azure SaaS boundary |
| CMP-33 | ECC-CN (Function + SLT) | APP-05 | - | component | ip | integration_service | - | ecc-cn | SAP CN boundary |
| CMP-34 | S4-CN (Function + SLT) | APP-05 | - | component | ip | integration_service | - | s4-cn | SAP CN boundary |
| CMP-35 | S4-NA (Function + SLT) | APP-06 | - | component | ip | integration_service | - | s4-na | SAP NA boundary |

## R4 — Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|------------|--------------|--------|----------|------|
| DEP-01 | CN web tier | CMP-01 | prod | private_cloud | data_center | INF-02 | container | 2 | web-cn | CN |
| DEP-02 | NA web tier | CMP-01 | prod | private_cloud | data_center | INF-05 | container | 2 | web-na | NA |
| DEP-03 | CN gateway | CMP-02 | prod | private_cloud | data_center | INF-02 | container | 2 | gw-cn | CN |
| DEP-04 | NA gateway | CMP-02 | prod | private_cloud | data_center | INF-05 | container | 2 | gw-na | NA |
| DEP-05 | CN order creation | CMP-03 | prod | private_cloud | data_center | INF-02 | container | 2 | oc-cn | CN |
| DEP-06 | NA order creation | CMP-03 | prod | private_cloud | data_center | INF-05 | container | 2 | oc-na | NA |
| DEP-07 | CN order change | CMP-04 | prod | private_cloud | data_center | INF-02 | container | 2 | och-cn | CN |
| DEP-08 | NA order change | CMP-04 | prod | private_cloud | data_center | INF-05 | container | 2 | och-na | NA |
| DEP-09 | CN data distribution | CMP-05 | prod | private_cloud | data_center | INF-02 | container | 2 | dd-cn | CN |
| DEP-10 | NA data distribution | CMP-05 | prod | private_cloud | data_center | INF-05 | container | 2 | dd-na | NA |
| DEP-11 | CN master data | CMP-06 | prod | private_cloud | data_center | INF-02 | container | 2 | md-cn | CN |
| DEP-12 | NA master data | CMP-06 | prod | private_cloud | data_center | INF-05 | container | 2 | md-na | NA |
| DEP-13 | CN order inquiry | CMP-07 | prod | private_cloud | data_center | INF-02 | container | 2 | oi-cn | CN |
| DEP-14 | NA order inquiry | CMP-07 | prod | private_cloud | data_center | INF-05 | container | 2 | oi-na | NA |
| DEP-15 | CN basic operation | CMP-08 | prod | private_cloud | data_center | INF-02 | container | 2 | bo-cn | CN |
| DEP-16 | NA basic operation | CMP-08 | prod | private_cloud | data_center | INF-05 | container | 2 | bo-na | NA |
| DEP-17 | CN logging | CMP-09 | prod | private_cloud | data_center | INF-02 | container | 2 | log-cn | CN |
| DEP-18 | NA logging | CMP-09 | prod | private_cloud | data_center | INF-05 | container | 2 | log-na | NA |
| DEP-19 | CN misc service | CMP-10 | prod | private_cloud | data_center | INF-02 | container | 2 | misc-cn | CN |
| DEP-20 | NA misc service | CMP-10 | prod | private_cloud | data_center | INF-05 | container | 2 | misc-na | NA |
| DEP-21 | CN APIM | CMP-11 | prod | private_cloud | data_center | INF-02 | container | 2 | apim-cn | CN only |
| DEP-22 | CN WSO2 | CMP-12 | prod | private_cloud | data_center | INF-02 | container | 2 | wso2-cn | CN only |
| DEP-23 | CN APIH | CMP-13 | prod | private_cloud | data_center | INF-02 | container | 2 | apih-cn | CN |
| DEP-24 | NA APIH | CMP-13 | prod | private_cloud | data_center | INF-06 | container | 2 | apih-na | NA mediation zone |
| DEP-25 | CN Kafka | CMP-14 | prod | private_cloud | data_center | INF-02 | container | 3 | kafka-cn | CN |
| DEP-26 | NA Kafka | CMP-14 | prod | private_cloud | data_center | INF-06 | container | 3 | kafka-na | NA mediation zone |
| DEP-27 | CN RabbitMQ | CMP-15 | prod | private_cloud | data_center | INF-02 | container | 2 | mq-cn | CN |
| DEP-28 | NA RabbitMQ | CMP-15 | prod | private_cloud | data_center | INF-07 | container | 2 | mq-na | NA middleware zone |
| DEP-29 | CN Debezium | CMP-16 | prod | private_cloud | data_center | INF-02 | container | 2 | dbz-cn | CN |
| DEP-30 | NA Debezium | CMP-16 | prod | private_cloud | data_center | INF-07 | container | 2 | dbz-na | NA middleware zone |
| DEP-31 | CN Elasticsearch | CMP-17 | prod | private_cloud | data_center | INF-03 | vm | 3 | es-cn | CN DB zone |
| DEP-32 | NA Elasticsearch | CMP-17 | prod | private_cloud | data_center | INF-09 | vm | 3 | es-na | NA DB zone |
| DEP-33 | CN Redis | CMP-18 | prod | private_cloud | data_center | INF-03 | vm | 3 | redis-cn | CN DB zone |
| DEP-34 | NA Redis | CMP-18 | prod | private_cloud | data_center | INF-09 | vm | 3 | redis-na | NA DB zone |
| DEP-35 | CN MySQL | CMP-19 | prod | private_cloud | data_center | INF-03 | vm | 3 | mysql-cn | CN only |
| DEP-36 | CN PostgreSQL | CMP-20 | prod | private_cloud | data_center | INF-03 | vm | 3 | pg-cn | CN DB zone |
| DEP-37 | NA PostgreSQL | CMP-20 | prod | private_cloud | data_center | INF-09 | vm | 3 | pg-na | NA DB zone |
| DEP-38 | CN SQLServer | CMP-21 | prod | private_cloud | data_center | INF-03 | vm | 3 | mssql-cn | CN DB zone |
| DEP-39 | NA SQLServer | CMP-21 | prod | private_cloud | data_center | INF-09 | vm | 3 | mssql-na | NA DB zone |
| DEP-40 | NA ERPS | CMP-22 | prod | private_cloud | data_center | INF-05 | container | 2 | erps-dep | NA only |
| DEP-41 | NA LGS | CMP-23 | prod | private_cloud | data_center | INF-05 | container | 2 | lgs-dep | NA only |
| DEP-42 | NA IBS | CMP-24 | prod | private_cloud | data_center | INF-05 | container | 2 | ibs-dep | NA only |
| DEP-43 | SAP NA interface | CMP-35 | prod | third_party | saas | INF-08 | physical | 1 | s4-na-dep | NA SAP zone |
| DEP-44 | CN SAP interface | CMP-33 | prod | third_party | saas | INF-01 | physical | 1 | ecc-dep | CN SAP zone |
| DEP-45 | Azure peers | CMP-31 | prod | public_cloud | public_cloud_region | INF-12 | serverless | 1 | azure-peer-dep | CMP-31–CMP-32 |
| DEP-46 | CN peer boundary | CMP-29 | prod | third_party | saas | INF-01 | serverless | 1 | cn-peer-dep | |
| DEP-47 | AWS peer boundary | CMP-30 | prod | public_cloud | public_cloud_region | INF-11 | serverless | 1 | aws-peer-dep | |
| DEP-48 | Azure SaaS boundary | CMP-32 | prod | third_party | saas | INF-12 | serverless | 1 | azure-saas-dep | |
| DEP-49 | CN SAP interface | CMP-34 | prod | third_party | saas | INF-01 | physical | 1 | s4-cn-dep | |
| DEP-50 | CN peer boundary | CMP-25 | prod | third_party | saas | INF-01 | serverless | 1 | ecomm-peer-dep | |
| DEP-51 | CN peer boundary | CMP-26 | prod | third_party | saas | INF-01 | serverless | 1 | sos-prc-dep | |
| DEP-52 | CN peer boundary | CMP-27 | prod | third_party | saas | INF-01 | serverless | 1 | cfos-prc-dep | |
| DEP-53 | CN peer boundary | CMP-28 | prod | third_party | saas | INF-01 | serverless | 1 | cfos-ap-dep | |
| DEP-46 | CN peer boundary | CMP-29 | prod | third_party | saas | INF-01 | serverless | 1 | cn-peer-dep | |
| DEP-47 | AWS peer boundary | CMP-30 | prod | public_cloud | public_cloud_region | INF-11 | serverless | 1 | aws-peer-dep | |
| DEP-48 | Azure SaaS boundary | CMP-32 | prod | third_party | saas | INF-12 | serverless | 1 | azure-saas-dep | |
| DEP-49 | CN SAP interface | CMP-34 | prod | third_party | saas | INF-01 | physical | 1 | s4-cn-dep | |
| DEP-50 | CN peer boundary | CMP-25 | prod | third_party | saas | INF-01 | serverless | 1 | ecomm-peer-dep | |
| DEP-51 | CN peer boundary | CMP-26 | prod | third_party | saas | INF-01 | serverless | 1 | sos-prc-dep | |
| DEP-52 | CN peer boundary | CMP-27 | prod | third_party | saas | INF-01 | serverless | 1 | cfos-prc-dep | |
| DEP-53 | CN peer boundary | CMP-28 | prod | third_party | saas | INF-01 | serverless | 1 | cfos-ap-dep | |

## R5 — Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | Office → CN web | internet | CMP-01 | HTTPS | 443 | none | TLS1.3 | 否 | INF-16 | CN employees; user auth = AUTH-01 |
| FLOW-02 | Office → NA web | internet | CMP-01 | HTTPS | 443 | none | TLS1.3 | 否 | INF-19 | NA employees |
| FLOW-03 | web → gateway | CMP-01 | CMP-02 | HTTPS | 443 | none | TLS1.3 | 否 | - | internal access auth |
| FLOW-04 | gateway → order creation | CMP-02 | CMP-03 | HTTPS | 8080 | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-05 | order creation → PostgreSQL | CMP-03 | CMP-20 | JDBC | 5432 | UserPassword | TLS1.3 | 否 | - | creds in K8s Secret |
| FLOW-06 | order creation → APIH | CMP-03 | CMP-13 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | - | cross-app mediation |
| FLOW-07 | Debezium → RabbitMQ | CMP-16 | CMP-15 | TCP | 5672 | UserPassword | TLS1.3 | 否 | - | CDC pipeline |
| FLOW-08 | RabbitMQ → Kafka | CMP-15 | CMP-14 | Kafka | 9093 | SASL_SCRAM | TLS1.3 | 否 | - | CDC to events |
| FLOW-09 | APIH → ECC-CN | CMP-13 | CMP-33 | RFC | 3300 | Kerberos | TLS1.3 | 否 | - | SAP Function module |
| FLOW-10 | Kafka → SOS-ROW | CMP-14 | CMP-30 | Kafka | 9093 | SASL_SCRAM | TLS1.3 | 是 | - | 跨境 event replication |
| FLOW-11 | Kafka → D365 | CMP-14 | CMP-32 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | - | Azure SaaS |
| FLOW-12 | APIH → ERPS | CMP-13 | CMP-22 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | - | NA backend |
| FLOW-13 | Kafka → Elasticsearch | CMP-14 | CMP-17 | HTTPS | 9200 | Basic | TLS1.3 | 否 | - | search indexing |

## R6 — Infra network links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | Office → CN DC | INF-13 | INF-01 | mpls | TBD | 是 | InfraSec | employee access CN |
| LNK-02 | Office → NA DC | INF-13 | INF-04 | mpls | TBD | 是 | InfraSec | employee access NA |
| LNK-03 | CN ↔ NA backbone | INF-01 | INF-04 | mpls | TBD | 是 | InfraSec | active-active replication |
| LNK-04 | NA ↔ AWS | INF-04 | INF-11 | vpn | TBD | 是 | InfraSec | peer app |
| LNK-05 | NA ↔ Azure | INF-04 | INF-12 | expressroute | TBD | 是 | InfraSec | Azure peers |

## R7 — Auth (user / entry)

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | Employee SSO | user | CMP-01 | INF-22 | SAML2 | RBAC | 是 | employees via the identity DC |
| AUTH-02 | CN mediation entry | application | CMP-11 | INF-22 | SAML2 | RBAC | 否 | APIM admin entry |
