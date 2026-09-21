# Systems Registry — Factory MES (PlantMES)

Single source of truth for every entity name in this example (req/v2 model).

- **参考图不做脱敏**：`input/diagrams/reference-architecture.png` 保留原名。
- **文档只引用编号**：`prompt.md`、`requirements.md`、`README.md`、`config.yaml`
  中所有实体均以类型化编号引用，不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **编号含义（req/v2）**：`INF` 承载/网络节点、`APP` 应用系统、`CMP` 组件/服务、
  `STK` 组件-技术栈、`DEP` 部署、`FLOW` 组件通信、`LNK` 基础设施链路、`AUTH` 用户/入口认证。
- **设备归属**：VIP、ADFS 等网络/安全设备是 `INF` 节点，不是 `CMP` 组件。
- **范围标记**：清单型实体（`INF`/`APP`/`CMP`）默认全部纳入设计范围；若有意不纳入，
  在其「备注」列写 `OUT-OF-SCOPE`。派生行（`DEP`/`FLOW`/`LNK`/`AUTH`）不参与
  `prompt.md` 覆盖检查。
- **手动脱敏流程**：直接修改下表「文档用名」列即可；编号不变，所有引用自动跟随。

## R1 — Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | plant-us-01 | data_center | private_cloud | prod_network | - | US | plant-site | plant-local site |
| INF-02 | plant-us-01 APP Zone | network_zone | private_cloud | prod_network | INF-01 | US | plant-zone | plant APP zone |
| INF-03 | dc-us | data_center | private_cloud | prod_network | - | US | us-corp-dc | US corporate DC |
| INF-04 | dc-cn-primary | data_center | private_cloud | prod_network | - | CN | cn-primary-dc | CN primary DC |
| INF-05 | dc-us-na | data_center | private_cloud | prod_network | - | US | na-dc | NA DC, multi-zone |
| INF-06 | dc-cn-secondary | data_center | private_cloud | prod_network | - | CN | cn-secondary-dc | CN secondary DC |
| INF-07 | azure-eastus | iaas_vpc_vnet | public_cloud | prod_network | - | US | azure-us | Azure region |
| INF-08 | NA-PROD-INA-INTEGRATION | network_zone | private_cloud | prod_network | INF-05 | US | na-int-zone | NA integration zone |
| INF-09 | NA-PROD-INA-K8S | network_zone | private_cloud | prod_network | INF-05 | US | na-k8s-zone | NA Kubernetes zone |
| INF-10 | NA-PROD-INA-LAKEHOUSE | network_zone | private_cloud | prod_network | INF-05 | US | na-lakehouse-zone | NA lakehouse zone |
| INF-11 | NA-PROD-INA-SAP | network_zone | private_cloud | prod_network | INF-05 | US | na-sap-zone | NA SAP zone |
| INF-12 | dc-cn-primary App Zone | network_zone | private_cloud | prod_network | INF-04 | CN | cn-app-zone | CN app zone |
| INF-13 | VIP | load_balancer | private_cloud | prod_network | INF-02 | US | plant-vip | HTTPS ingress VIP |
| INF-14 | ADFS | identity_provider | private_cloud | prod_network | INF-03 | US | adfs | external authorization IdP |
| INF-15 | Plant boundary firewall | firewall | private_cloud | prod_network | INF-02 | US | plant-fw | plant/ WAN/ inter-zone transit; deny by default |
| INF-16 | dc-us boundary firewall | firewall | private_cloud | prod_network | INF-03 | US | us-dc-fw | identity/authorization transit |
| INF-17 | dc-cn-primary boundary firewall | firewall | private_cloud | prod_network | INF-12 | CN | cn-primary-fw | cross-DC and inter-zone integration |
| INF-18 | dc-cn-secondary boundary firewall | firewall | private_cloud | prod_network | INF-06 | CN | cn-secondary-fw | cross-DC Kafka transit |
| INF-19 | dc-us-na boundary firewall | firewall | private_cloud | prod_network | INF-08 | US | na-fw | all cross-zone, cross-DC, plant and Azure flows |
| INF-20 | Azure EDW firewall | firewall | public_cloud | prod_network | INF-07 | US | azure-edw-fw | NA DC to Azure data endpoint |

## R2 — Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | PlantMES | new | org_it | - | plantmes | autonomous plant MES |
| APP-02 | LMS ROW | existing | org_it | - | us-identity | US DC authorization boundary |
| APP-03 | CN Central Platform | existing | org_it | - | cn-central | APIM + Kafka CN + peers |
| APP-04 | NA Integration Platform | existing | org_it | - | na-int-platform | Kafka NA + NA services |
| APP-05 | SAP NA | existing | third_party | SAP | sap-na | S4 / POCS / Service-CRM |
| APP-06 | Manufacturing Control Tower | new | org_it | - | mct-platform | plant message bridge |
| APP-07 | EDW ROW | existing | org_it | - | edw | Enterprise data warehouse |

