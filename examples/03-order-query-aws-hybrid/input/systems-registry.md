# Systems Registry — Order Query Platform (OVP ROW)

Single source of truth for every system / service name in this example. This
is the only file that contains literal entity names.

- **Reference diagram is not scrubbed**: the image remains unchanged and is
  not copied into this text registry.
- **Codes-only documents**: `prompt.md`, `requirements.md`, `cmdb-export.csv`,
  `README.md`, and config notes refer to `SYS-nn` codes only.
- **Manual scrub workflow**: edit only the 「文档用名」 cell below; never
  renumber an existing row. All references follow automatically.
- **Scope marker**: every row is in design scope by default. To exclude a
  system deliberately, write `OUT-OF-SCOPE` in its Notes column — then
  `registry_check` stops requiring `prompt.md` to reference it. This records
  a deliberate exclusion instead of a silent omission.

| 编号 | 源提示词名称 | 类型 | 位置 | 文档用名 | 备注 |
|------|-----------|------|------|----------|------|
| SYS-01 | ADFS | identity | dc-us | ADFS | 内部 SSO |
| SYS-02 | Enterprise ID | identity | dc-us | Enterprise ID | 外部 IdP；已在源提示词中脱敏 |
| SYS-03 | SOWB(sales operation workbench) | portal | dc-us DMZ | SOWB(sales operation workbench) | 内部门户 |
| SYS-04 | external OP(order portal) site | portal | dc-us DMZ | external OP(order portal) site | 外部门户 |
| SYS-05 | OP(order portal)-row-web (Nginx/React) | frontend | aws-us public subnet | OP(order portal)-row-web | 前端 K8s 集群 |
| SYS-06 | Gateway | backend | aws-us app zone | Gateway | 后端 K8s 网关 |
| SYS-07 | Order Portal | backend | aws-us | Order Portal | Java/Spring |
| SYS-08 | Order Report | backend | aws-us | Order Report | Java/Spring |
| SYS-09 | Order Notification | backend | aws-us | Order Notification | Java/Spring |
| SYS-10 | Transform Service | backend | aws-us | Transform Service | Java/Spring |
| SYS-11 | Task Service | backend | aws-us | Task Service | Java/Spring |
| SYS-12 | Order Web | frontend | aws-us | Order Web | React |
| SYS-13 | D365  Consumer | consumer | aws-us | D365 Consumer | Kafka 消费者 |
| SYS-14 | OFS(order fulfill service) Consumer | consumer | aws-us |  OFS(order fulfill service) Consumer | Kafka 消费者 |
| SYS-15 | PRC Consumer | consumer | aws-us | PRC Consumer | Kafka 消费者 |
| SYS-16 | SOS(salse order servie) Consumer | consumer | aws-us | SOS(salse order servie) Consumer | Kafka 消费者 |
| SYS-17 | IC(invoice service) Consumer | consumer | aws-us | IC(invoice service) Consumer | Kafka 消费者 |
| SYS-18 | LOS(logistics operation servie) Consumer | consumer | aws-us | LOS(logistics operation servie) Consumer | Kafka 消费者 |
| SYS-19 | SDS(service data service) Consumer | consumer | aws-us | SDS(service data service) Consumer | Kafka 消费者 |
| SYS-20 | SIS(supply intelligence service) Consumer | consumer | aws-us | SIS(supply intelligence service) Consumer | Kafka 消费者 |
| SYS-21 | NA Consumer | consumer | aws-us | NA Consumer | Kafka 消费者 |
| SYS-22 | Consumer Task | backend | aws-us | Consumer Task | Java/Spring |
| SYS-23 | XXL-Job scheduler | backend | aws-us | XXL-Job scheduler | 调度（公开 OSS 名） |
| SYS-24 | SOS(salse order servie) | backend | aws-us | SOS(salse order servie) | CMDB A-XXXX-05 |
| SYS-25 | PostgreSQL ODS | database | aws-us db zone | PostgreSQL ODS | ODS 库 |
| SYS-26 | PostgreSQL DWS | database | aws-us db zone | PostgreSQL DWS | DWS 库 |
| SYS-27 | Redis | cache | aws-us db zone | Redis | 缓存 |
| SYS-28 | S3 | storage | aws-us | S3 | AWS 对象存储 |
| SYS-29 | DMZ-APIM | integration | dc-us | DMZ-APIM | 外部 API 网关 |
| SYS-30 | APIM | integration | dc-us | APIM | 内部 API 网关 |
| SYS-31 | APIH | integration | dc-us-na INTEGRATION | APIH | NA 集成网关 |
| SYS-32 | kafka-us | messaging | dc-us | kafka-us | Kafka 集群；已在源提示词中脱敏 |
| SYS-33 | kafka-cn | messaging | dc-cn-primary | kafka-cn | Kafka 集群；已在源提示词中脱敏 |
| SYS-34 | kafka-ikp | messaging | dc-cn-secondary | kafka-ikp | Kafka 集群；已在源提示词中脱敏 |
| SYS-35 | kafka-us-na | messaging | dc-us-na INTEGRATION | kafka-us-na | Kafka 集群；已在源提示词中脱敏 |
| SYS-36 | kafka-us-log | messaging | dc-us-na INTEGRATION | kafka-us-log | Kafka 集群；已在源提示词中脱敏 |
| SYS-37 | OP(order portal) ES | database | dc-us-na db zone | OP(order portal) ES | Elasticsearch（存量） |
| SYS-38 | SDS(service data service) | backend | dc-us | SDS(service data service) | CMDB A-XXXX-01 |
| SYS-39 | 2B service portal | backend | dc-us | 2b service portal | CMDB A-XXXX-02 |
| SYS-40 | OOP(order open platform) | backend | dc-us | OOP(order open platform) | CMDB A-XXXX-03 |
| SYS-41 | order orchestration | backend | dc-us | order orchestration | CMDB A-XXXX-04 |
| SYS-42 | CSP(cload servie portal) | backend | dc-cn-secondary | CSP(cload servie portal) | CMDB A-XXXX-10 |
| SYS-43 | IC(invoice service) | backend | dc-cn-secondary | IC(invoice service) | CMDB A-XXXX-11 |
| SYS-44 | LOS(logistics operation servie) | backend | dc-cn-secondary | LOS(logistics operation servie) | CMDB A-XXXX-12 |
| SYS-45 | Lakehouse | data | dc-cn-secondary | Lakehouse | 已在源提示词中脱敏；CMDB A-XXXX-13 |
| SYS-46 | OP(order portal)-PRC | backend | dc-cn-secondary | OP(order portal)-PRC | CMDB A-XXXX-14 |
| SYS-47 | SIS(supply intelligence service) | backend | dc-cn-secondary | SIS(supply intelligence service) | CMDB A-XXXX-15 |
| SYS-48 | GAP(general account platform)-OTC | backend | dc-cn-primary | GAP(general account platform)-OTC | CMDB A-XXXX-16 |
| SYS-49 | ECC | erp | dc-cn-primary | ECC | SAP；CMDB A-XXXX-17 |
| SYS-50 | IC(invoice service)-NA | backend | dc-us-na | IC(invoice service)-NA | CMDB A-XXXX-18 |
| SYS-51 | SIS(supply intelligence service)-NA | backend | dc-us-na | SIS(supply intelligence service)-NA | CMDB A-XXXX-19 |
| SYS-52 | GAP(general account platform)-OTC-NA | backend | dc-us-na | GAP(general account platform)-OTC-NA | CMDB A-XXXX-20 |
| SYS-53 | Lakehouse-ROW | data | dc-us-na | Lakehouse-ROW | 已在源提示词中脱敏；CMDB A-XXXX-21 |
| SYS-54 | D365 | saas | azure-us | D365 | 公开 SaaS；CMDB A-XXXX-06 |
| SYS-55 | edge-cache | backend | azure-us | edge-cache | 已在源提示词中脱敏；CMDB A-XXXX-07 |
| SYS-56 | ROW DWP(data warehosue platform) | data | azure-us | ROW DWP(data warehosue platform) | 已在源提示词中脱敏；CMDB A-XXXX-08 |
| SYS-57 | PRC DWP(data warehosue platform) | data | azure-cn-north | PRC DWP(data warehosue platform) | 已在源提示词中脱敏；CMDB A-XXXX-09 |
| SYS-58 | Internal K8s Platform | platform | all K8s clusters | Internal K8s Platform | 已在源提示词中脱敏 |
