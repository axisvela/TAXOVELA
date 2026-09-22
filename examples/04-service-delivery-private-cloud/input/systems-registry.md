# Systems Registry — Service Delivery Platform (SDP)

Single source of truth for every system / service name in this example.

- **参考图不做脱敏**：`input/diagrams/reference-architecture.png` 保留原名。
- **文档只引用编号**：`prompt.md`、`requirements.md`、
  `README.md`、`config.yaml` 中所有系统/服务均以 `SYS-nn` 引用，不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **范围标记**：本表默认全部纳入设计范围；若某系统有意不纳入，在其「备注」列写上 `OUT-OF-SCOPE`，`registry_check` 便不再要求 `prompt.md` 引用它（用标记记录有意排除，而非沉默遗漏）。
- **手动脱敏流程**：直接修改下表「文档用名」列即可；编号不变，所有引用
  自动跟随，无需全局替换。

| 编号 | 参考图原名 | 类型 | 位置 | 文档用名 | 备注 |
|------|-----------|------|------|----------|------|
| SYS-01 | F5 | ingress | dc-cn-primary | F5 | TLS termination ingress |
| SYS-02 | Service-Supply-Chain-dmz-nginx-proxy (Nginx) | web | DMZ K8s | Service-Supply-Chain-dmz-nginx-proxy | DMZ reverse proxy |
| SYS-03 | Service-Supply-Chain-gateway (Java,SpringCloud) | backend | DMZ K8s | Service-Supply-Chain-gateway | DMZ API gateway service |
| SYS-04 | Service-Supply-Chain-web (Java,SpringCloud) | frontend | DMZ K8s | Service-Supply-Chain-web | DMZ frontend entry |
| SYS-05 | WSO2 | integration | Intranet | WSO2 | Internal API gateway mediator |
| SYS-06 | Kafka (primary DC cluster) | messaging | Intranet | Kafka (primary) | Primary event bus cluster |
| SYS-07 | Service-Supply-Chain-int-nginx-proxy (Nginx) | backend | Intranet K8s | Service-Supply-Chain-int-nginx-proxy | Intranet reverse proxy |
| SYS-08 | Service-Supply-Chain-main (Java,SpringCloud) | backend | Intranet K8s | Service-Supply-Chain-main | Core service entry |
| SYS-09 | Service-Supply-Chain-websocket (Java,SpringCloud) | backend | Intranet K8s | Service-Supply-Chain-websocket | Push websocket service |
| SYS-10 | Service-Supply-Chain-service-group-1 | backend group | Intranet K8s | Service-Supply-Chain-* group (10 services) | 10-service backend group, members in requirements §2 |
| SYS-11 | Service-Supply-Chain-service-group-2 | backend group | Intranet K8s | Service-Supply-Chain-* group (22 services) | 22-service backend group, members in requirements §2 |
| SYS-12 | TMS MySQL HA GRP | database | DB Zone | MySQL TMS | Relational HA group 1M+2S |
| SYS-13 | Main MySQL HA GRP | database | DB Zone | MySQL Main | Relational HA group 1M+2S |
| SYS-14 | WMS MySQL HA GRP | database | DB Zone | MySQL WMS | Relational HA group 1M+2S |
| SYS-15 | MDS MySQL HA GRP | database | DB Zone | MySQL MDS | Relational HA group 1M+2S |
| SYS-16 | OMS MySQL HA GRP | database | DB Zone | MySQL OMS | Relational HA group 1M+2S |
| SYS-17 | Redis HA GRP | cache | DB Zone | Redis HA | Cache HA 3M+3S |
| SYS-18 | RabbitMQ HA GRP | messaging | DB Zone | RabbitMQ HA | Messaging HA 3 replicas |
| SYS-19 | ES HA GRP | database | DB Zone | Elasticsearch HA | Search HA 3 nodes |
| SYS-20 | S4 | erp | SAP landscape | S4 | SAP ERP hub |
| SYS-21 | Service-ECC | erp | SAP landscape | SECC | SAP ERP component |
| SYS-22 | Service-CRM | erp | SAP landscape | LSCRM | SAP ERP component |
| SYS-23 | Core-ECC | erp | SAP landscape | CECC | SAP ERP component |
| SYS-24 | S3 | storage | SAP landscape | S3 | SAP object storage |
| SYS-25 | Account-Service | backend | dc-us | Account-Service | US satellite backend |
| SYS-26 | Service-customer-master-data | backend | dc-us | Service-customer-master-data | US satellite backend |
| SYS-27 | Serice-Data-service | backend | dc-us | Serice-Data-serviceE | US satellite backend |
| SYS-28 | Price-master-ROW | backend | dc-us | Price-master-ROW | US satellite backend |
| SYS-29 | ADFS | identity | dc-us | ADFS | Internal SSO |
| SYS-30 | External-IdP | identity | dc-us | Enterprise ID | External-IdP brand scrubbed |
| SYS-31 | Reverse-Management-System | backend | dc-cn-secondary | Reverse-Management-System | Secondary DC backend |
| SYS-32 | procurement-service | backend | dc-cn-secondary | procurement-service | Secondary DC backend |
| SYS-33 | Data-lake-platform | data | dc-cn-secondary | lakehouse | Data platform codename scrubbed |
| SYS-34 | Kafka (secondary DC cluster) | messaging | dc-cn-secondary | Kafka (secondary) | Secondary event bus cluster |
| SYS-35 | Reverse-planning | backend | dc-cn-secondary | support-hub | Codename scrubbed |
| SYS-36 | Service-Support | backend | dc-cn-support | support-portal | Brand scrubbed |
| SYS-37 | Service-portal | backend | dc-cn-support | support-gateway | Codename scrubbed |
| SYS-38 | d365-service-delivery-bu1 | saas | azure | d365-service-delivery-bu1 | SaaS app name kept |
| SYS-39 | d365-service-delivery-bu2 | saas | azure | d365-service-delivery-bu2 | SaaS app name kept |
| SYS-40 | d365-service-delivery-bu3 | saas | azure | d365-service-delivery-bu3 | SaaS app name kept |
| SYS-41 | ecomm-cache | backend | azure | edge-cache | Codename scrubbed |
| SYS-42 | Aremax | external | Internet 3PL | logistics partner A | Carrier brand scrubbed |
| SYS-43 | logstics-vendor-1 | external | Internet 3PL | logstics-vendor-1 | Carrier brand scrubbed |
| SYS-44 | DHL | external | Internet 3PL | logistics partner B | Carrier brand scrubbed |
| SYS-45 | YCH | external | Internet 3PL | logistics partner C | Carrier brand scrubbed |
| SYS-46 | TECHWAH | external | Internet 3PL | logistics partner D | Carrier brand scrubbed |
| SYS-47 | UPS | external | Internet 3PL | logistics partner E | Carrier brand scrubbed |
| SYS-48 | Phoenix | external | partner file hub SFTP | file partner A | File-transfer partner brand scrubbed |
| SYS-49 | GSPP | external | partner file hub SFTP | file partner B | File-transfer partner brand scrubbed |
| SYS-50 | SFJ | external | partner file hub SFTP | file partner C | File-transfer partner brand scrubbed |
| SYS-51 | Axway | integration | Intranet | MFT platform | Managed file transfer; vendor scrubbed |
| SYS-52 | container-ingress | network | dc-cn-primary | Edge router | Router codename scrubbed |
