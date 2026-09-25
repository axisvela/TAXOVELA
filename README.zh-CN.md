# ArchHarness

[English](./README.md) | **中文**

面向 **Claude Code**、**OpenCode**、**Codex**、**GitHub Copilot** 和 **Cursor** 的
企业架构设计与验证技能包。

> 本中文版为方便阅读而维护，可能与英文版存在滞后；如有出入，以
> [英文版 README.md](./README.md) 为准。

ArchHarness 把你的 AI 编程助手变成一支架构专家团队——需求分析师、资深架构师、
偏执的安全审计员、评审委员会委员、技术文档写手——每个角色都可以用一条命令
随时召唤。

<img src="docs/images/hero-d2.png" alt="ArchHarness 渲染输出 —— Azure Hub-Spoke 与本地数据中心（D2 渲染）" width="880">

> **D2 渲染。** 同一份架构模型编译到两种渲染器：**draw.io** 是可编辑源文件，
> **D2** 产出清晰的演示图片。本页图片均为 D2 渲染。

> **不是又一个只有 README 的仓库。** `archharness` 带有真正的 CLI
> （`python -m archharness`）、多项目工作区布局，以及从单一配置文件加载企业取值
> 的平台技能——并且能证明结果：每个工件都经过哈希校验，门禁是确定性的。

## 示例画廊

六个完整示例，每个平台标准一个——全部端到端可运行：需求、`req/v2` 清单、
架构蓝图、渲染图和标准符合性检查。卡片展示 **D2** 渲染图；点击进入示例，
其中也带有可编辑的 draw.io 源文件。

<table>
  <tr>
    <td width="50%"><a href="examples/01-ecommerce-azure/"><img src="docs/images/examples/01-ecommerce-azure-d2.png" alt="Azure Hub-Spoke 架构（D2 渲染）" width="410"></a><br><b>Azure</b> — Hub-Spoke VNET + ExpressRoute · <i>D2 渲染</i></td>
    <td width="50%"><a href="examples/03-order-query-aws-hybrid/"><img src="docs/images/examples/03-order-query-aws-hybrid-d2.png" alt="AWS 混合架构（D2 渲染）" width="410"></a><br><b>AWS</b> — Hub-Spoke VPC + Direct Connect · <i>D2 渲染</i></td>
  </tr>
  <tr>
    <td width="50%"><a href="examples/06-factory-mes-industrial/"><img src="docs/images/examples/06-factory-mes-industrial-d2.png" alt="工厂 MES 架构（D2 渲染）" width="410"></a><br><b>私有云</b> — 工厂边缘 + 中心 DC · <i>D2 渲染</i></td>
    <td width="50%"><a href="examples/09-analytics-gcp-shared-vpc/"><img src="docs/images/examples/09-analytics-gcp-shared-vpc-d2.png" alt="Google Cloud Shared VPC 架构（D2 渲染）" width="410"></a><br><b>Google Cloud</b> — Shared VPC + Interconnect · <i>D2 渲染</i></td>
  </tr>
  <tr>
    <td width="50%"><a href="examples/10-power-platform-governed/"><img src="docs/images/examples/10-power-platform-governed-d2.png" alt="受治理的 Power Platform 架构（D2 渲染）" width="410"></a><br><b>Microsoft SaaS</b> — Power Platform + DLP · <i>D2 渲染</i></td>
    <td width="50%"><a href="examples/11-aliyun-landing-zone/"><img src="docs/images/examples/11-aliyun-landing-zone-d2.png" alt="阿里云 landing-zone 架构（D2 渲染）" width="410"></a><br><b>阿里云</b> — 资源目录 + CEN · <i>D2 渲染</i></td>
  </tr>
</table>

共 11 个示例：`01`–`06` 覆盖私有云、AWS 和 Azure，`09`–`11` 增加
Google Cloud、Microsoft SaaS 和阿里云，`07`–`08` 是等待输入的脚手架。
每个示例都自包含并纳入版本控制；完整矩阵和运行方法见
[`examples/README.md`](./examples/README.md)。

