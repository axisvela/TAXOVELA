# Systems Registry — Service Delivery Platform (SDP)

Single source of truth for every system / service name in this example.

- **参考图不做脱敏**：`input/diagrams/reference-architecture.png` 保留原名。
- **文档只引用编号**：`prompt.md`、`requirements.md`、`README.md`、`config.yaml`
  中所有系统/服务均以类型化编号引用（`INF-` 基础设施、`APP-` 系统、
  `CMP-` 组件，以及 `DEP`/`FLOW`/`LNK`/`AUTH` 派生层），不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **范围标记**：本表默认全部纳入设计范围；若某系统有意不纳入，在其「备注」列写上 `OUT-OF-SCOPE`。

## R1 — Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | CN Primary DC, City A, Province A [CN] | data_center | private_cloud | prod_network | - | CN | cn-primary-dc-city-a-province-a-cn | private_dc |
| INF-02 | DMZ | network_zone | private_cloud | dmz | INF-01 | CN | dmz | dmz |
| INF-03 | Edge router | router | private_cloud | dmz | INF-02 | CN | edge-router | NW appliance |
| INF-04 | F5 | load_balancer | private_cloud | dmz | INF-02 | CN | f5 | LB appliance |
| INF-05 | Intranet | network_zone | private_cloud | prod_network | INF-01 | CN | intranet | intranet |
| INF-06 | DB Zone | network_zone | private_cloud | prod_network | INF-01 | CN | db-zone | db_zone |
| INF-07 | US DC, City C, State X [US] | data_center | private_cloud | prod_network | - | US | us-dc-city-c-state-x-us | private_dc |
| INF-08 | App Zone / Intranet | network_zone | private_cloud | prod_network | INF-07 | US | app-zone-intranet | intranet |
| INF-09 | ADFS | identity_provider | private_cloud | prod_network | INF-08 | US | adfs | SEC appliance |
| INF-10 | Enterprise ID | identity_provider | private_cloud | prod_network | INF-08 | US | enterprise-id | SEC appliance |
| INF-11 | CN Secondary DC, City B, Province B [CN] | data_center | private_cloud | prod_network | - | CN | cn-secondary-dc-city-b-province-b-cn | private_dc |
| INF-12 | Intranet | network_zone | private_cloud | prod_network | INF-11 | CN | intranet-2 | intranet |
| INF-13 | Support DC, City F [CN] | data_center | private_cloud | prod_network | - | CN | support-dc-city-f-cn | private_dc |
| INF-14 | App Zone | network_zone | private_cloud | prod_network | INF-13 | CN | app-zone | app_zone |
| INF-15 | SAP landscape [location TBD] | data_center | private_cloud | prod_network | - | TBD | sap-landscape-location-tbd | private_dc |
| INF-16 | SAP Private Zone | network_zone | private_cloud | prod_network | INF-15 | TBD | sap-private-zone | intranet |
| INF-17 | Azure US [exact region TBD] | iaas_vpc_vnet | public_cloud | prod_network | - | TBD | azure-us-exact-region-tbd | azure_vnet |
| INF-18 | SaaS Application Boundary | network_zone | public_cloud | prod_network | INF-17 | TBD | saas-application-boundary | spoke |
| INF-19 | Application Boundary | network_zone | public_cloud | prod_network | INF-17 | TBD | application-boundary | spoke |
| INF-20 | Partner hosted [locations TBD] | data_center | private_cloud | prod_network | - | TBD | partner-hosted-locations-tbd | private_dc |
| INF-21 | Internet 3PL Boundary | network_zone | private_cloud | prod_network | INF-20 | TBD | internet-3pl-boundary | dmz |
| INF-22 | Partner hosted [locations TBD] | data_center | private_cloud | prod_network | - | TBD | partner-hosted-locations-tbd-2 | private_dc |
| INF-23 | Internet File-Transfer Boundary | network_zone | private_cloud | prod_network | INF-20 | TBD | internet-file-transfer-boundary | dmz |

