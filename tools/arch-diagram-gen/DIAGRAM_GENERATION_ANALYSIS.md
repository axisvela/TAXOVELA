# draw.io 生成方案对比：Hard-coded Python vs LLM-assisted

## 背景

当前 `generator.py` + `layout.py` 是完全 hard-coded 的 Python 实现：
从 YAML → XML 的映射由代码显式控制，布局由算法计算。
这个方案有明确的问题，也有明确的优势。

---

## 当前 Hard-coded 方案状态（2026-09）

| 项目 | 状态 | 说明 |
|------|------|------|
| 自适应组件尺寸与行分割 | 已完成 | `layout.py` 以最终可用宽度重分行，按标签长度扩展组件并计算容器高度。 |
| 逻辑组嵌套布局 | 已完成 | 逻辑组成员是实际节点，使用组内相对坐标布局。 |
| 生命周期颜色 | 已完成 | draw.io、D2、matplotlib 共用 `labels.component_fill()`，状态不再重复打印在节点文本中。 |
| D2 PNG 输出 | 已完成 | `--png-engine d2` 使用 ELK 自动布局；适合预览和需要避障边线的 PNG。 |
| draw.io 连线避障与通道路由 | 已完成 | 确定性正交 router 写入显式 waypoint、分散端点约束和跨容器 gutter；通道仅从交互两端容器选择，XML 记录路由策略与 fallback。 |
| 组件形状覆盖度 | 待评估（P3） | 核心六边形、平行四边形、圆柱、圆形已实现；补充形状须由标准需求驱动。 |

**根本原因**：这些都是 **布局计算** 问题，不是 **内容生成** 问题。
LLM 擅长的是理解语义和生成内容，不擅长精确坐标计算。

---

## LLM-assisted 方案分析

### 方案 A：LLM 直接生成 draw.io XML

让 LLM（Claude/GPT-4o）读入 YAML，直接输出 `mxGraphModel` XML。

**优势**：
- 可利用 LLM 对 draw.io 格式的"感觉"来做更自然的布局
- 可在 prompt 里直接描述 Company 形状规范，LLM 会遵守
- 对于复杂的跨区连线，LLM 可以手动插入 waypoint 避免穿框

**致命缺陷**：
1. **坐标不可靠**：LLM 无法精确计算 `x/y/width/height`，会产生重叠或溢出。
   draw.io XML 的每个 `mxGeometry` 都需要精确坐标，这是 LLM 的硬伤。
2. **非确定性**：同一个 YAML 每次生成的图布局可能不同，不适合版本控制。
3. **成本高**：完整 YAML（含多 DC）token 数大，每次生成约 2000-4000 token input。
4. **输出不稳定**：XML 里一个 `"` 和 `&amp;` 的混用就会破坏整个文件。

**结论**：❌ 不推荐直接生成 XML。

---

### 方案 B：LLM 生成 D2/PlantUML，再转换到 draw.io

**流程**：YAML → LLM → D2/PlantUML 文本 → draw.io import

**优势**：
- LLM 生成文本格式（D2/PlantUML）比生成 XML 可靠得多
- D2/PlantUML 文本出错时错误范围小，容易修复
- draw.io 原生支持 PlantUML 导入（Extras → Edit Diagram → paste PlantUML）
- D2 可通过 `d2 --output-format drawio` 导出 draw.io 格式

**问题**：
- PlantUML 的 Deployment Diagram 导入 draw.io 后布局仍然很粗糙
- D2 → draw.io 的转换是实验性功能，格式映射不完整
- 多了一个依赖（LLM API 调用）

**结论**：⚠️ 可作为辅助，但不是银弹。

---

### 方案 C：LLM 只做"布局修复"（推荐探索方向）

**流程**：Hard-coded Python 生成基础 XML → LLM 读取 XML，识别问题，输出修正后的坐标

**优势**：
- LLM 的工作是"审查和修正"，不是"从零生成"
- Python 确保结构正确（节点、边、容器关系），LLM 只调整数字
- 错误范围可控