## R3 — Components / services

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | Nginx Master | APP-01 | ingress | service | lb | load_balancer | - | nginx-master | HTTPS ingress |
| CMP-02 | Nginx Slave | APP-01 | ingress | service | lb | load_balancer | - | nginx-slave | HTTPS ingress |
| CMP-03 | LeMES-Web | APP-01 | web | component | fe | web_frontend | - | plantmes-web | plant web frontend |
| CMP-04 | Spring Cloud Gateway | APP-01 | gateway | component | ip | api_gateway | - | spring-cloud-gateway | K8s ingress gateway |
| CMP-05 | global-config | APP-01 | services | service | be | backend_service | - | global-config | Java/Spring |
| CMP-06 | elasticjob | APP-01 | services | service | be | backend_service | - | elasticjob | Java/Spring |
| CMP-07 | common | APP-01 | services | service | be | backend_service | - | common | Java/Spring |
| CMP-08 | web | APP-01 | services | service | be | backend_service | - | web | Java/Spring |
| CMP-09 | inbound-executor | APP-01 | services | service | be | backend_service | - | inbound-executor | Java/Spring |
| CMP-10 | quality | APP-01 | services | service | be | backend_service | - | quality | Java/Spring |
| CMP-11 | report | APP-01 | services | service | be | backend_service | - | report | Java/Spring |
| CMP-12 | order | APP-01 | services | service | be | backend_service | - | order | Java/Spring |
| CMP-13 | material | APP-01 | services | service | be | backend_service | - | material | Java/Spring |
| CMP-14 | printing | APP-01 | services | service | be | backend_service | - | printing | Java/Spring |
| CMP-15 | api | APP-01 | services | service | be | backend_service | - | api | Java/Spring |
| CMP-16 | outbound-executor | APP-01 | services | service | be | backend_service | - | outbound-executor | Java/Spring |
| CMP-17 | lvr | APP-01 | services | service | be | backend_service | - | lvr | Java/Spring |
| CMP-18 | trace | APP-01 | services | service | be | backend_service | - | trace | Java/Spring |
| CMP-19 | PgSQL HA GRP Master | APP-01 | db | component | db | database | AES-256 | pgsql-master | plant-local HA, VM |
| CMP-20 | PgSQL HA GRP Mirror | APP-01 | db | component | db | database | AES-256 | pgsql-mirror | plant-local HA, VM |
| CMP-21 | LMS(labor management service) ROW | APP-02 | - | component | ip | integration_service | - | lms-row | EXISTING boundary |
| CMP-22 | APIM | APP-03 | - | component | ip | api_gateway | - | apim | EXISTING interface |
| CMP-23 | KAFKA (CN hub) | APP-03 | - | component | mq | message_bus | - | kafka-cn | EXISTING interface |
| CMP-24 | MCS(manufactory configuration service) | APP-03 | - | service | be | backend_service | - | mcs | NEW interface |
| CMP-25 | APS(advanced planning service) | APP-03 | - | service | be | backend_service | - | aps | NEW interface |
| CMP-26 | ERPS(ERP service) | APP-03 | - | service | be | backend_service | - | erps | NEW; also deployed in NA |
| CMP-27 | PDS(procument data service) | APP-03 | - | service | be | backend_service | - | pds | NEW interface |
| CMP-28 | KAFKA (NA INTEGRATION zone) | APP-04 | - | component | mq | message_bus | - | kafka-na | NEW interface |
| CMP-29 | Lakehouse-ROW | APP-04 | - | component | db | data_lake | - | lakehouse-row | NEW; TCP/TLS 1.2 |
| CMP-30 | LGS(logistics dateway service)-NA | APP-04 | - | service | be | backend_service | - | lgs-na | NEW interface |
| CMP-31 | IBS(Install  base service) | APP-04 | - | service | be | backend_service | - | ibs | NEW interface |
| CMP-32 | S4-NA | APP-05 | - | component | ip | integration_service | - | s4-na | NEW; IDOC |
| CMP-33 | POCS(Purchase order collaboration service)-NA | APP-05 | - | component | ip | integration_service | - | pocs-na | NEW; RFC |
| CMP-34 | Service-CRM | APP-05 | - | component | ip | integration_service | - | service-crm | NEW; RFC |
| CMP-35 | MCT(Manufacturing Control Tower) | APP-06 | - | service | be | backend_service | - | mct | NEW; TCP/Kafka |
| CMP-36 | EDW ROW | APP-07 | - | component | db | data_warehouse | - | edw-row | NEW; Kafka SASL_SSL |