## 两个渲染器，一份模型

每个示例都以两种格式交付同一份模型，每个渲染器各司其职：

| 渲染器 | 产物 | 定位 |
|---|---|---|
| **draw.io** | `diagram-v<N>.drawio` | **仅作可编辑源。** 在 draw.io 桌面应用中打开，手工调整布局或标注。默认不再用它出图；`--png-engine drawio` 可以显式回到 draw.io PNG 渲染。 |
| **D2** | `diagram-v<N>.d2` + PNG/SVG | **默认的图片渲染器。** 一条命令（`d2 --layout elk diagram.d2 out.png`），更清晰、更一致——所以上面的画廊和题图都用 D2。没有 d2 CLI 时回退到 matplotlib。超大图可能耗尽 d2 的栅格后端；传 `--d2-scale 0.2`（或自己用 `d2 --scale` 渲染 `.d2`）即可恢复。 |

同一份模型（示例 09）经两种渲染器的效果：

**draw.io —— 可编辑源**

<img src="docs/images/renderers-drawio.png" alt="示例 09 的 draw.io 渲染" width="560">

**D2 —— 演示渲染**

<img src="docs/images/renderers-d2.png" alt="示例 09 的 D2 渲染" width="880">

## 功能一览

| 智能体 / 技能 | Claude Code | OpenCode | 角色 |
|---|---|---|---|
| arch-workflow | `/arch-workflow` | `@arch-workflow` | 流水线守门员——强制阶段顺序；BLOCK 停止流水线 |
| arch-requirements | `/arch-requirements` | `@arch-requirements` | 结构化访谈 → REQ.md + req.yaml |
| arch-req-from-diagram | `/arch-req-from-diagram` | `@arch-req-from-diagram` | draw.io / PNG → 部分 req.yaml |
| arch-req-from-doc | `/arch-req-from-doc` | `@arch-req-from-doc` | PDF / DOCX / MD → 部分 req.yaml |
| arch-req-from-api | `/arch-req-from-api` | `@arch-req-from-api` | CMDB / ServiceNow / CSV → 部分 req.yaml |
| arch-req-merge | `/arch-req-merge` | `@arch-req-merge` | 合并部分结果、冲突检测、缺口报告 |
| arch-design | `/arch-design` | `@arch-design` | 需求 → 架构 YAML + draw.io 指导 |
| arch-diagram | `/arch-diagram` | `@arch-diagram` | 架构 YAML → draw.io XML + PNG |
| arch-validate | `/arch-validate` | `@arch-validate` | 架构图图片 → 打分 JSON 报告（6 个维度） |
| arch-enforce  | `/arch-enforce`  | `@arch-enforce`  | CI 强制门禁——PASS / WARN / BLOCK 带退出码 |
| arch-security | `/arch-security` | `@arch-security` | 认证 / 凭据 / 网络边界深挖 |
| arch-review | `/arch-review` | `@arch-review` | 委员会门禁：APPROVED / CONDITIONS / REJECTED |
| arch-optimize | `/arch-optimize` | `@arch-optimize` | 按优先级排序的修复清单（P0/P1/P2/P3） |
| arch-report | `/arch-report` | `@arch-report` | Confluence 页面 / 高管摘要 / 风险简报 |

## 工作流

```
Requirements → arch-design → draw in draw.io → arch-validate
                                                       │
                                               arch-enforce gate
                                            PASS / WARN / BLOCK
                                                       │  if PASS/WARN
                                                       │
                                           arch-security  arch-review
                                                       │
                                                arch-optimize
                                                       │
                                                arch-report
```

**流水线是强制的，由工件门禁控制。** 阶段顺序和每阶段要求的输入/输出文件
定义在 [`standards/workflow.yaml`](./standards/workflow.yaml)。
`arch-workflow` 守门员会在阶段开始前检查下一阶段要求的每个工件是否存在
（以及强制门禁是否记录了 PASS 或 WARN）。BLOCK 决定会停止流水线，直到修复
发现项并重新运行验证。永远不要跳过阶段或伪造前置产物；拿不准时调用
`@arch-workflow status` / `@arch-workflow can <stage>`。

