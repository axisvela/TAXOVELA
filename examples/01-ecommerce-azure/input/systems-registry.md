# Systems Registry — E-commerce Platform (Azure)

Single source of truth for every system / service name in this example.

- **参考图不做脱敏**：`input/diagrams/reference-architecture.png` 保留原名。
- **文档只引用编号**：`prompt.md`、`requirements.md`、`README.md`、`config.yaml`
  中所有系统/服务均以 `SYS-nn` 引用，不直接写名字。
- **唯一具名文件**：本注册表是唯一出现具名实体的文件。
- **范围标记**：本表默认全部纳入设计范围；若某系统有意不纳入，在其「备注」列写上 `OUT-OF-SCOPE`，`registry_check` 便不再要求 `prompt.md` 引用它（用标记记录有意排除，而非沉默遗漏）。
- **手动脱敏流程**：直接修改下表「文档用名」列即可；编号不变，所有引用
  自动跟随，无需全局替换。

| 编号 | 参考图原名 | 类型 | 位置 | 文档用名 | 备注 |
|------|-----------|------|------|----------|------|
| SYS-01 | vNet-eCom-CoreService-EUS | network | azure-eastus | vnet-ecom-coreservice-eus | EastUS hub VNet, firewall egress |
| SYS-02 | EastUS-VNET-A-BU | network | azure-eastus | vnet-ecom-bu-eus | EastUS BU spoke VNet |
| SYS-03 | EastUS-VNET-Common | network | azure-eastus | vnet-ecom-common-eus | EastUS shared-services spoke VNet |
| SYS-04 | VNET-Flash-CoreService-AP-Prod | network | azure-japaneast | vnet-ecom-coreservice-ap | JapanEast hub VNet, firewall egress |
| SYS-05 | Vnet-Flash-AP-Prod | network | azure-japaneast | vnet-ecom-ap-prod | JapanEast AP spoke VNet |
| SYS-06 | AzureFirewallSubnet firewall | security | SYS-01 | Azure Firewall (EastUS) | Hub firewall instance, forced egress |
| SYS-07 | GatewaySubnet gateway | network | SYS-01 | ExpressRoute gateway (EastUS) | Hub hybrid gateway |
| SYS-08 | AzureFirewallSubnet firewall | security | SYS-04 | Azure Firewall (JapanEast) | Hub firewall instance, forced egress |
| SYS-09 | GatewaySubnet gateway | network | SYS-04 | ExpressRoute gateway (JapanEast) | Hub hybrid gateway |
| SYS-10 | APPGW subnet App Gateway | security | SYS-02 | Application Gateway | Public ingress with WAF |
| SYS-11 | AKS subnet cluster | platform | SYS-02 | AKS (BU) | BU workload cluster |
| SYS-12 | APP subnet VMs | backend | SYS-02 | App VMs | BU app servers |
| SYS-13 | DB subnet | database | SYS-02 | DB (BU) | BU database tier |
| SYS-14 | Common-AKS subnet | platform | SYS-03 | Common AKS | Shared workload cluster |
| SYS-15 | Common subnet shared services | backend | SYS-03 | Shared services | Shared backend services |
| SYS-16 | Storage-Endpoint subnet | storage | SYS-03 | Storage | Private endpoints for storage |
| SYS-17 | Subnet-Flash-AP-AKS | platform | SYS-05 | AKS (AP) | AP workload cluster |
| SYS-18 | Subnet-Flash-AP-APP | backend | SYS-05 | App (AP) | AP app tier |
| SYS-19 | Subnet-Flash-AP-DB | database | SYS-05 | DB (AP) | AP database tier |
| SYS-20 | dc-us | external | dc-us | US HQ DC systems | US on-prem corporate systems |
| SYS-21 | dc-jp | external | dc-jp | Japan DC systems | Japan on-prem local systems |
| SYS-22 | Azure-US-ER primary circuit | network | SYS-01<->dc-us | Carrier A ExpressRoute | Primary US dedicated circuit |
| SYS-23 | Azure-US-ER secondary circuit | network | SYS-01<->dc-us | Carrier B ExpressRoute | Secondary US dedicated circuit |
| SYS-24 | MPLS | network | hybrid | MPLS | Backup WAN path for US |
| SYS-25 | Internet VPN | network | hybrid | Internet VPN | Backup VPN path for US |
| SYS-26 | Azure-JP-ER primary circuit | network | SYS-04<->dc-jp | Carrier C ExpressRoute | Primary Japan dedicated circuit |
