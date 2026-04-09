# Instance QA Schema Trace Streaming Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 基于现有链路，把已有的 schema 检索过程通过 SSE 流式暴露给前端，并驱动本体结构图实时动态可视化。

**Architecture:** 不新增第二次 schema 检索，也不改变实例 QA 主链路职责。复用现有 `search/ontology_query_engine.py` 的 `retrieve_ontology_evidence(...)` 结果，把它挂到 `InstanceQAResult` 中，并在 `server/ontology_http_service.py` 的实例 QA 事件流里插入 `trace_anchor / trace_expand / evidence_final`。前端继续复用已有 `PlaybackController` 和图谱高亮逻辑。

**Tech Stack:** Python 3.11, FastAPI SSE, inline browser JavaScript in `export/graph_export.py`, pytest

---

### Task 1: 锁定实例 QA 流会发出现有 schema trace 事件

**Files:**
- Modify: `tests/integration/test_instance_qa_stream.py`
- Modify: `instance_qa/orchestrator.py`
- Modify: `server/ontology_http_service.py`

**Step 1: Write the failing test**

```python
def test_instance_qa_stream_emits_schema_trace_events_before_typedb_queries(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01机房断电会有哪些影响'})

    text = response.text
    assert 'event: trace_anchor' in text
    assert 'event: evidence_final' in text
    assert text.index('event: question_dsl') < text.index('event: trace_anchor')
    assert text.index('event: evidence_final') < text.index('event: fact_query_planned')
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_stream_emits_schema_trace_events_before_typedb_queries -q`
Expected: FAIL because instance QA SSE does not emit schema trace events yet.

**Step 3: Write minimal implementation**

- 在 `InstanceQAResult` 中补充 schema retrieval bundle 字段
- 在实例 QA 主流程中复用 `retrieve_ontology_evidence(graph, question)`
- 在 `iter_qa_events(...)` 中于 `question_dsl` 之后、`fact_query_planned` 之前发出 `trace_anchor / trace_expand / evidence_final`

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_stream_emits_schema_trace_events_before_typedb_queries -q`
Expected: PASS

### Task 2: 锁定 trace 事件负载来自现有 schema retrieval trace

**Files:**
- Modify: `tests/integration/test_instance_qa_stream.py`
- Modify: `server/ontology_http_service.py`

**Step 1: Write the failing test**

```python
def test_instance_qa_stream_trace_expand_payload_uses_search_trace_snapshots(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01机房断电会有哪些影响'})

    expand_payload = _event_payloads(response.text, 'trace_expand')[0]
    assert 'snapshot_node_ids' in expand_payload
    assert 'snapshot_edge_ids' in expand_payload
    assert 'delay_ms' in expand_payload
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_stream_trace_expand_payload_uses_search_trace_snapshots -q`
Expected: FAIL because no expand payload is emitted yet.

**Step 3: Write minimal implementation**

- 从 `bundle.search_trace.expansion_steps` 直接构造 `trace_expand` payload
- 从 `bundle.seed_node_ids` 构造 `trace_anchor`
- 从 `bundle.evidence_chain + bundle.search_trace` 构造 `evidence_final`

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_stream_trace_expand_payload_uses_search_trace_snapshots -q`
Expected: PASS

### Task 3: 锁定前端入口继续消费实时 trace 而无需新协议

**Files:**
- Modify: `tests/integration/test_definition_graph_export.py`
- Modify only if needed: `export/graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_instance_qa_stream_still_consumes_live_trace_events(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'trace_anchor' in text
    assert 'trace_expand' in text
    assert 'evidence_final' in text
    assert 'playbackController.enqueue(eventType, payload)' in text
```

**Step 2: Run test to verify it fails only if front-end protocol drift exists**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_instance_qa_stream_still_consumes_live_trace_events -q`
Expected: PASS or minimal fix required.

**Step 3: Write minimal implementation if needed**

- 仅在前端协议漂移时补最小修正
- 不新增新的前端播放协议

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_instance_qa_stream_still_consumes_live_trace_events -q`
Expected: PASS

### Task 4: Full verification

**Files:**
- Modify only if follow-up fixes are required.

**Step 1: Run focused stream tests**

Run: `pytest tests/integration/test_instance_qa_stream.py -q`
Expected: PASS

**Step 2: Run focused export tests**

Run: `pytest tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 3: Run server/integration regression**

Run: `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 4: Run full suite**

Run: `pytest tests -q`
Expected: PASS