记录的工件经过哈希校验，不只是登记名字：与磁盘文件不再匹配的清单会让门禁
失败关闭（fail closed），因此无法在已记录的决策之下偷改架构图。
`python -m archharness workflow verify` 会直接报告这些发现，并在任何工件
过期或被改动时以退出码 1 结束。

## 路线图

产品能力、工程质量和参考内容的仓库级优先级维护在
[docs/ROADMAP.md](./docs/ROADMAP.md)。详细的 draw.io 布局与连线路由计划维护在
[DIAGRAM_GENERATION_ANALYSIS.md](./tools/arch-diagram-gen/DIAGRAM_GENERATION_ANALYSIS.md)。
已发布和未发布的变更，以及下游可以钉住的接口，列在
[CHANGELOG.md](./CHANGELOG.md)。从全新检出到出一张过门禁的架构图的逐步演练
（含每种常见失败的诊断）见 [docs/first-run.md](./docs/first-run.md)；
在每次 PR 上跑门禁并归档证据的配方见
[docs/ci-pipeline.md](./docs/ci-pipeline.md)；引擎与 AXISRobo-PAMP 平台的边界
——包括保护隐私的 `metrics/v1` 可观测性契约——见
[docs/pamp-integration.md](./docs/pamp-integration.md)。针对示例当前（D2）图片
重新验证的方法与实测绑定状态见
[docs/revalidation-guide.md](./docs/revalidation-guide.md)。

## 安装配置

### 1. 克隆

```bash
git clone https://github.com/axisrobo/ea-harness.git
cd ea-harness
```

### 2. 配置组织档案

编辑仓库根目录的 **`config.yaml`**，填入你组织的基础设施信息（DC 名称、
平台名称、密级前缀）。技能和 LLM 规则在运行时加载这些值。

```yaml
company:
  name: "Acme Corp"

datacenters:
  - id: "dc-primary"
    aliases: ["Primary DC", "Tokyo DC"]
    location: { city: "Tokyo", country: "JP" }
    zones: ["DMZ", "App Zone", "DB Zone"]

platforms:
  api_gateway: "Kong API Gateway"   # 或 WSO2、AWS API GW、Azure APIM…
  message_bus: "RabbitMQ"           # 或 Kafka、Azure Service Bus…
  k8s_platform: "Rancher"
  integration_platforms:
    - "Kong API Gateway"
    - "RabbitMQ"
    - "SFTP/MFT"
```

> 如果你管理多个架构项目，把这些公司取值写进 `config.yaml` 一次，然后创建
> **相互隔离的项目**（下一步）。每个项目的输入和输出都在 `projects/<id>/` 下。

### 3. 创建工作区和项目

一个工作区可以容纳多个架构项目。每个项目有自己的 `input/`、`working/` 和
`output/` 目录树，文件绝不会在项目之间串扰。

```bash
# POSIX / macOS / Linux
python -m archharness init-workspace .
python -m archharness init-project payments --name "Payments Platform" --default
python -m archharness list-projects
```

```powershell
# Windows PowerShell
python -m archharness init-workspace .
python -m archharness init-project payments --name "Payments Platform" --default
python -m archharness list-projects
```

这会创建：

```text
projects/payments/
├─ project.yaml               # id、名称、平台、数据密级
├─ input/                     # 文档、架构图、API 导出、需求
├─ working/                   # 中间文件
└─ output/                    # 需求、设计、架构图、验证、报告
```

`project.yaml` 和所有生成的文件都被 git 忽略——只有 `project.yaml` 和
`README.md` 在你选择提交时才被跟踪。

在项目目录内工作时，工具和技能会自动识别活动项目
（在工作区任意位置也可以用 `--project` 指定）。

### 4. 安装 Python 依赖

```bash
# POSIX / macOS / Linux
./install.sh

# Windows PowerShell
.\install.ps1
```

或手动：

```bash
pip install -e ".[all]"
python -m archharness init-workspace .   # 仅当上面没有创建过
python -m archharness doctor             # 验证安装
```

