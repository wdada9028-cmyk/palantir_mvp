# OA-RAG 路径剪枝与动态电流可视化重构设计

**Date:** 2026-03-19

## Goal
针对因果类问答（影响、依赖、冲突等）减少检索噪音，输出更短、更可信的因果骨架，并在前端以受控的动态电流动画突出关键逻辑路径；对定义查询等非因果类问题保持现有自然展示模式。

## Existing Context
当前系统已经具备三层基础能力：
1. `search/ontology_query_engine.py` 可以基于种子节点与相邻关系生成 `OntologyEvidenceBundle`、`SearchTrace` 和前端高亮步骤。
2. `server/ontology_http_service.py` 已能通过 SSE 发送 `trace_anchor`、`trace_expand`、`answer_delta`、`answer_done` 等事件。
3. `export/graph_export.py` 已支持证据回放、答案流式显示和基于 SSE 的图谱高亮。

当前问题在于：
- 扩散结果仍会携带大量结构性节点，因果问题中噪音偏高；
- 前端对因果问题与普通定义问题没有明确的视觉分层差异；
- “是否需要电流寻路动画”缺少明确的后端协议开关。

## Chosen Approach
采用“意图识别驱动检索与渲染分支”的方案：
- 新增 `qa/intent_resolver.py`，专门输出 UI/检索所需的 `intent_type`
- 对因果类问题执行加权骨架提取（近似 Steiner Tree 的最小连通子图）
- 对非因果类问题保留当前普通中心扩散结果
- 在 `answer_done` 中新增 `critical_path` 和 `seeds`，前端仅在 `critical_path` 非空时启用全图降噪与 Canvas 电流动画

## Why This Approach
这是风险最低且最可控的演进路径：
- 不破坏现有 SSE 流与模板答案回退链路
- 将“问什么类型的问题”和“如何剪枝/如何渲染”解耦
- 对非因果类问题零惊扰，避免所有问答都被强行做成“激光聚焦”效果
- 关键词兜底保证即便 LLM 失败，影响分析类问题仍能触发关键路径模式

## Intent Alignment Design
创建 `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/intent_resolver.py`。

### Responsibilities
- 调用 Qwen 判断当前问答意图，只允许：
  - `impact_analysis`
  - `definition_query`
- 当 LLM 返回空、非法值、异常或超时时，自动进入关键词兜底
- 关键词列表固定为：
  - `影响`
  - `后果`
  - `延期`
  - `风险`
  - `冲突`
  - `依赖`
  - `关联`
  - `导致`
- 任一命中 => `impact_analysis`
- 既无 LLM 有效结果，也无关键词命中 => `definition_query`

### Suggested API
- `QAIntentResolution`
  - `intent_type`
  - `source` (`llm|keyword|default`)
  - `matched_keywords`
  - `error`
- `resolve_qa_intent(question, *, timeout_s=...) -> QAIntentResolution`

### Failure Handling
- LLM timeout / transport error / invalid JSON / invalid enum：全部视为可恢复错误
- 关键词兜底是强制对齐层，不依赖种子解析器是否成功
- 只有完全无法判断时才落到 `definition_query`

## Retrieval Pruning Design
### Relation Weight Model
在 `search/ontology_query_models.py` 中加入结构化权重定义，至少包含：
- 强逻辑边：
  - `REFERENCES`
  - `CONSTRAINS`
  - `APPLIES_TO`
  - `DEPENDS_ON`
  - 权重 `1.0`
- 弱拓扑边：
  - `CONTAINS`
  - `BELONGS_TO`
  - `DEFINES`
  - 权重 `0.1`
- 其他未列出关系给出保守中间权重，例如 `0.5`

### Skeleton Extraction
在 `search/ontology_query_engine.py` 中保留原始命中与扩散逻辑，但增加后处理分支：
1. 先得到扩散后的候选子图
2. 提取种子节点 `seed_node_ids`
3. 若 `intent_type == impact_analysis`：
   - 基于边权重构建候选图
   - 对任意两个种子节点求加权最短路径
   - 合并所有最短路径，得到近似 Steiner skeleton
   - 删除不在骨架上的叶子节点（非 seed）
   - 删除低权重且非唯一通路的拓扑长链
4. 若 `intent_type == definition_query`：
   - 不做骨架剪枝
   - 维持当前扩散结果

### Output Additions
`OntologyEvidenceBundle` 需要增加：
- `intent_type`
- `critical_path_edge_ids`
- `critical_path_node_ids`
- `seeds`（可直接复用 `seed_node_ids`，但为了协议清晰可显式暴露）

