# LLM Question Router Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在实例 QA 入口增加受 schema 约束的 LLM question router，并将属性查询切到 anchor-only 执行路径，同时复用现有图扩展主链路。

**Architecture:** 新增 `instance_qa/question_router.py` 输出结构化路由结果；`orchestrator.py` 优先消费 router 输出并构造 `QuestionDSL`；`fact_query_planner.py` 根据 `reasoning_scope` 选择仅锚点查询或现有图扩展；schema trace 复用同一锚点，保持前后链路一致。LLM 输出始终经过 schema 校验，不可执行时回退旧规则逻辑。

**Tech Stack:** Python 3.11, FastAPI SSE, OpenAI-compatible chat completions, pytest

---

### Task 1: 为路由结果定义受控数据模型与校验

**Files:**
- Create: `instance_qa/question_router.py`
- Modify: `tests/instance_qa/test_question_extractor.py`

**Step 1: Write the failing test**

```python
def test_parse_router_payload_supports_anchor_locator_and_reasoning_scope():
    payload = {
        'intent': 'attribute_lookup',
        'anchor_entity': 'PoD',
        'anchor_locator': {
            'match_type': 'key_attribute',
            'attribute': 'pod_id',
            'value': 'POD-001',
        },
        'target_attributes': ['pod_status'],
        'reasoning_scope': 'anchor_only',
        'confidence': 0.97,
    }

    result = parse_question_route_payload(payload)

    assert result.intent == 'attribute_lookup'
    assert result.anchor_entity == 'PoD'
    assert result.anchor_locator.attribute == 'pod_id'
    assert result.target_attributes == ['pod_status']
    assert result.reasoning_scope == 'anchor_only'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_extractor.py::test_parse_router_payload_supports_anchor_locator_and_reasoning_scope -q`
Expected: FAIL because router parser does not exist yet.

**Step 3: Write minimal implementation**
- 在 `instance_qa/question_router.py` 定义 route dataclass
- 实现 payload parser
- 添加基础字段校验

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_extractor.py::test_parse_router_payload_supports_anchor_locator_and_reasoning_scope -q`
Expected: PASS

### Task 2: 生成 router prompt，并锁定 attribute / impact 两类 few-shot 约束

**Files:**
- Modify: `instance_qa/question_router.py`
- Modify: `tests/instance_qa/test_question_extractor.py`

**Step 1: Write the failing test**

```python
def test_build_question_router_prompt_mentions_anchor_only_and_expand_graph():
    prompt = build_question_router_prompt(registry, 'POD-001的状态是什么？')

    assert 'attribute_lookup' in prompt
    assert 'impact_analysis' in prompt
    assert 'anchor_only' in prompt
    assert 'expand_graph' in prompt
    assert 'POD-001的状态是什么？' in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_extractor.py::test_build_question_router_prompt_mentions_anchor_only_and_expand_graph -q`
Expected: FAIL because prompt builder does not exist yet.

**Step 3: Write minimal implementation**
- 构造受控 prompt
- 加入 `attribute_lookup` 与 `impact_analysis` 示例
- 暴露允许实体与属性

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_extractor.py::test_build_question_router_prompt_mentions_anchor_only_and_expand_graph -q`
Expected: PASS

### Task 3: 在 orchestrator 中接入 router，并保留 fallback

**Files:**
- Modify: `instance_qa/orchestrator.py`
- Modify: `tests/integration/test_instance_qa_stream.py`
- Modify: `tests/server/test_ontology_http_app.py`

**Step 1: Write the failing test**

```python
def test_instance_qa_prefers_router_anchor_for_attribute_lookup(tmp_path: Path, monkeypatch):
    ...
    monkeypatch.setattr(router_module, 'resolve_question_route', lambda *args, **kwargs: route)
    response = client.get('/api/qa/stream', params={'q': 'POD-001的状态是什么？'})
    question_payload = _event_payloads(response.text, 'question_dsl')[0]
    assert question_payload['question_dsl']['anchor']['entity'] == 'PoD'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_prefers_router_anchor_for_attribute_lookup -q`
Expected: FAIL because orchestrator still uses old rule chain only.

**Step 3: Write minimal implementation**
- orchestrator 先尝试 router
- router 不可执行或校验失败时回退当前逻辑
- router 成功时构造 `QuestionDSL`

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_prefers_router_anchor_for_attribute_lookup -q`
Expected: PASS

### Task 4: 让 fact query planner 支持 anchor_only

**Files:**
- Modify: `instance_qa/fact_query_planner.py`
- Modify: `tests/instance_qa/test_fact_query_planner.py`

**Step 1: Write the failing test**

```python
def test_build_fact_queries_returns_only_anchor_query_for_anchor_only_scope():
    ...
    question = build_question_with_scope('anchor_only')
    queries = build_fact_queries(question, registry)
    assert [item.purpose for item in queries] == ['resolve_anchor']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_fact_query_planner.py::test_build_fact_queries_returns_only_anchor_query_for_anchor_only_scope -q`
Expected: FAIL because planner always adds neighbor expansion today.

**Step 3: Write minimal implementation**
- 为 `QuestionDSL` 承载 `reasoning_scope`
- planner 检查 `anchor_only`
- `anchor_only` 时只返回 `resolve_anchor`

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_fact_query_planner.py::test_build_fact_queries_returns_only_anchor_query_for_anchor_only_scope -q`
Expected: PASS

### Task 5: 统一 schema trace 与实例问答锚点

**Files:**
- Modify: `search/ontology_query_engine.py`
- Modify: `server/ontology_http_service.py`
- Modify: `tests/integration/test_instance_qa_stream.py`

**Step 1: Write the failing test**

```python
def test_instance_qa_schema_trace_uses_router_anchor_entity(tmp_path: Path, monkeypatch):
    ...
    response = client.get('/api/qa/stream', params={'q': 'POD-001的状态是什么？'})
    anchor_payload = _event_payloads(response.text, 'trace_anchor')[0]
    assert 'object_type:PoD' in anchor_payload['node_ids']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_schema_trace_uses_router_anchor_entity -q`
Expected: FAIL because schema trace still uses its own seed inference.

**Step 3: Write minimal implementation**
- schema retrieval 优先使用 router anchor entity 作为 seed 候选
- SSE trace 复用统一锚点

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_schema_trace_uses_router_anchor_entity -q`
Expected: PASS

### Task 6: 跑回归与最小手工验证

**Files:**
- Modify only if needed: `SESSION_LOG.md`

**Step 1: Run focused tests**

Run:
- `pytest tests/instance_qa/test_question_extractor.py -q`
- `pytest tests/instance_qa/test_fact_query_planner.py -q`
- `pytest tests/integration/test_instance_qa_stream.py -q`
- `pytest tests/server/test_ontology_http_app.py -q`

Expected: PASS

**Step 2: Run full suite**

Run: `pytest -q`
Expected: PASS

**Step 3: Manual smoke**

Run service and verify:
- `POD-001的状态是什么？` 走 `anchor_only`
- `L1-A机房断电一周，会有哪些影响？` 走 `expand_graph`

**Step 4: Commit**

```bash
git add docs/plans/2026-04-10-llm-question-router-design.md docs/plans/2026-04-10-llm-question-router.md instance_qa/question_router.py instance_qa/orchestrator.py instance_qa/fact_query_planner.py search/ontology_query_engine.py server/ontology_http_service.py tests/instance_qa/test_question_extractor.py tests/instance_qa/test_fact_query_planner.py tests/integration/test_instance_qa_stream.py tests/server/test_ontology_http_app.py
 git commit -m "feat: add llm question router for instance qa"
```
