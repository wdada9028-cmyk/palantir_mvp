# LLM Question Router Design

**Date:** 2026-04-10

## Goal
在实例 QA 前面增加统一的 LLM 语义路由层，把“问题理解”和“查询执行”拆开：前者由大模型输出受约束的结构化结果，后者继续复用现有的 TypeDB 实例查询、图扩展、推理与 SSE 返回链路。

## Scope
本次设计覆盖：
- 在实例 QA 入口新增统一 `question_router`
- 用 LLM 输出结构化路由结果，而不是直接回答
- 支持两类主路径：`anchor_only`（实例属性直查）与 `expand_graph`（现有图扩展）
- 让 schema trace 和 instance QA 使用同一份锚点理解结果，避免前后不一致
- 保留现有规则链路作为兜底

## Non-goals
- 不改为 LLM 生成 TypeQL
- 不重写 TypeDB client / result mapper / reasoning / trace summary 主逻辑
- 不在第一阶段引入独立向量库
- 不在第一阶段处理所有 ID 大小写归一化问题

## Problem Statement
当前项目存在两条独立的问题理解链路：
- schema 检索链路：`search/ontology_query_engine.py`
- instance QA 链路：`instance_qa/orchestrator.py` + `search/query_parser/*`

它们使用的实体识别逻辑不同，导致同一问题会出现：
- 图谱定位认为命中了 `PoD`
- 实例问答却回退到默认锚点 `Project`

典型案例：
- `POD-001的状态是什么？`

因此需要把“用户问题理解”统一到单一入口，再把统一结果喂给后续执行链路。

## Architectural Decision
新增 `instance_qa/question_router.py`，只负责输出受 schema 约束的结构化路由结果。路由结果示例：

```json
{
  "intent": "attribute_lookup",
  "anchor_entity": "PoD",
  "anchor_locator": {
    "match_type": "key_attribute",
    "attribute": "pod_id",
    "value": "POD-001"
  },
  "target_attributes": ["pod_status"],
  "reasoning_scope": "anchor_only",
  "confidence": 0.97,
  "why": "Question asks for a specific instance attribute value."
}
```

以及：

```json
{
  "intent": "impact_analysis",
  "anchor_entity": "Room",
  "anchor_locator": {
    "match_type": "key_attribute",
    "attribute": "room_id",
    "value": "L1-A"
  },
  "target_attributes": [],
  "reasoning_scope": "expand_graph",
  "confidence": 0.96,
  "why": "Question asks for downstream impact analysis."
}
```

## Core Principle
- LLM 负责理解问题
- 程序负责校验输出是否合法
- 查询执行仍由后端决定
- 低置信度或非法输出时回退当前规则链路

## Router Output Contract
建议输出字段：
- `intent`: `attribute_lookup | impact_analysis | relation_query | instance_lookup`
- `anchor_entity`: schema 中真实存在的实体名
- `anchor_locator`:
  - `match_type`: `key_attribute | attribute | name | alias | unknown`
  - `attribute`: 用于定位实例的字段名，可为空
  - `value`: 问题中用于定位实例的值
- `target_attributes`: 仅属性查询时有值
- `reasoning_scope`: `anchor_only | expand_graph`
- `confidence`: 0~1
- `why`: 调试解释

## Prompt Strategy
Prompt 输入：
- 当前允许的实体列表
- 每个实体的 key attributes
- 每个实体可查询属性
- 受控的 intent / reasoning_scope 列表
- 2~4 个 few-shot 示例
- 原始问题

Prompt 约束：
- 只能从给定 schema 中选实体和属性
- 问“状态 / 属性 / 字段值 / 时间 / 负责人 / 数量”时优先输出 `attribute_lookup`
- `attribute_lookup` 必须使用 `reasoning_scope = anchor_only`
- 问“影响 / 传播 / 依赖 / 范围 / 上下游”时输出 `expand_graph`
- 严格输出 JSON

## Validation Rules
程序侧必须校验：
- `anchor_entity` 是否存在于 schema registry
- `target_attributes` 是否属于该实体
- `anchor_locator.value` 是否非空
- `reasoning_scope` 是否合法
- `attribute_lookup` 是否具备可执行的 locator + target attributes

校验失败：
- 回退到当前 `parse_query(...)` + `_build_question_dsl(...)` 规则链路

## Integration With Existing Chain
### 1. Orchestrator
`instance_qa/orchestrator.py` 先调用 `question_router`，优先根据 router 输出构造 `QuestionDSL`；只有在 router 不可执行时，才走当前规则生成 DSL 的逻辑。

### 2. Fact Query Planner
`instance_qa/fact_query_planner.py` 只增加轻量分支：
- `anchor_only`：只生成锚点查询，不扩展邻居
- `expand_graph`：继续走现有 adjacency / propagation 逻辑

### 3. Schema Retrieval / Trace
`search/ontology_query_engine.py` 和 `server/ontology_http_service.py` 优先使用 router 产出的锚点实体，保证图谱定位与实例问答命中同一实体。

### 4. Answer Layer
- `attribute_lookup`：只根据锚点实例属性回答
- `expand_graph`：继续复用现有 reasoning + trace summary + answer generation

## Why No Vector Index In Phase 1
当前主要问题是实体识别链路分裂，而不是 schema 规模过大。直接引入向量库会显著增加系统复杂度，但不能直接解决“图定位和实例问答不一致”的核心问题。第一阶段先完成统一路由与执行分流；若后续发现属性同义表达召回不足，再补充轻量 embedding 检索层。

## Example Outcomes
### Question: `POD-001的状态是什么？`
- Router: `attribute_lookup`
- Anchor: `PoD.pod_id = POD-001`
- Execution: only resolve anchor row
- Answer: `POD-001 当前状态是 Installing。`

### Question: `L1-A机房断电一周，会有哪些影响？`
- Router: `impact_analysis`
- Anchor: `Room.room_id = L1-A`
- Execution: resolve anchor + graph expansion + propagation
- Answer: 继续输出实例级影响分析

## Risks
- LLM 可能输出 schema 不存在的属性或实体
- 属性查询与关系查询可能存在模糊边界
- Router 和旧规则链路并行阶段可能出现少量行为不一致

## Mitigations
- 强制 schema 校验
- 保留 fallback
- 用回归测试锁定 `attribute_lookup` 与 `impact_analysis` 两条主路径
- 在 SSE 输出里保留 router 结果，便于调试