## R4 — Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|------------|--------------|--------|----------|------|
| DEP-01 | Nginx master (VM) | CMP-01 | prod | private_cloud | data_center | INF-02 | vm | 1 | nginx-master-dep | plant-local |
| DEP-02 | Nginx slave (VM) | CMP-02 | prod | private_cloud | data_center | INF-02 | vm | 1 | nginx-slave-dep | plant-local |
| DEP-03 | LeMES-Web pod | CMP-03 | prod | private_cloud | data_center | INF-02 | container | 2 | plantmes-web-dep | plant K8s |
| DEP-04 | Spring Cloud Gateway pod | CMP-04 | prod | private_cloud | data_center | INF-02 | container | 2 | gateway-dep | plant K8s |
| DEP-05 | Plant Java services | CMP-05 | prod | private_cloud | data_center | INF-02 | container | 14 | plant-svc-dep | 13 services (CMP-05–CMP-18) share this profile |
| DEP-06 | PgSQL HA master VM | CMP-19 | prod | private_cloud | data_center | INF-01 | vm | 1 | pgsql-master-dep | plant-local only |
| DEP-07 | PgSQL HA mirror VM | CMP-20 | prod | private_cloud | data_center | INF-01 | vm | 1 | pgsql-mirror-dep | plant-local only |
| DEP-08 | LMS ROW interface | CMP-21 | prod | private_cloud | data_center | INF-03 | container | 1 | lms-row-dep | existing |
| DEP-09 | APIM cluster | CMP-22 | prod | private_cloud | data_center | INF-12 | container | 2 | apim-dep | existing |
| DEP-10 | Kafka CN hub | CMP-23 | prod | private_cloud | data_center | INF-12 | container | 3 | kafka-cn-dep | existing |
| DEP-11 | CN peer services | CMP-24 | prod | private_cloud | data_center | INF-12 | container | 4 | cn-peer-dep | CMP-24–CMP-27 |
| DEP-12 | ERPS in NA K8s | CMP-26 | prod | private_cloud | data_center | INF-09 | container | 2 | erps-na-dep | same component, second site |
| DEP-13 | Kafka NA | CMP-28 | prod | private_cloud | data_center | INF-08 | container | 3 | kafka-na-dep | new |
| DEP-14 | Lakehouse ROW | CMP-29 | prod | private_cloud | data_center | INF-10 | container | 2 | lakehouse-dep | new |
| DEP-15 | NA K8s services | CMP-30 | prod | private_cloud | data_center | INF-09 | container | 2 | lgs-na-dep | CMP-30–CMP-31 |
| DEP-16 | SAP interfaces | CMP-32 | prod | third_party | saas | INF-11 | physical | 1 | sap-na-dep | CMP-32–CMP-34 |
| DEP-17 | MCT bridge | CMP-35 | prod | private_cloud | data_center | INF-06 | container | 2 | mct-dep | new |
| DEP-18 | EDW consume | CMP-36 | prod | public_cloud | public_cloud_region | INF-07 | serverless | 1 | edw-dep | new |

## R5 — Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | Intranet client → VIP | internet | CMP-01 | HTTPS | 443 | none | TLS1.3 | 否 | INF-13 | plant intranet users; user auth = AUTH-01 |
| FLOW-02 | Nginx → web | CMP-01 | CMP-03 | HTTPS | 443 | none | TLS1.3 | 否 | - | |
| FLOW-03 | web → gateway | CMP-03 | CMP-04 | HTTPS | 443 | none | TLS1.3 | 否 | - | |
| FLOW-04 | gateway → order svc | CMP-04 | CMP-12 | HTTPS | 8080 | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-05 | order svc → PgSQL | CMP-12 | CMP-19 | JDBC | 5432 | UserPassword | TLS1.3 | 否 | - | plant-local; creds in K8s Secret |
| FLOW-06 | gateway → LMS ROW | CMP-04 | CMP-21 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.3 | 否 | - | external authorization |
| FLOW-07 | trace svc → Kafka CN | CMP-18 | CMP-23 | Kafka | 9093 | SASL_SCRAM | TLS1.3 | 是 | - | async plant→central |
| FLOW-08 | trace svc → Kafka NA | CMP-18 | CMP-28 | Kafka | 9093 | SASL_SCRAM | TLS1.3 | 是 | - | async plant→central |
| FLOW-09 | Kafka NA → LGS-NA | CMP-28 | CMP-30 | Kafka | 9093 | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-10 | Kafka NA → S4-NA | CMP-28 | CMP-32 | IDOC | - | Kerberos | TLS1.3 | 否 | - | SAP logon ticket |
| FLOW-11 | Kafka NA → MCT | CMP-28 | CMP-35 | Kafka | 9093 | SASL_SCRAM | TLS1.3 | 是 | - | CN secondary bridge |
| FLOW-12 | Kafka NA → EDW | CMP-28 | CMP-36 | Kafka | 9093 | SASL_SCRAM | TLS1.3 | 否 | - | SASL_SSL |

## R6 — Infra network links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | plant WAN | INF-01 | INF-03 | mpls | TBD | 是 | InfraSec | plant ↔ US DC |
| LNK-02 | plant WAN backup | INF-01 | INF-05 | vpn | TBD | 是 | InfraSec | plant ↔ NA DC backup |
| LNK-03 | DC backbone | INF-04 | INF-05 | mpls | TBD | TBD | InfraSec | CN ↔ NA |
| LNK-04 | cloud attach | INF-05 | INF-07 | vpn | TBD | 是 | InfraSec | NA DC ↔ Azure |

## R7 — Auth (user / entry)

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | Plant user SSO | user | CMP-03 | INF-14 | SAML2 | RBAC | 是 | plant intranet users via dc-us ADFS |
| AUTH-02 | Site admin | application | CMP-04 | INF-14 | SAML2 | RBAC | 是 | gateway admin entry |