### Fallback Rule
若骨架提取把路径剪断或输出空骨架：
- 回退到“权重保留”模式
- 保证至少保留一条连接任意 seed 的最短通路
- 再不行则回退原始扩散结果，确保可视路径不为空

## SSE Protocol Design
在 `server/ontology_http_service.py` 中升级 `answer_done`。

### Required Fields
- `full_answer`: 顶部显示的最终答案文本
- `trace_report`: 剪枝后的精简逻辑路径文本
- `critical_path`: 关键边 ID 列表
- `seeds`: 原始锚点 ID 列表

### Compatibility Fields
保留现有：
- `answer`
- `answer_text`
- `matched_node_ids`
- `matched_edge_ids`
- `evidence_chain`
- `search_trace`

### Trigger Contract
- `critical_path` 非空：前端进入因果渲染模式
- `critical_path` 为空：前端维持普通模式，不启用电流层

## Front-End Visualization Design
在 `export/graph_export.py` 中引入“条件化高级渲染”。

### Default Mode
适用于 `critical_path` 为空：
- 不做全局降噪
- 不绘制 Canvas 电流层
- 只保留当前节点/边高亮与证据时间线逻辑

### Causal Mode
适用于 `critical_path` 非空：
- 全图节点和边默认透明度降到 `0.2`
- `seeds` 节点使用金黄色 `#f1e05a`
- `seeds` 增加呼吸缩放动画
- `critical_path` 上的节点和边提升到 `1.0`
- 在 Cytoscape 上方增加 Canvas overlay
- 沿 `critical_path` 边绘制蓝色流动虚线，通过 `lineDashOffset` 做电流前进动画

### Interaction Rhythm
- `trace_anchor`: seed 节点先脉冲
- `answer_delta`: 顶部答案继续打字
- `answer_done`: 若 `critical_path` 非空，启动电流寻路并锁定骨架视角

### Front-End Fallback
如果 Canvas 初始化失败或绘制异常：
- 不影响页面其他功能
- 退回到基础高亮（加粗、变色、调透明度）
- 不阻断 SSE 或答案展示

## Data Flow
1. 用户提问
2. `qa/intent_resolver.py` 输出 `intent_type`
3. 现有种子解析器继续解析实体 seed
4. `retrieve_ontology_evidence()` 根据 `intent_type` 选择普通扩散或因果骨架剪枝
5. 模板答案和 LLM 生成继续消费剪枝后的 bundle
6. SSE 发送检索过程、流式答案和最终 `critical_path`
7. 前端仅在 `critical_path` 非空时启用电流层与降噪渲染

## Testing Strategy
### Unit
`tests/qa/test_intent_resolver.py`：
- LLM 返回 `impact_analysis`
- LLM 返回 `definition_query`
- LLM 返回非法值时关键词兜底
- LLM 超时时关键词兜底
- 无 LLM 且无关键词命中时降级 `definition_query`

### Search
`tests/search/test_ontology_query_engine.py`：
- 因果类问题能剪掉无关拓扑叶子
- 定义类问题不做剪枝
- 断路时触发保底通路模式
- `critical_path_edge_ids` 与 `intent_type` 正确写入 bundle

### Server
`tests/server/test_ontology_http_app.py`：
- `answer_done` 带 `full_answer`、`trace_report`、`critical_path`、`seeds`
- 因果类问题 `critical_path` 非空
- 定义类问题 `critical_path` 为空
- 现有 `answer_delta` 流不回退

### Front End
`tests/integration/test_definition_graph_export.py`：
- 页面包含 Canvas overlay 壳、条件开关、seed 呼吸动画样式
- `critical_path` 非空时调用电流绘制逻辑
- `critical_path` 为空时跳过电流层
- Canvas 失败时仍有基础高亮分支

## Risks and Controls
1. **因果问题误判为定义问题**
   - control: LLM + 关键词兜底双层判断
2. **关键词误伤普通查询**
   - control: 只用固定小词表，且只控制因果模式开关，不直接改写答案内容
3. **剪枝过头导致图断裂**
   - control: 保底通路模式 + 原始扩散兜底
4. **Canvas 动画拖慢页面**
   - control: 仅在 `critical_path` 非空时初始化，失败立即降级
5. **协议升级破坏旧逻辑**
   - control: 保留现有 `answer` / `answer_text` / 匹配字段