## R2 — Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | Service Delivery Platform | new | org_it | - | service-delivery-platform | active-active CN + NA |
| APP-02 | SAP landscape | existing | third_party | SAP | sap-landscape | ECC/S4, Function and SLT |
| APP-03 | Azure satellites | existing | third_party | Microsoft Azure | azure-satellites | d365 SaaS and edge cache |
| APP-04 | Logistics partners | existing | third_party | - | logistics-partners | 3PL EDI/API boundary |
| APP-05 | File-transfer partners | existing | third_party | - | file-transfer-partners | managed file exchange |

## R3 — Components / services

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | Service-Supply-Chain-dmz-nginx-proxy | APP-01 | - | service | fe | web_frontend | - | service-supply-chain-dmz-nginx-proxy | FE |
| CMP-02 | Service-Supply-Chain-gateway | APP-01 | - | service | api | api_gateway | - | service-supply-chain-gateway | API |
| CMP-03 | Service-Supply-Chain-web | APP-01 | - | service | fe | web_frontend | - | service-supply-chain-web | FE |
| CMP-04 | WSO2 | APP-01 | - | service | ip | integration_service | - | wso2 | IP |
| CMP-05 | Kafka (primary) | APP-01 | - | service | mq | message_bus | - | kafka | MQ |
| CMP-06 | Service-Supply-Chain-int-nginx-proxy | APP-01 | - | service | be | backend_service | - | service-supply-chain-int-nginx-proxy | BE |
| CMP-07 | Service-Supply-Chain-main | APP-01 | - | service | be | backend_service | - | service-supply-chain-main | BE |
| CMP-08 | Service-Supply-Chain-websocket | APP-01 | - | service | be | backend_service | - | service-supply-chain-websocket | BE |
| CMP-09 | Service-Supply-Chain-* group (10 services) | APP-01 | - | service | be | backend_service | - | service-supply-chain-group | BE |
| CMP-10 | Service-Supply-Chain-* group (22 services) | APP-01 | - | service | be | backend_service | - | service-supply-chain-group-2 | BE |
| CMP-11 | MFT platform | APP-01 | - | service | ip | integration_service | - | mft-platform | IP |
| CMP-12 | MySQL TMS HA (1 primary + 2 replicas) | APP-01 | - | component | db | database | - | mysql-tms-ha | DB |
| CMP-13 | MySQL Main HA (1 primary + 2 replicas) | APP-01 | - | component | db | database | - | mysql-main-ha | DB |
| CMP-14 | MySQL WMS HA (1 primary + 2 replicas) | APP-01 | - | component | db | database | - | mysql-wms-ha | DB |
| CMP-15 | MySQL MDS HA (1 primary + 2 replicas) | APP-01 | - | component | db | database | - | mysql-mds-ha | DB |
| CMP-16 | MySQL OMS HA (1 primary + 2 replicas) | APP-01 | - | component | db | database | - | mysql-oms-ha | DB |
| CMP-17 | Redis HA (3 primary + 3 replicas) | APP-01 | - | component | db | database | - | redis-ha | DB |
| CMP-18 | RabbitMQ HA (3 replicas) | APP-01 | - | service | mq | message_bus | - | rabbitmq-ha | MQ |
| CMP-19 | Elasticsearch HA (3 nodes) | APP-01 | - | component | db | database | - | elasticsearch-ha | DB |
| CMP-20 | Account-Service | APP-01 | - | service | be | backend_service | - | account-service | BE |
| CMP-21 | Service-customer-master-data | APP-01 | - | service | be | backend_service | - | service-customer-master-data | BE |
| CMP-22 | Serice-Data-serviceE | APP-01 | - | service | be | backend_service | - | serice-data-servicee | BE |
| CMP-23 | Price-master-ROW | APP-01 | - | service | be | backend_service | - | price-master-row | BE |
| CMP-24 | Reverse-Management-System | APP-01 | - | service | be | backend_service | - | reverse-management-system | BE |
| CMP-25 | procurement-service | APP-01 | - | service | be | backend_service | - | procurement-service | BE |
| CMP-26 | lakehouse | APP-01 | - | component | db | object_storage | - | lakehouse | DS |
| CMP-27 | Kafka (secondary) | APP-01 | - | service | mq | message_bus | - | kafka-2 | MQ |
| CMP-28 | support-hub | APP-01 | - | service | be | backend_service | - | support-hub | BE |
| CMP-29 | support-portal | APP-01 | - | service | be | backend_service | - | support-portal | BE |
| CMP-30 | support-gateway | APP-01 | - | service | api | api_gateway | - | support-gateway | API |
| CMP-31 | S4 | APP-02 | - | service | be | backend_service | - | s4 | BE |
| CMP-32 | SECC | APP-02 | - | service | be | backend_service | - | secc | BE |
| CMP-33 | LSCRM | APP-02 | - | service | be | backend_service | - | lscrm | BE |
| CMP-34 | CECC | APP-02 | - | service | be | backend_service | - | cecc | BE |
| CMP-35 | S3 | APP-02 | - | component | db | object_storage | - | s3 | DS |
| CMP-36 | d365-service-delivery-bu1 | APP-03 | - | service | be | backend_service | - | d365-service-delivery-bu1 | BE |
| CMP-37 | d365-service-delivery-bu2 | APP-03 | - | service | be | backend_service | - | d365-service-delivery-bu2 | BE |
| CMP-38 | d365-service-delivery-bu3 | APP-03 | - | service | be | backend_service | - | d365-service-delivery-bu3 | BE |
| CMP-39 | edge-cache | APP-03 | - | service | be | backend_service | - | edge-cache | BE |
| CMP-40 | logistics partner A | APP-04 | - | service | be | backend_service | - | logistics-partner-a | BE |
| CMP-41 | logstics-vendor-1 | APP-04 | - | service | be | backend_service | - | logstics-vendor-1 | BE |
| CMP-42 | logistics partner B | APP-04 | - | service | be | backend_service | - | logistics-partner-b | BE |
| CMP-43 | logistics partner C | APP-04 | - | service | be | backend_service | - | logistics-partner-c | BE |
| CMP-44 | logistics partner D | APP-04 | - | service | be | backend_service | - | logistics-partner-d | BE |
| CMP-45 | logistics partner E | APP-04 | - | service | be | backend_service | - | logistics-partner-e | BE |
| CMP-46 | file partner A | APP-04 | - | service | be | backend_service | - | file-partner-a | BE |
| CMP-47 | file partner B | APP-04 | - | service | be | backend_service | - | file-partner-b | BE |
| CMP-48 | file partner C | APP-04 | - | service | be | backend_service | - | file-partner-c | BE |

