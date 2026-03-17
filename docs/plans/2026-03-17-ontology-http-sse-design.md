# Ontology HTTP SSE Local Single-Machine Design

**Date:** 2026-03-17

## Goal
把当前基于 Markdown 构建的本体系统，从“双击打开的静态 `ontology.html`”升级为“本地单机 HTTP 页面 + SSE 流式检索动效页面”，并且严格基于当前本体系统内容回答，不接大模型，先把检索高亮、证据链、模板回答跑通。

## Accepted Constraints
- Markdown 文件仍然是唯一事实源。
- 仍然只构建本体定义图，不引入实例图谱。
- 图谱继续使用当前 `Cytoscape.js`。
- 维持当前用户已接受的图布局基线：`cose`、无顶部层级标题、节点不可拖拽。
- 第一版改成 HTTP 页面，但先不接大模型。
- 回答必须严格受限于当前本体结构、属性、关系；遇到实例级、实时状态级问题必须明确返回“证据不足”。

## Architecture

### 1. Runtime shape
启动本地服务时，后端读取指定 Markdown 文件，构建内存中的 `OntologyGraph`，同时生成前端需要的 Cytoscape payload。服务对外提供：
- `GET /ontology`：返回完整页面。
- `GET /api/graph`：返回当前图谱 payload。
- `GET /api/qa/stream?q=...`：SSE 流式返回检索步骤、证据链和最终模板回答。

### 2. Stack
- 后端：`FastAPI`
- 流式通信：`SSE`
- 前端图谱：`Cytoscape.js`
- 前端页面：沿用当前 `graph_export.py` 生成的 HTML 模板，增加 HTTP/SSE 模式
- 检索：确定性本体检索器，不接 LLM

### 3. In-memory data
服务启动后只保留一份当前图谱：
- `OntologyGraph`
- `graph_payload`
- 反向索引（节点名、中文释义、分组、关键属性、状态建议、规则、说明、关系标签）

第一版不做热更新；Markdown 改动后，重启服务重新加载。

## Retrieval Model

### 1. Supported question scope
第一版支持：
- 查询某个实体有哪些属性/语义定义
- 查询两个实体间有哪些关系
- 查询某个层/某类节点的上下游关系
- 查询某个属性名属于哪个实体

第一版不支持：
- 实例级问题
- 实时状态问题
- “某机柜里哪些服务器宕机”这类运行数据问题

对于不支持的问题，后端仍然执行锚定和检索，但最终模板回答必须明确说明：当前系统只有本体定义，没有实例运行数据，因此证据不足。

### 2. Deterministic retrieval flow
后端检索流程固定拆成：
1. 归一化问题文本
2. 节点锚定
3. 邻居扩展
4. 条件过滤
5. 聚焦最终子图
6. 生成证据链
7. 生成模板回答

### 3. Node anchoring rules
按优先级匹配：
1. 实体英文名精确/包含匹配
2. 中文释义、分组名匹配
3. 关键属性 / 状态建议 / 规则 / 说明匹配
4. 关系标签匹配后回溯关联节点

### 4. Evidence chain shape
每条证据至少包含：
- `evidence_id`
- `kind` (`seed` / `relation` / `node` / `filter_result`)
- `label`
- `message`
- `node_ids`
- `edge_ids`
- `why_matched`

最终答案必须引用这些证据项。

## SSE Event Protocol
前端通过 `EventSource` 监听 `/api/qa/stream`。

### Event types
- `anchor_node`
- `expand_neighbors`
- `filter_nodes`
- `focus_subgraph`
- `evidence`
- `answer_done`
- `error`

### Common payload fields
每条事件统一包含：
- `session_id`
- `step`
- `message`
- `node_ids`
- `edge_ids`
- `evidence_ids`

### Final event
`answer_done` 额外包含：
- `answer`
- `evidence_chain`
- `matched_node_ids`
- `matched_edge_ids`
- `insufficient_evidence`

## Front-End Behavior

### 1. Page model
`/ontology` 页面继续保留：
- 图谱主视图
- 节点点击浮层详情
- 右下角智能问答入口

但问答面板改为真正联动后端：
- 提问后创建 SSE 连接
- 实时消费后端步骤事件
- 驱动图上高亮/聚焦动画
- 渲染证据链和最终回答

### 2. Animation rules
- `anchor_node`：高亮起始节点
- `expand_neighbors`：高亮边和扩展节点
- `filter_nodes`：非命中节点变暗
- `focus_subgraph`：仅保留最终证据子图高亮
- 播放一次后停留在最终证据子图

### 3. Evidence interaction
聊天面板中的每条证据都必须可点击；点击后左侧图谱重新闪烁对应节点/边。

## Template Answering
第一版不用大模型。
最终回答由模板生成器根据：
- 命中实体
- 命中关系
- 命中属性/说明
- 证据链
- 是否证据不足

拼装为可读中文结果。

示例回答风格：
- “根据当前本体定义，`PoD` 与 `ArrivalPlan` 之间存在 `APPLIES_TO` 关系。证据：[E1][E2]。”
- “当前系统仅包含本体定义，不包含实例运行状态，因此无法回答‘哪些服务器宕机’。证据：[E1][E2]。”

## API and CLI

### HTTP routes
- `GET /ontology`
- `GET /api/graph`
- `GET /api/qa/stream?q=...`

### CLI entry
新增本地服务命令，例如：
- `python -m cloud_delivery_ontology_palantir.cli serve-ontology --input-file "...md" --host 127.0.0.1 --port 8000`

启动后用户访问：
- `http://127.0.0.1:8000/ontology`

## Error Handling
- Markdown 文件不存在：服务启动失败并输出明确错误。
- 问题为空：前端不发起 SSE。
- 未找到锚定节点：仍然返回 `answer_done`，说明当前本体中未匹配到相关实体。
- SSE 中途异常：发送 `error` 事件并关闭连接。

## Non-goals
当前版本不做：
- 大模型接入
- 实例图谱
- 实时数据库查询
- Markdown 热重载
- 多用户会话隔离优化
- WebSocket 双工协议

## Rollout Order
1. 先搭出 FastAPI 页面和 `/api/graph`
2. 再补确定性检索器
3. 再补 SSE 流式事件
4. 最后接前端动画和证据链 UI