安装程序会向你的 AI 工具注册技能、在缺少工作区时创建它，并运行 `doctor`。
如果你会从其他工作目录运行工具，请把 `ARCHHARNESS_HOME=/path/to/ea-harness`
加入环境变量。

### 5. 在你的 AI 编程工具中打开

**Claude Code**
```bash
claude .
```
`.claude/skills/` 下的技能注册为 `/arch-*` 斜杠命令。

**OpenCode**
```bash
opencode .
```
`.opencode/agents/` 下的智能体注册为 `@arch-*`。

**Codex / GitHub Copilot / Cursor**
把工具指向本仓库根目录。三者都会读取 `AGENTS.md`；Codex 从
`.agents/skills/` 发现技能；GitHub Copilot 从 `.github/agents/` 发现
`@arch-*` 自定义智能体；受支持的 Cursor 版本也会读取 `.claude/skills/`。

> **提示：** 工作目录应为仓库根目录（或某个项目目录），这样技能、工具和
> `config.yaml` 才能被自动找到。

### 各工具如何发现 ArchHarness

| 工具 | 项目规则文件 | 技能 / 智能体位置 | 调用方式 |
|------|---------------|-----------------|------------|
| Claude Code | `CLAUDE.md` | `.claude/skills/` | `/arch-validate`、`/arch-design`…… |
| OpenCode | `AGENTS.md` | `.opencode/agents/` | `@arch-validate`、`@arch-design`…… |
| Codex | `AGENTS.md` | `.agents/skills/` | 基于 `.agents/skills/` 的技能选择器 |
| GitHub Copilot | `AGENTS.md` | `.github/agents/` | `@arch-validate`、`@arch-design`…… |
| Cursor | `AGENTS.md` | `.claude/skills/`（受支持的版本） | `/skills` |

`.agents/skills/` 是 `.claude/skills/` 的生成镜像。编辑任何技能后用
`python scripts/sync_agents_skills.py` 更新它；CI 强制镜像保持同步
（`scripts/check_repo.py` 校验整个技能包）。

### 能在聊天窗口里直接安装吗？

**Claude Code —— 可以，通过插件市场。** 在 Claude Code 聊天窗口中：

```
/plugin marketplace add axisrobo/ea-harness
/plugin install archharness@archharness-marketplace
/reload-plugins
```

插件技能以 `/archharness:arch-validate`、`/archharness:arch-design`、
`/archharness:arch-workflow` 等命名空间形式提供（插件会缓存一份技能副本）。
共享资源（`standards/`、`tools/`、`config.yaml`）由技能通过已安装的包或
本地检出解析——所以请先运行一次 `pip install archharness[all]`
（或设置 `ARCHHARNESS_HOME`）。

**其他工具**：以本仓库为工作目录打开即可（`claude .`、`opencode .`、
`codex`，或让 Copilot/Cursor 指向它）。技能、智能体和 `AGENTS.md` 会被自动
发现，并能访问 `tools/`、`standards/` 和 `config.yaml`。

**安装程序**（`install.ps1` / `install.sh`）会为全新检出做好准备：安装
Python 包、初始化工作区并运行 `doctor`。

### 命令行参考

