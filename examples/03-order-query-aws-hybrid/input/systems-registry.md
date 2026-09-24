# Systems Registry — Order Query Platform (OQP ROW)

This req/v2 registry is the authoritative inventory for this example. The reference
image is restricted input and intentionally retains its original labels. All prose
outside this file uses typed identifiers only.

## R1 — Infra nodes

| 编号 | 参考图原名 | node_kind | infra_type | network_type | 父节点 | 位置/国家 | 文档用名 | 备注 |
|------|-----------|-----------|------------|--------------|--------|-----------|----------|------|
| INF-01 | AWS US VPC | iaas_vpc_vnet | public_cloud | prod_network | - | US | aws-vpc-ref | N. Virginia production VPC |
| INF-02 | Public subnet (DMZ) | subnet | public_cloud | dmz | INF-01 | US | aws-public-dmz | frontend ingress subnet |
| INF-03 | Private subnet (App Zone) | subnet | public_cloud | prod_network | INF-01 | US | aws-app-zone | backend runtime subnet |
| INF-04 | Private subnet (DB Zone) | subnet | public_cloud | prod_network | INF-01 | US | aws-db-zone | data subnet |
| INF-05 | AWS WAF and ALB | waf | public_cloud | dmz | INF-02 | US | aws-waf | public ingress appliance |
| INF-06 | AWS DMZ boundary firewall | firewall | public_cloud | dmz | INF-02 | US | aws-dmz-firewall | DMZ to application control |
| INF-07 | AWS App boundary firewall | firewall | public_cloud | prod_network | INF-03 | US | aws-app-firewall | application to data and WAN control |
| INF-08 | AWS KMS | key_management | public_cloud | prod_network | INF-01 | US | aws-kms | key store for AWS data services |
| INF-09 | dc-us | data_center | private_cloud | prod_network | - | US | us-dc | US identity and source DC |
| INF-10 | dc-us DMZ | network_zone | private_cloud | dmz | INF-09 | US | us-dmz | portal and external mediation zone |
| INF-11 | dc-us Boundary Firewall | firewall | private_cloud | dmz | INF-10 | US | us-boundary-firewall | DC boundary control |
| INF-12 | ADFS | identity_provider | private_cloud | prod_network | INF-09 | US | adfs | internal SSO appliance |
| INF-13 | Enterprise ID | identity_provider | third_party | prod_network | INF-09 | US | enterprise-id | partner identity boundary |
| INF-14 | dc-us-na | data_center | private_cloud | prod_network | - | US | na-dc | NA source DC |
| INF-15 | NA-PROD-INA-INTEGRATION | network_zone | private_cloud | prod_network | INF-14 | US | na-integration-zone | API and Kafka mediation |
| INF-16 | NA-PROD-INA-K8S | network_zone | private_cloud | prod_network | INF-14 | US | na-k8s-zone | existing workloads |
| INF-17 | NA-PROD-INA-DB | network_zone | private_cloud | prod_network | INF-14 | US | na-db-zone | existing data stores |
| INF-18 | dc-us-na Boundary Firewall | firewall | private_cloud | prod_network | INF-14 | US | na-boundary-firewall | DC boundary control |
| INF-19 | dc-cn-primary | data_center | private_cloud | prod_network | - | CN | cn-primary-dc | PRC primary DC |
| INF-20 | dc-cn-primary DMZ | network_zone | private_cloud | dmz | INF-19 | CN | cn-primary-dmz | PRC boundary zone |
| INF-21 | dc-cn-primary Intranet | network_zone | private_cloud | prod_network | INF-19 | CN | cn-primary-intranet | PRC application zone |
| INF-22 | dc-cn-primary Boundary Firewall | firewall | private_cloud | dmz | INF-20 | CN | cn-primary-firewall | blocks PRC row egress |
| INF-23 | dc-cn-secondary | data_center | private_cloud | prod_network | - | CN | cn-secondary-dc | PRC secondary DC |
| INF-24 | dc-cn-secondary DMZ | network_zone | private_cloud | dmz | INF-23 | CN | cn-secondary-dmz | PRC boundary zone |
| INF-25 | dc-cn-secondary Intranet | network_zone | private_cloud | prod_network | INF-23 | CN | cn-secondary-intranet | PRC application zone |
| INF-26 | dc-cn-secondary Boundary Firewall | firewall | private_cloud | dmz | INF-24 | CN | cn-secondary-firewall | blocks PRC row egress |
| INF-27 | Azure US | iaas_vpc_vnet | public_cloud | prod_network | - | US | azure-us-boundary | existing Azure source boundary |
| INF-28 | Azure CN North | iaas_vpc_vnet | public_cloud | prod_network | - | CN | azure-cn-boundary | PRC EDW boundary |