**问题**：
- XML 体积仍然大，读取 + 修正消耗 token 多
- 修正坐标时 LLM 很难"看"到全局布局，可能越改越乱

**结论**：⚠️ 有价值但实现成本高，暂不优先。

---

### 方案 D：确定性 draw.io 路由器（推荐下一步）

当前的剩余主要问题是 **edge routing**，不是节点或容器的布局计算。应保持 Python 生成 XML 的确定性，并在现有 `layout["abs_positions"]` 基础上为每条边计算路由：

| 层次 | 具体实现 | 价值 |
|------|----------|------|
| 端口选择 | 按源、目标的相对方向设置 `exitX/exitY/entryX/entryY`；同侧多条边按序号分配端口偏移。 | 减少边从错误一侧离开节点、降低首段重叠。 |
| 简单正交路由 | 对同一区域或同一行/列的节点，生成 0–2 个 Manhattan waypoint。 | 可读、稳定，适合绝大多数内部调用。 |
| 容器外通道路由 | 为跨 zone / region 边预留容器外侧 gutter；使用 `mxGeometry` 的 `Array as="points"` 写入明确坐标。 | 避免线穿越容器内部或边框，并让跨 DC 流量走统一通道。 |
| 障碍物避让 | 将组件、逻辑组及可选的容器边界转换为矩形障碍物；先用 L 形候选路径，冲突时切换到水平/垂直通道。 | 不引入外部依赖即可解决常见的穿节点问题。 |
| 冲突收敛 | 为共享通道分配 lane offset；同一 source/target 的反向或并行边使用不同 lane，边标签跟随最长段。 | 减少重叠和不可读标签。 |
| 回退策略 | 路由失败时保留当前 `orthogonalEdgeStyle` 自动路由，并在测试/诊断中记录原因。 | 保证现有图不会因新路由器失败而无法输出。 |

draw.io XML 的表达方式是保留 `source` / `target`，并在边的 `mxGeometry` 增加：

```xml
<Array as="points">
  <mxPoint x="..." y="..."/>
  <mxPoint x="..." y="..."/>
</Array>
```

坐标使用根画布坐标；现有 `abs_positions` 已提供节点的根坐标。不要把 D2 的自动布局结果反向转换成 draw.io：这样会丢失公司样式、嵌套容器和可预测的 XML。

---

## 决策建议

```
当前优先级排序：

P0（已完成）：自适应节点/容器布局、逻辑组嵌套、生命周期颜色、D2 和 PlantUML 输出

P1（已完成）：确定性 draw.io edge router
            → Manhattan waypoint + 容器外 gutter + 失败回退 + 双向边 lane 分流
            → 保持 YAML 相同则 XML 路由相同，不引入 LLM 或图数据库依赖

P2（已完成）：为路由添加可重复的测试与诊断
            → 断言 waypoint 不落在组件矩形内
            → 断言跨容器边使用预期 gutter
            → 在 example 06 和多 DC fixture 上生成 PNG 作视觉回归

P3（已完成）：受限 visibility graph 避障
            → 仅在 L 形候选路径均与障碍物冲突时，沿组件安全边界选择最短正交路径
            → 图规模受限于端点和组件边界，仅连接相邻可见节点；超过节点上限时回退外部 gutter，不引入外部依赖或非确定性

P4（不做）：LLM 直接生成 mxGraphModel XML
```

---

## 结论

**Hard-coded draw.io 方案保留，是正确决策。** 原因：

1. 确定性输出：相同 YAML 永远产生相同图
2. 无 API 成本：可在 CI/CD 中免费运行
3. 可测试：每个布局函数可写单元测试
4. 可调整：布局 bug 修复后立即生效，不需要改 prompt

LLM 在这个工具链中的最佳位置是：
- **输入理解**（arch-design skill：从自然语言需求生成 YAML）
- **校验**（arch-validate skill：从图片或 XML 识别架构问题）
- **文档**（arch-report skill：从 YAML + 校验结果生成报告）

而不是：坐标计算、XML 序列化、精确布局。