| 命令 | 用途 |
|---|---|
| `python -m archharness --version` | 显示已安装版本 |
| `python -m archharness root` | 打印资源根目录（config.yaml + tools/） |
| `python -m archharness doctor` | 自检安装、工作区和项目 |
| `python -m archharness init-workspace .` | 创建工作区元数据 |
| `python -m archharness init-project <id>` | 脚手架一个隔离项目 |
| `python -m archharness list-projects` | 列出工作区中的项目 |
| `python -m archharness diagram -i arch.yaml` | 运行架构图生成器（draw.io/PNG/D2/PlantUML） |
| `python -m archharness diagram -i arch.yaml --routing-diagnostics routes.json` | 同时记录每条连线的路由策略、车道与回退 |
| `python -m archharness diagram -i arch.yaml --d2 out.d2 --png out.png` | 渲染 PNG——默认 D2，matplotlib 兜底（`--d2-scale` 缩小超大图） |
| `python -m archharness diagram -i arch.yaml --png out.png --png-engine drawio` | 显式选择 draw.io PNG 渲染（draw.io 默认仅编辑） |
| `python -m archharness arch-check -i blueprint.yaml [--json]` | 对架构模型跑确定性规则（A-01…A-06） |
| `python -m archharness trace-check -r req.yaml -b blueprint.yaml` | 验证 req/v2 清单可追溯到带类型的蓝图节点 |
| `python -m archharness req --doc brief.md` | 运行需求读取器 + 合并器 |
| `python -m archharness req-validate req.yaml` | req/v2 文档的跨字段校验（规则 V1–V7） |
| `python -m archharness validate-yaml config.yaml` | YAML 语法门禁（CI 失败关闭检查） |
| `python -m archharness workflow status` | 显示各阶段就绪状态 |
| `python -m archharness workflow can <stage>` | 仅当该阶段可以开始时返回退出码 0 |
| `python -m archharness workflow verify [--json]` | 重新校验已记录工件的摘要 |
| `python -m archharness manifest --file out/diagram-v2.png --id diagram.png --type diagram --schema diagram/png` | 为文件构建 `artifact/v1` 溯源清单 |
| `python -m archharness enforce --validation validate_result.json` | 应用门禁策略（PASS/WARN/BLOCK） |
| `python -m archharness validate-check -v validate_result.json -r req.yaml -b blueprint.yaml` | 证明每条发现引用的元素真实存在 |
| `python -m archharness backlog -v validate_result.json -r req.yaml -b blueprint.yaml` | 按元素分组的排序修复清单（`backlog/v1`） |
| `python -m archharness metrics --project <id> [--json]` | 聚合治理指标，不含架构负载 |
| `python -m archharness schema-check --baseline <ref>` | 把契约变更分类为 breaking / additive / cosmetic |
| `python -m archharness migrate-status` | 各示例的 req/v2 迁移状态 |
| `python -m archharness view "<question>"` | 为一个问题推荐架构视点 |
| `python -m archharness sketch "Browser -> API -> DB" -o d.drawio` | 不用 YAML 文件的一次性草图 |
| `python -m archharness model diff old.yaml new.yaml` | 语义化模型 diff |
| `python -m archharness plugins` | 列出已发现的插件及能力 |

`arch-check`、`diagram`、`req` 和 `validate-yaml` 会把参数转发给 `tools/` 下
对应的 Python 工具，两种调用方式等价：

```bash
python tools/arch-diagram-gen/arch_diagram_gen.py -i arch.yaml
python -m archharness diagram -i arch.yaml
```

在 `projects/<id>/` 内运行工具会自动作用于该项目；在任意位置传
`--project <id>` 可指定目标项目。

**自包含安装（无需检出仓库）。** `pip install archharness[all]` 会把
`tools/`、`standards/` 和技能树打包进发行包，`python -m archharness root`
会返回内置资源根，CLI 工具可在任意工作目录使用：

```bash
pip install "archharness[all]"              # 从 PyPI 安装，或钉住某个发布版本：
pip install https://github.com/axisrobo/ea-harness/releases/download/v1.1.0/archharness-1.1.0-py3-none-any.whl
python -m archharness root        # → …/site-packages/archharness/data
python -m archharness doctor
```

构建 wheel 前用 `python scripts/assemble_data.py` 重新生成内置数据。

## 使用示例

### 设计一个新系统

```
/arch-requirements
```
Claude 会进行结构化访谈，并在活动项目的 `output/requirements/` 下产出
`REQ.md` + `req.yaml`。

### 生成架构图

```
/arch-design
```
产出架构 YAML 蓝图。然后在项目目录内：

```bash
python ../../tools/arch-diagram-gen/arch_diagram_gen.py -i arch.yaml
# → output/diagrams/arch.drawio
```

或在工作区任意位置显式指定项目：

```bash
python tools/arch-diagram-gen/arch_diagram_gen.py -i projects/payments/input/arch.yaml \
  --project payments
```