The internal K8s platform is a runtime substrate, not a topology appliance or a
component. It is recorded in R4 `runtime_detail` only.

## R2 — Systems

| 编号 | 参考图原名 | type | owner | vendor | 文档用名 | 备注 |
|------|-----------|------|-------|--------|----------|------|
| APP-01 | Order Query Platform | new | org_it | - | oqp | AWS-hosted application |
| APP-02 | US source systems | existing | org_it | - | us-sources | integration boundary only |
| APP-03 | NA source systems | existing | org_it | - | na-sources | integration boundary only |
| APP-04 | PRC primary source systems | existing | org_it | - | cn-primary-sources | integration boundary only |
| APP-05 | PRC secondary source systems | existing | org_it | - | cn-secondary-sources | integration boundary only |
| APP-06 | Azure and SaaS sources | existing | org_it | Microsoft | azure-sources | integration boundary only |
| APP-07 | Existing portal entry systems | existing | org_it | - | portal-entries | integration boundary only |

## R3 — Components / services

| 编号 | 参考图原名 | 所属系统 | 子系统 | kind | layer | component_role | 静态加密 | 文档用名 | 备注 |
|------|-----------|----------|--------|------|-------|----------------|----------|----------|------|
| CMP-01 | OP-row-web | APP-01 | web | component | fe | web_frontend | - | order-web | frontend K8s runtime |
| CMP-02 | Gateway | APP-01 | gateway | component | api | api_gateway | - | gateway | backend K8s runtime |
| CMP-03 | Order Portal | APP-01 | order | service | be | backend_service | - | order-portal | Java/Spring |
| CMP-04 | Order Report | APP-01 | report | service | be | backend_service | - | order-report | Java/Spring |
| CMP-05 | Order Notification | APP-01 | notification | service | be | backend_service | - | order-notification | Java/Spring |
| CMP-06 | Transform Service | APP-01 | transform | service | be | data_processing | - | transform-service | Java/Spring |
| CMP-07 | Task Service | APP-01 | task | service | be | backend_service | - | task-service | Java/Spring |
| CMP-08 | Order Web | APP-01 | web | component | fe | web_frontend | - | order-ui | React |
| CMP-09 | D365 Consumer | APP-01 | consumers | service | be | streaming_processing | - | d365-consumer | Kafka consumer |
| CMP-10 | OFS Consumer | APP-01 | consumers | service | be | streaming_processing | - | ofs-consumer | Kafka consumer |
| CMP-11 | PRC Consumer | APP-01 | consumers | service | be | streaming_processing | - | prc-consumer | Kafka consumer |
| CMP-12 | SOS Consumer | APP-01 | consumers | service | be | streaming_processing | - | sos-consumer | Kafka consumer |
| CMP-13 | IC Consumer | APP-01 | consumers | service | be | streaming_processing | - | ic-consumer | Kafka consumer |
| CMP-14 | LOS Consumer | APP-01 | consumers | service | be | streaming_processing | - | los-consumer | Kafka consumer |
| CMP-15 | SDS Consumer | APP-01 | consumers | service | be | streaming_processing | - | sds-consumer | Kafka consumer |
| CMP-16 | SIS Consumer | APP-01 | consumers | service | be | streaming_processing | - | sis-consumer | Kafka consumer |
| CMP-17 | NA Consumer | APP-01 | consumers | service | be | streaming_processing | - | na-consumer | Kafka consumer |
| CMP-18 | Consumer Task | APP-01 | consumers | service | be | batch_processing | - | consumer-task | scheduled task |
| CMP-19 | XXL-Job scheduler | APP-01 | ops | service | be | batch_processing | - | scheduler | HA topology TBD |
| CMP-20 | SOS | APP-02 | source | component | ip | integration_service | - | sos-us | US source boundary |
| CMP-21 | PostgreSQL ODS | APP-01 | data | component | db | database | TBD | ods-db | AWS database |
| CMP-22 | PostgreSQL DWS | APP-01 | data | component | db | data_warehouse | TBD | dws-db | AWS warehouse |
| CMP-23 | Redis | APP-01 | data | component | db | cache | TBD | cache | AWS cache |
| CMP-24 | S3 | APP-01 | data | component | db | object_storage | TBD | object-store | AWS object storage |
| CMP-25 | DMZ-APIM | APP-07 | integration | component | ip | api_gateway | - | dmz-apim | external mediation |
| CMP-26 | APIM | APP-02 | integration | component | ip | api_gateway | - | us-apim | internal mediation |
| CMP-27 | APIH | APP-03 | integration | component | ip | integration_service | - | na-apih | NA mediation |
| CMP-28 | kafka-us | APP-02 | messaging | component | mq | message_bus | TBD | us-kafka | US mediation |
| CMP-29 | kafka-cn | APP-04 | messaging | component | mq | message_bus | TBD | cn-primary-kafka | PRC primary mediation |
| CMP-30 | kafka-ikp | APP-05 | messaging | component | mq | message_bus | TBD | cn-secondary-kafka | PRC secondary mediation |
| CMP-31 | kafka-us-na | APP-03 | messaging | component | mq | message_bus | TBD | na-kafka | NA mediation |
| CMP-32 | kafka-us-log | APP-03 | messaging | component | mq | message_bus | TBD | na-log-kafka | NA mediation |
| CMP-33 | Order Portal ES | APP-03 | data | component | db | database | TBD | na-search | existing search store |
| CMP-34 | SDS | APP-02 | source | component | ip | integration_service | - | sds-us | US source boundary |
| CMP-35 | 2B service portal | APP-02 | source | component | ip | integration_service | - | b2b-us | US source boundary |
| CMP-36 | OOP | APP-02 | source | component | ip | integration_service | - | oop-us | US source boundary |
| CMP-37 | order orchestration | APP-02 | source | component | ip | integration_service | - | orchestration-us | US source boundary |
| CMP-38 | CSP | APP-05 | source | component | ip | integration_service | - | csp-cn | PRC source boundary |
| CMP-39 | IC | APP-05 | source | component | ip | integration_service | - | ic-cn | PRC source boundary |
| CMP-40 | LOS | APP-05 | source | component | ip | integration_service | - | los-cn | PRC source boundary |
| CMP-41 | Lakehouse | APP-05 | source | component | ip | integration_service | - | lakehouse-cn | PRC source boundary |
| CMP-42 | OP-PRC | APP-05 | source | component | ip | integration_service | - | op-prc | PRC source boundary |
| CMP-43 | SIS | APP-05 | source | component | ip | integration_service | - | sis-cn | PRC source boundary |
| CMP-44 | GAP-OTC | APP-04 | source | component | ip | integration_service | - | gap-cn | PRC source boundary |
| CMP-45 | ECC | APP-04 | source | component | ip | integration_service | - | ecc-cn | ERP boundary |
| CMP-46 | IC-NA | APP-03 | source | component | ip | integration_service | - | ic-na | NA source boundary |
| CMP-47 | SIS-NA | APP-03 | source | component | ip | integration_service | - | sis-na | NA source boundary |
| CMP-48 | GAP-OTC-NA | APP-03 | source | component | ip | integration_service | - | gap-na | NA source boundary |
| CMP-49 | Lakehouse-ROW | APP-03 | source | component | ip | integration_service | - | lakehouse-na | NA source boundary |
| CMP-50 | D365 | APP-06 | source | component | ip | integration_service | - | d365 | SaaS boundary |
| CMP-51 | edge-cache | APP-06 | source | component | ip | integration_service | - | edge-cache | Azure US boundary |
| CMP-52 | ROW DWP | APP-06 | source | component | ip | integration_service | - | row-dwp | Azure US boundary |
| CMP-53 | PRC DWP | APP-06 | source | component | ip | integration_service | - | prc-dwp | Azure CN boundary |
| CMP-54 | SOWB | APP-07 | portal | component | fe | web_frontend | - | internal-portal | internal entry |
| CMP-55 | external OP site | APP-07 | portal | component | fe | web_frontend | - | partner-portal | partner entry |