## R4 — Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|-----------|--------------|--------|----------|------|
| DEP-01 | Service-Supply-Chain-dmz-nginx-proxy | CMP-01 | prod | private_cloud | data_center | INF-02 | container | - | service-supply-chain-dmz-nginx-proxy-dep | Internal K8s Platform |
| DEP-02 | Service-Supply-Chain-gateway | CMP-02 | prod | private_cloud | data_center | INF-02 | container | - | service-supply-chain-gateway-deployment | Internal K8s Platform |
| DEP-03 | Service-Supply-Chain-web | CMP-03 | prod | private_cloud | data_center | INF-02 | container | - | service-supply-chain-web-deployment | Internal K8s Platform |
| DEP-04 | WSO2 | CMP-04 | prod | private_cloud | data_center | INF-12 | vm | - | wso2-deployment | Private DC integration platform |
| DEP-05 | Kafka (primary) | CMP-05 | prod | private_cloud | data_center | INF-12 | container | - | kafka-deployment | Private DC HA cluster |
| DEP-06 | Service-Supply-Chain-int-nginx-proxy | CMP-06 | prod | private_cloud | data_center | INF-12 | container | - | service-supply-chain-int-nginx-proxy-dep | Internal K8s Platform |
| DEP-07 | Service-Supply-Chain-main | CMP-07 | prod | private_cloud | data_center | INF-12 | container | - | service-supply-chain-main-deployment | Internal K8s Platform |
| DEP-08 | Service-Supply-Chain-websocket | CMP-08 | prod | private_cloud | data_center | INF-12 | container | - | service-supply-chain-websocket-deploymen | Internal K8s Platform |
| DEP-09 | Service-Supply-Chain-* group (10 services) | CMP-09 | prod | private_cloud | data_center | INF-12 | container | - | service-supply-chain-group-deployment | Internal K8s Platform HA workload group |
| DEP-10 | Service-Supply-Chain-* group (22 services) | CMP-10 | prod | private_cloud | data_center | INF-12 | container | - | service-supply-chain-group-deployment-2 | Internal K8s Platform HA workload group |
| DEP-11 | MFT platform | CMP-11 | prod | private_cloud | data_center | INF-12 | vm | - | mft-platform-deployment | Private DC HA integration platform |
| DEP-12 | MySQL TMS HA (1 primary + 2 replicas) | CMP-12 | prod | private_cloud | data_center | INF-06 | physical | - | mysql-tms-ha-deployment | Private DC HA group |
| DEP-13 | MySQL Main HA (1 primary + 2 replicas) | CMP-13 | prod | private_cloud | data_center | INF-06 | physical | - | mysql-main-ha-deployment | Private DC HA group |
| DEP-14 | MySQL WMS HA (1 primary + 2 replicas) | CMP-14 | prod | private_cloud | data_center | INF-06 | physical | - | mysql-wms-ha-deployment | Private DC HA group |
| DEP-15 | MySQL MDS HA (1 primary + 2 replicas) | CMP-15 | prod | private_cloud | data_center | INF-06 | physical | - | mysql-mds-ha-deployment | Private DC HA group |
| DEP-16 | MySQL OMS HA (1 primary + 2 replicas) | CMP-16 | prod | private_cloud | data_center | INF-06 | physical | - | mysql-oms-ha-deployment | Private DC HA group |
| DEP-17 | Redis HA (3 primary + 3 replicas) | CMP-17 | prod | private_cloud | data_center | INF-06 | physical | - | redis-ha-deployment | Private DC HA group |
| DEP-18 | RabbitMQ HA (3 replicas) | CMP-18 | prod | private_cloud | data_center | INF-06 | physical | - | rabbitmq-ha-deployment | Private DC HA group |
| DEP-19 | Elasticsearch HA (3 nodes) | CMP-19 | prod | private_cloud | data_center | INF-06 | physical | - | elasticsearch-ha-deployment | Private DC HA group |
| DEP-20 | Account-Service | CMP-20 | prod | private_cloud | data_center | INF-08 | container | - | account-service-deployment |  |
| DEP-21 | Service-customer-master-data | CMP-21 | prod | private_cloud | data_center | INF-08 | container | - | service-customer-master-data-deployment |  |
| DEP-22 | Serice-Data-serviceE | CMP-22 | prod | private_cloud | data_center | INF-08 | container | - | serice-data-servicee-deployment |  |
| DEP-23 | Price-master-ROW | CMP-23 | prod | private_cloud | data_center | INF-08 | container | - | price-master-row-deployment |  |
| DEP-24 | Reverse-Management-System | CMP-24 | prod | private_cloud | data_center | INF-12 | container | - | reverse-management-system-deployment |  |
| DEP-25 | procurement-service | CMP-25 | prod | private_cloud | data_center | INF-12 | container | - | procurement-service-deployment |  |
| DEP-26 | lakehouse | CMP-26 | prod | private_cloud | data_center | INF-12 | container | - | lakehouse-deployment |  |
| DEP-27 | Kafka (secondary) | CMP-27 | prod | private_cloud | data_center | INF-12 | container | - | kafka-deployment-2 |  |
| DEP-28 | support-hub | CMP-28 | prod | private_cloud | data_center | INF-12 | container | - | support-hub-deployment |  |
| DEP-29 | support-portal | CMP-29 | prod | private_cloud | data_center | INF-14 | container | - | support-portal-deployment |  |
| DEP-30 | support-gateway | CMP-30 | prod | private_cloud | data_center | INF-14 | container | - | support-gateway-deployment |  |
| DEP-31 | S4 | CMP-31 | prod | private_cloud | data_center | INF-16 | container | - | s4-deployment |  |
| DEP-32 | SECC | CMP-32 | prod | private_cloud | data_center | INF-16 | container | - | secc-deployment |  |
| DEP-33 | LSCRM | CMP-33 | prod | private_cloud | data_center | INF-16 | container | - | lscrm-deployment |  |
| DEP-34 | CECC | CMP-34 | prod | private_cloud | data_center | INF-16 | container | - | cecc-deployment |  |
| DEP-35 | S3 | CMP-35 | prod | private_cloud | data_center | INF-16 | container | - | s3-deployment |  |
| DEP-36 | d365-service-delivery-bu1 | CMP-36 | prod | public_cloud | public_cloud_region | INF-18 | container | - | d365-service-delivery-bu1-deployment |  |
| DEP-37 | d365-service-delivery-bu2 | CMP-37 | prod | public_cloud | public_cloud_region | INF-18 | container | - | d365-service-delivery-bu2-deployment |  |
| DEP-38 | d365-service-delivery-bu3 | CMP-38 | prod | public_cloud | public_cloud_region | INF-18 | container | - | d365-service-delivery-bu3-deployment |  |
| DEP-39 | edge-cache | CMP-39 | prod | public_cloud | public_cloud_region | INF-19 | container | - | edge-cache-deployment |  |
| DEP-40 | logistics partner A | CMP-40 | prod | private_cloud | data_center | INF-21 | container | - | logistics-partner-a-deployment |  |
| DEP-41 | logstics-vendor-1 | CMP-41 | prod | private_cloud | data_center | INF-21 | container | - | logstics-vendor-1-deployment |  |
| DEP-42 | logistics partner B | CMP-42 | prod | private_cloud | data_center | INF-21 | container | - | logistics-partner-b-deployment |  |
| DEP-43 | logistics partner C | CMP-43 | prod | private_cloud | data_center | INF-21 | container | - | logistics-partner-c-deployment |  |
| DEP-44 | logistics partner D | CMP-44 | prod | private_cloud | data_center | INF-21 | container | - | logistics-partner-d-deployment |  |
| DEP-45 | logistics partner E | CMP-45 | prod | private_cloud | data_center | INF-21 | container | - | logistics-partner-e-deployment |  |
| DEP-46 | file partner A | CMP-46 | prod | private_cloud | data_center | INF-23 | container | - | file-partner-a-deployment |  |
| DEP-47 | file partner B | CMP-47 | prod | private_cloud | data_center | INF-23 | container | - | file-partner-b-deployment |  |
| DEP-48 | file partner C | CMP-48 | prod | private_cloud | data_center | INF-23 | container | - | file-partner-c-deployment |  |