### 评审前检查模型

客观规则仅凭架构 YAML 就能判定，在耗费评审周期之前先跑一遍：

```bash
python -m archharness arch-check -i output/designs/blueprint.yaml
# ERROR A-03: interaction api -> db has no protocol label
# ERROR A-04: interaction api -> db has no authentication label
#   ...
# 2 error(s), 0 warning(s)

python -m archharness arch-check -i output/designs/blueprint.yaml --json
```

退出码 1 表示至少有一个 `ERROR`。每条发现都带规则编号（`A-01`…`A-06`）
及其证据来源。

### 验证架构图

附上你的架构图 PNG 并运行：

```
/arch-validate
```
返回带 `must_fix`、`should_fix` 和 `consider` 发现的打分 JSON 报告。

### 完整流水线（OpenCode）

```
@arch-requirements   # 收集需求
@arch-design         # 设计架构
@arch-validate       # 验证架构图
@arch-enforce        # CI 强制门禁决策
@arch-security       # 深度安全审计
@arch-review         # 委员会门禁决策
@arch-optimize       # 按优先级排序的修复清单
@arch-report         # 可直接发 Confluence 的文档
```

## 评分维度

| 维度 | 权重 |
|---|---|
| 云 / 网络完整性 | 2.0 |
| 连通性 | 1.0 |
| 技术组件完整性 | 2.0 |
| 交互 / 集成 | 2.0 |
| 安全合规 | 2.0 |
| 术语表达 | 1.0 |
| **总分** | **10.0** |

## 验证规则

规则位于 `.claude/skills/arch-validate/rules/`：

| 文件 | 系列 | 覆盖范围 |
|---|---|---|
| `diagram-rules.yaml` | V- | 形状、颜色、箭头方向、图例 |
| `interaction-rules.yaml` | W- | 协议、认证、集成平台位置 |
| `security-rules.yaml` | S- | 系统认证、用户认证、凭据保护 |
| `accuracy-rules.yaml` | E- | DC 位置、网段、组件完整性 |
| `platform-rules.yaml` | — | 平台特定规则：私有云、AWS、Azure、GCP、阿里云、Microsoft SaaS（`E-*` 家族） |
| `compliance/terminology.yaml` | — | 云术语、ISO 27001 / TOGAF 映射 |

## 强制门禁

验证之后，**arch-enforce** 门禁对验证结果应用策略阈值，输出可供 CI 使用的
决策：

| 决策 | 条件 | 退出码 |
|----------|-----------|-----------|
| **PASS** | 得分 ≥ 8.0 且无 `must_fix` 问题 | 0 |
| **WARN** | 得分 ≥ 6.0 且 < 8.0 且无 `must_fix` 问题 | 0 |
| **BLOCK** | 得分 < 6.0 或存在任何 `must_fix` 问题 | 1 |

门禁为自动化 CI 流水线设计。人工评审场景请跳过门禁，直接使用
`arch-review`。

策略分两个文件：

- `standards/arch-gate-policy.yaml` —— 强制边界、豁免条件、元控制
- `standards/ci-gate-spec.yaml` —— 各维度最低分、阻断规则 ID、画像
  （金融 / 面向互联网 / 内部）

完整的控制目标与审计追踪规范见 `ARCHITECTURE.md`。

## 基准测试套件

`benchmark/` 目录包含 AI 与伦理修订测量套件：

- Exp1：严格的 C 层门禁到 A 层构建的开销。
- Exp2：`temperature=0.1` 与 `temperature=0.3` 下的一致性。

当前已完成的候选结果记录在 `benchmark/EXPERIMENT_STATUS.md`；本地生成结果
文件存在时汇总在 `benchmark/results/summary.md`。生成的 CSV/汇总文件被 git
忽略；准备论文修订包时请单独保存最终产物。

## 支持的平台

`standards/` 中的标准覆盖六个部署目标。每个都有放置模型、区域模型、身份
与密钥处理、数据密级、配套放置规则、设计模板和完整示例：