## R4 — Deployments

| 编号 | 参考图原名 | 组件 | 环境 | deployment_type | location_type | infra 节点 | runtime_type | 实例数 | 文档用名 | 备注 |
|------|-----------|------|------|-----------------|---------------|-----------|--------------|--------|----------|------|
| DEP-01 | frontend pods | CMP-01 | prod | public_cloud | public_cloud_region | INF-02 | container | 2 | frontend-aws | internal K8s platform |
| DEP-02 | backend pods | CMP-02 | prod | public_cloud | public_cloud_region | INF-03 | container | 2 | gateway-aws | internal K8s platform |
| DEP-03 | application services | CMP-03 through CMP-19 | prod | public_cloud | public_cloud_region | INF-03 | container | 2 | app-services-aws | individual deployment records are represented in req.yaml |
| DEP-20 | US source boundaries | CMP-20, CMP-26, CMP-28, CMP-34 through CMP-37 | prod | private_cloud | data_center | INF-09 | vm | 1 | us-source-deps | existing |
| DEP-21 | AWS data services | CMP-21 through CMP-24 | prod | public_cloud | public_cloud_region | INF-04 | serverless | 1 | aws-data-deps | managed service selection TBD |
| DEP-22 | DMZ entry | CMP-25, CMP-54, CMP-55 | prod | private_cloud | data_center | INF-10 | vm | 1 | us-dmz-deps | existing |
| DEP-23 | NA mediation and sources | CMP-27, CMP-31, CMP-32, CMP-33, CMP-46 through CMP-49 | prod | private_cloud | data_center | INF-14 | vm | 1 | na-deps | existing |
| DEP-24 | PRC primary sources | CMP-29, CMP-44, CMP-45 | prod | private_cloud | data_center | INF-19 | vm | 1 | cn-primary-deps | existing |
| DEP-25 | PRC secondary sources | CMP-30, CMP-38 through CMP-43 | prod | private_cloud | data_center | INF-23 | vm | 1 | cn-secondary-deps | existing |
| DEP-26 | Azure sources | CMP-50 through CMP-52 | prod | public_cloud | public_cloud_region | INF-27 | serverless | 1 | azure-us-deps | existing |
| DEP-27 | Azure CN source | CMP-53 | prod | public_cloud | public_cloud_region | INF-28 | serverless | 1 | azure-cn-dep | in-country only |