## R5 — Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | internet -> CMP-01 | internet | CMP-01 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | INF-03 INF-04 | |
| FLOW-02 | CMP-01 -> CMP-01 | CMP-01 | CMP-01 | HTTPS/TLS 1.3 | TBD | mTLS | TLS1.3 | 否 | INF-03 INF-04 INF-04 | |
| FLOW-03 | CMP-01 -> CMP-01 | CMP-01 | CMP-01 | HTTPS/TLS 1.3 | TBD | mTLS | TLS1.3 | 否 | INF-04 | |
| FLOW-04 | CMP-01 -> CMP-03 | CMP-01 | CMP-03 | HTTPS/TLS 1.3 | TBD | mTLS | TLS1.3 | 否 | - | |
| FLOW-05 | CMP-03 -> CMP-02 | CMP-03 | CMP-02 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-06 | CMP-02 -> CMP-04 | CMP-02 | CMP-04 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-07 | CMP-04 -> CMP-09 | CMP-04 | CMP-09 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-08 | CMP-04 -> CMP-10 | CMP-04 | CMP-10 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-09 | CMP-06 -> CMP-05 | CMP-06 | CMP-05 | Kafka/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-10 | CMP-07 -> CMP-05 | CMP-07 | CMP-05 | Kafka/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-11 | CMP-08 -> CMP-05 | CMP-08 | CMP-05 | Kafka/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-12 | CMP-09 -> CMP-05 | CMP-09 | CMP-05 | Kafka/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-13 | CMP-10 -> CMP-05 | CMP-10 | CMP-05 | Kafka/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-14 | CMP-06 -> CMP-12 | CMP-06 | CMP-12 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-15 | CMP-07 -> CMP-13 | CMP-07 | CMP-13 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-16 | CMP-08 -> CMP-13 | CMP-08 | CMP-13 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-17 | CMP-09 -> CMP-12 | CMP-09 | CMP-12 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-18 | CMP-09 -> CMP-13 | CMP-09 | CMP-13 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-19 | CMP-09 -> CMP-14 | CMP-09 | CMP-14 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-20 | CMP-09 -> CMP-15 | CMP-09 | CMP-15 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-21 | CMP-09 -> CMP-16 | CMP-09 | CMP-16 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-22 | CMP-10 -> CMP-12 | CMP-10 | CMP-12 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-23 | CMP-10 -> CMP-13 | CMP-10 | CMP-13 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-24 | CMP-10 -> CMP-14 | CMP-10 | CMP-14 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-25 | CMP-10 -> CMP-15 | CMP-10 | CMP-15 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-26 | CMP-10 -> CMP-16 | CMP-10 | CMP-16 | JDBC/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-27 | CMP-06 -> CMP-17 | CMP-06 | CMP-17 | Redis/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-28 | CMP-07 -> CMP-17 | CMP-07 | CMP-17 | Redis/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-29 | CMP-08 -> CMP-17 | CMP-08 | CMP-17 | Redis/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-30 | CMP-09 -> CMP-17 | CMP-09 | CMP-17 | Redis/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-31 | CMP-10 -> CMP-17 | CMP-10 | CMP-17 | Redis/TLS | TBD | none | TLS1.3 | 否 | - | |
| FLOW-32 | CMP-06 -> CMP-18 | CMP-06 | CMP-18 | AMQPS/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-33 | CMP-07 -> CMP-18 | CMP-07 | CMP-18 | AMQPS/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-34 | CMP-08 -> CMP-18 | CMP-08 | CMP-18 | AMQPS/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-35 | CMP-09 -> CMP-18 | CMP-09 | CMP-18 | AMQPS/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-36 | CMP-10 -> CMP-18 | CMP-10 | CMP-18 | AMQPS/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-37 | CMP-06 -> CMP-19 | CMP-06 | CMP-19 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-38 | CMP-07 -> CMP-19 | CMP-07 | CMP-19 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-39 | CMP-08 -> CMP-19 | CMP-08 | CMP-19 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-40 | CMP-09 -> CMP-19 | CMP-09 | CMP-19 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-41 | CMP-10 -> CMP-19 | CMP-10 | CMP-19 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-42 | CMP-06 -> CMP-31 | CMP-06 | CMP-31 | RFC/SNC | TBD | none | TBD | 否 | - | |
| FLOW-43 | CMP-07 -> CMP-31 | CMP-07 | CMP-31 | RFC/SNC | TBD | none | TBD | 否 | - | |
| FLOW-44 | CMP-08 -> CMP-31 | CMP-08 | CMP-31 | RFC/SNC | TBD | none | TBD | 否 | - | |
| FLOW-45 | CMP-09 -> CMP-31 | CMP-09 | CMP-31 | RFC/SNC | TBD | none | TBD | 否 | - | |
| FLOW-46 | CMP-10 -> CMP-31 | CMP-10 | CMP-31 | RFC/SNC | TBD | none | TBD | 否 | - | |
| FLOW-47 | CMP-31 -> CMP-32 | CMP-31 | CMP-32 | RFC/SNC | TBD | none | TBD | 否 | - | |
| FLOW-48 | CMP-31 -> CMP-33 | CMP-31 | CMP-33 | RFC/SNC | TBD | none | TBD | 否 | - | |
| FLOW-49 | CMP-31 -> CMP-34 | CMP-31 | CMP-34 | RFC/SNC | TBD | none | TBD | 否 | - | |
| FLOW-50 | CMP-06 -> CMP-35 | CMP-06 | CMP-35 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-51 | CMP-07 -> CMP-35 | CMP-07 | CMP-35 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-52 | CMP-08 -> CMP-35 | CMP-08 | CMP-35 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-53 | CMP-09 -> CMP-35 | CMP-09 | CMP-35 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-54 | CMP-10 -> CMP-35 | CMP-10 | CMP-35 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-55 | CMP-04 -> CMP-20 | CMP-04 | CMP-20 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-56 | CMP-04 -> CMP-21 | CMP-04 | CMP-21 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-57 | CMP-04 -> CMP-22 | CMP-04 | CMP-22 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-58 | CMP-04 -> CMP-23 | CMP-04 | CMP-23 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-59 | CMP-04 -> CMP-24 | CMP-04 | CMP-24 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-60 | CMP-04 -> CMP-25 | CMP-04 | CMP-25 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-61 | CMP-04 -> CMP-26 | CMP-04 | CMP-26 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-62 | CMP-05 -> CMP-27 | CMP-05 | CMP-27 | Kafka/TLS over IPsec private WAN | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-63 | CMP-04 -> CMP-28 | CMP-04 | CMP-28 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-64 | CMP-04 -> CMP-29 | CMP-04 | CMP-29 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-65 | CMP-04 -> CMP-30 | CMP-04 | CMP-30 | HTTPS/TLS 1.3 over IPsec private WAN | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-66 | CMP-04 -> CMP-36 | CMP-04 | CMP-36 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-67 | CMP-04 -> CMP-37 | CMP-04 | CMP-37 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-68 | CMP-04 -> CMP-38 | CMP-04 | CMP-38 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-69 | CMP-05 -> CMP-39 | CMP-05 | CMP-39 | Kafka/TLS | TBD | SASL_SCRAM | TLS1.3 | 否 | - | |
| FLOW-70 | CMP-04 -> CMP-40 | CMP-04 | CMP-40 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-71 | CMP-04 -> CMP-41 | CMP-04 | CMP-41 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-72 | CMP-04 -> CMP-42 | CMP-04 | CMP-42 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-73 | CMP-04 -> CMP-43 | CMP-04 | CMP-43 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-74 | CMP-04 -> CMP-44 | CMP-04 | CMP-44 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-75 | CMP-04 -> CMP-45 | CMP-04 | CMP-45 | HTTPS/TLS 1.3 | TBD | OAuth2_ClientCredentials | TLS1.3 | 否 | - | |
| FLOW-76 | CMP-11 -> CMP-46 | CMP-11 | CMP-46 | SFTP/SSH | TBD | ClientCertificate | TBD | 否 | - | |
| FLOW-77 | CMP-11 -> CMP-47 | CMP-11 | CMP-47 | SFTP/SSH | TBD | ClientCertificate | TBD | 否 | - | |
| FLOW-78 | CMP-11 -> CMP-48 | CMP-11 | CMP-48 | SFTP/SSH | TBD | ClientCertificate | TBD | 否 | - | |

## R6 — Infra network links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | dc-cn-primary -> dc-us | INF-01 | INF-07 | TBD | TBD | IPSec | TBD | named private WAN path; carrier and routing TBD; no direct cross-region database replication |
| LNK-02 | dc-cn-primary -> dc-cn-secondary | INF-01 | INF-11 | TBD | TBD | IPSec | TBD | named private WAN path; carrier and routing TBD; no direct cross-region database replication |
| LNK-03 | dc-cn-primary -> dc-cn-support | INF-01 | INF-13 | TBD | TBD | IPSec | TBD | named private WAN path; carrier and routing TBD; no direct cross-region database replication |
| LNK-04 | dc-cn-primary -> azure-us-satellites | INF-01 | INF-17 | TBD | TBD | IPSec | TBD | named private WAN path; carrier and routing TBD; no direct cross-region database replication |

## R7 — Auth

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | ADFS sign-in | user | CMP-01 | INF-09 | SAML2 | RBAC | 是 | internal STS fallback; trigger and role mapping TBD |
| AUTH-02 | Enterprise ID sign-in | user | CMP-01 | INF-10 | OIDC | RBAC | 是 | external partner users; tenant and role claims TBD |