| 平台 | 标准 | 模型 | 示例 |
|---|---|---|---|
| **私有云** | `private-cloud-standard.yaml` | F5 入口、经集成平台的东西向隔离、PAW/ADFS | [`05`](./examples/05-supply-chain-order-private-cloud/) |
| **AWS** | `aws-standard.yaml` | Hub-Spoke VPC、ALB+WAF、Spoke VPC 内的 API Gateway、IAM + Secrets Manager | [`03`](./examples/03-order-query-aws-hybrid/) |
| **Azure** | `azure-standard.yaml` | Hub-Spoke VNET、App Gateway WAF v2、Spoke VNET 内的 APIM、Key Vault | [`01`](./examples/01-ecommerce-azure/) |
| **Google Cloud** | `gcp-standard.yaml` | Shared VPC 宿主 + 服务项目、全局 HTTPS LB + Cloud Armor、Cloud NAT、CMEK | [`09`](./examples/09-analytics-gcp-shared-vpc/) |
| **阿里云** | `aliyun-standard.yaml` | 资源目录 + 中心 VPC、Anti-DDoS → WAF → SLB、CEN、RAM 角色 + STS | [`11`](./examples/11-aliyun-landing-zone/) |
| **Microsoft SaaS** | `microsoft-saas-standard.yaml` | 黑盒租户/环境容器、单一边界组件、Entra ID + DLP（M365 / Power Platform / Dynamics 365） | [`10`](./examples/10-power-platform-governed/) |

所有平台特定名称（API 网关、消息总线、K8s 平台）都从 `config.yaml` 读取
——规则和技能文件中没有任何硬编码。

## 项目结构

```
ea-harness/
├── config.yaml              ← 组织档案 —— 先改这个文件
├── README.md
├── README.zh-CN.md          ← 中文版 README（本文件）
├── CLAUDE.md                ← Claude Code 项目规则
├── AGENTS.md                ← OpenCode / Codex / Copilot / Cursor 项目规则
├── ARCHITECTURE.md          ← 设计原理
├── archharness/             ← `python -m archharness` CLI（工作区 + 工具）
├── install.ps1 / install.sh ← 跨平台安装程序
├── benchmark/               ← 实验脚本、提示词、状态与生成结果
├── examples/                ← 11 个完整示例（注册表、req/v2、蓝图、架构图）
├── docs/                    ← 首次运行指南、CI 配方、平台配方、集成
├── schemas/                 ← 版本化契约（req/v2、artifact/v1、validation/v1、
│                              enforcement/v1、metrics/v1）
├── projects/<id>/           ← 工作区项目（用 `archharness init-project` 初始化）
├── standards/               ← 平台无关规则、拓扑规范与门禁策略
├── tools/
│   ├── config_loader.py     ← Python 工具的共享配置读取器
│   ├── arch-diagram-gen/    ← YAML → draw.io + PNG
│   └── arch-req-readers/    ← 架构图 / 文档 / API → req.yaml
├── tests/                   ← pytest 测试套件
├── scripts/                 ← check_repo.py、sync_agents_skills.py（也在 CI 中运行）
├── .github/workflows/       ← CI 流水线
├── .github/agents/          ← GitHub Copilot 自定义智能体（@arch-*）
├── .claude-plugin/          ← Claude Code 插件市场清单
├── plugins/archharness/     ← Claude Code 插件包（技能镜像，生成物）
├── .agents/skills/          ← Codex 发现镜像（生成物）
├── .claude/skills/          ← 技能定义（Claude Code 斜杠命令）
└── .opencode/agents/        ← 智能体定义（OpenCode @agent-name）
```

## 环境要求

- Claude Code、OpenCode、Codex、GitHub Copilot 或 Cursor
- Python 3.10+（`pip install -e ".[all]"` 装齐所有依赖；最小集是 `pyyaml matplotlib`）
- D2 CLI（[d2lang.com](https://d2lang.com)）——渲染 PNG 图片；matplotlib 是
  回退方案；draw.io 桌面版仅在编辑 `.drawio` 源文件时需要

## 许可证

MIT —— 见 `LICENSE`。