## R5 — Component flows

| 编号 | 参考图原名 | 发起组件 | 提供组件 | protocol | port | auth_method | 加密 | 跨境 | via | 备注 |
|------|-----------|----------|----------|----------|------|-------------|------|------|-----|------|
| FLOW-01 | browser ingress | internet | CMP-01 | HTTPS | 443 | none | TLS1.2 | 否 | INF-05 | user auth in AUTH-01/AUTH-02 |
| FLOW-02 | frontend to gateway | CMP-01 | CMP-02 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.2 | 否 | INF-06 | allow-listed route |
| FLOW-03 | gateway to app services | CMP-02 | CMP-03 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.2 | 否 | - | representative service flow |
| FLOW-04 | order portal to ODS | CMP-03 | CMP-21 | PostgreSQL | 5432 | UserPassword | TLS1.2 | 否 | INF-07 | AWS Secrets Manager credential |
| FLOW-05 | report to DWS | CMP-04 | CMP-22 | PostgreSQL | 5432 | UserPassword | TLS1.2 | 否 | INF-07 | AWS Secrets Manager credential |
| FLOW-06 | portal to cache | CMP-03 | CMP-23 | Redis | 6379 | UserPassword | TLS1.2 | 否 | INF-07 | AWS Secrets Manager credential |
| FLOW-07 | report to object store | CMP-04 | CMP-24 | HTTPS | 443 | IAM_Role | TLS1.2 | 否 | - | private endpoint |
| FLOW-08 | internal mediation | CMP-02 | CMP-26 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.2 | 否 | INF-11 | mandatory mediation |
| FLOW-09 | NA mediation | CMP-02 | CMP-27 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.2 | 否 | INF-18 | mandatory mediation |
| FLOW-10 | PRC consumer mediation | CMP-11 | CMP-30 | Kafka | 9093 | SASL_SCRAM | TLS1.2 | 是 | INF-26 | requests only; no PRC row replication |
| FLOW-11 | PRC in-country query | CMP-30 | CMP-53 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.2 | 否 | - | data remains in China |
| FLOW-12 | external mediation | internet | CMP-25 | HTTPS | 443 | OAuth2_ClientCredentials | TLS1.2 | 否 | INF-11 | external source entry |

## R6 — Infra network links

| 编号 | 参考图原名 | 源 infra | 目标 infra | method | 带宽 | 加密 | 管理方 | 备注 |
|------|-----------|----------|------------|--------|------|------|--------|------|
| LNK-01 | dc-us to AWS | INF-09 | INF-01 | mpls | TBD | 是 | TBD | application TLS required |
| LNK-02 | dc-us-na to AWS | INF-14 | INF-01 | mpls | TBD | 是 | TBD | application TLS required |
| LNK-03 | dc-cn-primary to AWS | INF-19 | INF-01 | mpls | TBD | 是 | TBD | PRC row payload prohibited |
| LNK-04 | dc-cn-secondary to AWS | INF-23 | INF-01 | mpls | TBD | 是 | TBD | PRC row payload prohibited |

## R7 — Auth

| 编号 | 参考图原名 | subject | 适用入口 | auth_server | protocol | authorization | MFA | 备注 |
|------|-----------|---------|----------|-------------|----------|---------------|-----|------|
| AUTH-01 | employee SSO | user | CMP-01 | INF-12 | SAML2 | RBAC | 是 | internal employee entry |
| AUTH-02 | partner SSO | user | CMP-01 | INF-13 | SAML2 | RBAC | 是 | external partner entry |
