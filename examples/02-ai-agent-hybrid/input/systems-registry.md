# Systems Registry — Data Agent Platform (Hybrid)

Single source of truth for every system / service name in this example.

- **参考图不做脱敏**：`input/diagrams/reference-architecture.png` 保留原名。
- **文档只引用编号**：`prompt.md`、`requirements.md`、`README.md` 中所有系统/服务均以 `SYS-nn` 引用，不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **范围标记**：本表默认全部纳入设计范围；若某系统有意不纳入，在其「备注」列写上 `OUT-OF-SCOPE`，`registry_check` 便不再要求 `prompt.md` 引用它（用标记记录有意排除，而非沉默遗漏）。
- **手动脱敏流程**：直接修改下表「文档用名」列即可；编号不变，所有引用自动跟随，无需全局替换。

The reference diagram itself is NOT scrubbed — that is why 参考图原名 keeps originals.

| 编号 | 参考图原名 | 类型 | 位置 | 文档用名 | 备注 |
|------|-----------|------|------|----------|------|
| SYS-01 | GDA Gateway + Dashboard UI (nginx: static hosting + API proxy) | web | dc-cn-primary App Zone (K8s) | gda-gateway | Web entry, static hosting + API proxy |
| SYS-02 | GDA Agent API, SSE, Agent Tools (Node.js) | backend | dc-cn-primary App Zone (K8s) | gda-agent-api | Agent runtime API with streaming |
| SYS-03 | GDA Scheduler Worker alerts, digests (Node.js) | backend | dc-cn-primary App Zone (K8s) | gda-scheduler-worker | Background worker for alerts and digests |
| SYS-04 | PostgreSQL (DB Zone) | database | dc-cn-primary DB Zone | PostgreSQL | Relational database, App Zone access only |
| SYS-05 | Nginx (outbound gateway to Azure), VM Rocky 9.8 | integration | dc-cn-primary App Zone | Outbound gateway | Sole DC-to-Azure egress path |
| SYS-06 | ADFS | identity | dc-cn-primary | ADFS | Internal STS fallback provider |
| SYS-07 | Entra ID | identity | Azure | Microsoft Entra ID | Primary user auth provider |
| SYS-08 | magellan-edw-row-databricks-prod / Magellan EDW Data | data | azure-eastus | EDW Databricks | Governed data source in East US |
| SYS-09 | LLM Gateway (overseas / China pool) | ai-platform | azure-eastus2 | LLM Gateway | Dual-pool model service, private endpoint only |
| SYS-10 | Earth K8S | platform | dc-cn-primary | Internal K8s Platform | Container platform for App Zone |
