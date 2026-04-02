# draw.io 生成方案对比：Hard-coded Python vs LLM-assisted

## 背景

当前 `generator.py` + `layout.py` 是完全 hard-coded 的 Python 实现：
从 YAML → XML 的映射由代码显式控制，布局由算法计算。
这个方案有明确的问题，也有明确的优势。

---

## 当前 Hard-coded 方案的问题清单

| 问题 | 根因 | 严重程度 |
|------|------|---------|
| 组件堆叠（AWS Spoke 5个组件挤一行） | `layout.py` 的行分割算法按像素宽度计算，但边界条件没有全部覆盖 | 中 |
| 跨 DC 连线穿越容器边框 | `generator.py` 生成的 edge 没有路由 waypoint，draw.io 自动路由会穿框 | 中 |
| 容器大小计算误差 | bottom-up 高度计算不考虑 zone label 行高和 padding 的叠加 | 低 |
| 组件形状单调 | 目前六边形/平行四边形/圆柱已实现，但图例形状（如wave/plaque/drop）没有完整映射 | 低 |
| 无法自适应文本长度 | 组件名称很长时，形状宽度不会自动拉伸 | 低 |

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

### 方案 D：修复 Hard-coded 方案的具体 Bug（推荐立即做）

当前布局问题的实际根因是几个具体的计算 bug，不是架构性缺陷：

| 问题 | 具体 Fix |
|------|---------|
| 组件堆叠 | `layout.py` 的 `_split_into_rows()` 需要考虑 zone padding 的实际可用宽度而非 `MAX_ROW_W` 常量 |
| 跨 DC 连线穿框 | `generator.py` 的 edge 生成加入 waypoint：在边的 `mxGeometry` 里显式插入中间点，强制走容器外部 |
| 容器高度误差 | 在 `_region_height()` 里增加 ZONE_LABEL 高度到累计高度 |

这些 fix 总计约 30 行代码，没有任何不确定性，完全可测试。

---

## 决策建议

```
当前优先级排序：

P0（立即）：修复 hard-coded 方案的 3 个具体布局 bug
            → 直接改 layout.py + generator.py，不引入 LLM

P1（下一步）：D2 + PlantUML 生成器已完成
              → D2 用于 git diff 友好的版本控制
              → PlantUML 用于 Confluence 内嵌 + draw.io import 桥接

P2（探索）：LLM 作为"内容辅助"，不作"坐标计算"
            具体场景：
            - 让 LLM 根据 YAML 的 interactions 自动推断 waypoint 路由策略
            - 让 LLM 审查生成的图，发现漏掉的 interaction（如没有画的 Kafka consumer）
            - arch-validate 里让 LLM 看 draw.io XML + YAML，做一致性验证

P3（不做）：LLM 直接生成 mxGraphModel XML
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
