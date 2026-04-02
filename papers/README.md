# papers/ — ArchHarness as Evidence for Unpublished Research

这个目录将 ArchHarness 作为工业验证材料，为以下论文提供对比
支撑。这些文件不是 ArchHarness 的使用说明——它们是以 ArchHarness
为对象的实证分析，可直接作为论文的 case study 材料引用。

## 论文 → 证据文件映射

| 论文 | 状态 | 证据文件 | 核心证据类型 |
|------|------|----------|-------------|
| PACT: A Reference Viewpoint Taxonomy | 待发表 | `pact-coverage-mapping.yaml` | 覆盖率审计（52个视角 × 8层）|
| ARCM: Responsibility Configuration | 待发表 | `arcm-evidence.yaml` | 责任字段追踪 + 缺口分析 |
| DIKCA: Knowledge vs Control | 待发表 | `dikca-layer-analysis.yaml` + `standards/ci-gate-spec.yaml` | K层饱和/C层缺失的系统级证明 |
| PPES: Probabilistic Execution Semantics | 待发表 | `ppes-sampling-protocol.yaml` | ensemble验证协议 + 初步观测 |
| Coalgebraic Framework | 待发表 | `coalgebra-workflow-model.yaml` | 状态机形式化 + 最小实现路径 |

## 已发表论文（AVDM 和 AADM）

AVDM 和 AADM 已正式发表。ArchHarness 通过以下文件体现这两篇
论文的思想：
- `config.yaml > paths` — AADM 的制品深度可配置
- `standards/eval-weights.yaml > profiles` — AVDM 的风险权重调整
- `CLAUDE.md > Configuration` 节 — 说明如何按项目类型裁剪工作量

## 证据的使用方式

每个证据文件包含：
1. **论文主张的具体映射** — 理论概念 ↔ ArchHarness 实现
2. **正面证据** — 项目已实现的部分，证明理论是可操作的
3. **反面证据** — 项目缺失的部分，证明理论解决了真实问题
4. **量化数据** — 可直接引用的数字（行数、覆盖率、字段计数）
