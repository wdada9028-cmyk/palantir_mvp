# Ontology LLM Answer Generation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Qwen2.5-32B streaming answer generator that summarizes retrieved ontology facts while preserving deterministic fallback and trace provenance.

**Architecture:** Keep the current retrieval pipeline unchanged as the fact source, add `qa/generator.py` as a stream-capable generation layer, extend the SSE service to emit `answer_delta`, and update the HTML client to render streamed answers plus a collapsible `trace_report`. Fallback always goes through the existing template answer path.

**Tech Stack:** Python 3.11, FastAPI, SSE, OpenAI-compatible API, `openai`, pytest

---

### Task 1: Add failing generator tests and install the OpenAI client dependency

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/qa/test_generator.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/generator.py`
- Modify: dependency file if present, otherwise add the minimal dependency declaration used by this repo
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/template_answering.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_models.py`

**Step 1: Write the failing tests**
Add tests covering:
- streaming success with mocked OpenAI chunks
- missing config fallback
- empty-facts fallback
- mid-stream exception fallback
- exact entity-label preservation in `answer_text`

Suggested test shape:
```python
async def test_iter_generated_answer_streams_chunks_and_preserves_entity_labels(monkeypatch):
    bundle = build_bundle_with_edges(...)
    fallback = TemplateAnswer(answer='fallback', insufficient_evidence=False)

    class FakeChunk:
        def __init__(self, text):
            self.choices = [type('Choice', (), {'delta': type('Delta', (), {'content': text})()})]

    async def fake_stream():
        for text in ['结论：', '机房里程碑(RoomMilestone)', ' 会影响落位方案(PlacementPlan)。']:
            yield FakeChunk(text)

    fake_client = AsyncMock()
    fake_client.chat.completions.create.return_value = fake_stream()
    monkeypatch.setattr('cloud_delivery_ontology_palantir.qa.generator.get_openai_client', lambda: fake_client)
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    chunks = [item async for item in iter_generated_answer('哪些里程碑会影响落位？', bundle, fallback)]

    result = chunks[-1]
    assert result.answer_text.startswith('结论：')
    assert '机房里程碑(RoomMilestone)' in result.answer_text
    assert '落位方案(PlacementPlan)' in result.answer_text
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/qa/test_generator.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Create `qa/generator.py` with:
- environment-based config loading for Qwen
- OpenAI-compatible async client factory
- fact formatter from deduped trace edges
- stream iterator that yields deltas and a final result
- fallback behavior for missing config, no facts, and runtime failure

**Step 4: Install dependency**
Install the `openai` package and update the repo dependency declaration actually used by this project.

**Step 5: Run test to verify it passes**
Run:
```bash
pytest tests/qa/test_generator.py -v
```
Expected: PASS.

**Step 6: Commit**
```bash
git add qa/generator.py tests/qa/test_generator.py <dependency-file>
git commit -m "feat: add ontology answer generator"
```

### Task 2: Add failing server tests for `answer_delta` streaming and response shape

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/server/test_ontology_http_app.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_app.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_service.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/generator.py`

**Step 1: Write the failing tests**
Extend server tests to assert:
- existing retrieval event order remains unchanged
- new `answer_delta` events are emitted after retrieval events
- `answer_done` includes `answer`, `answer_text`, `trace_report`, `used_fallback`
- generator failures still produce `answer_done` via fallback

Suggested test shape:
```python
def test_qa_stream_emits_answer_delta_and_extended_answer_done(tmp_path, monkeypatch):
    ...
    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.server.ontology_http_service.iter_generated_answer',
        fake_generator,
    )

    response = client.get('/api/qa/stream', params={'q': '哪些里程碑会影响落位？'})
    text = response.text

    assert 'event: trace_anchor' in text
    assert 'event: answer_delta' in text
    assert '"answer_text":' in text
    assert '"trace_report":' in text
    assert '"used_fallback":' in text
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update:
- `server/ontology_http_app.py` to build both `bundle` and `fallback_answer`
- `server/ontology_http_service.py` to consume generator output and emit `answer_delta`
- `answer_done` payload to preserve old `answer` and add the new fields

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add server/ontology_http_app.py server/ontology_http_service.py tests/server/test_ontology_http_app.py
git commit -m "feat: stream ontology generated answers"
```

### Task 3: Add failing front-end tests for dual-layer answer rendering

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/integration/test_definition_graph_export.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/export/graph_export.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_service.py`

**Step 1: Write the failing tests**
Add assertions that exported HTML contains:
- a prominent answer text area for streaming content
- a collapsible "逻辑溯源" section
- `answer_delta` event handling
- `answer_done` logic that renders `answer_text` and `trace_report`

Suggested test shape:
```python
def test_exported_html_contains_streaming_answer_and_trace_sections(tmp_path):
    graph = OntologyGraph(metadata={'title': 'ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'answer_delta' in text
    assert 'trace_report' in text
    assert '逻辑溯源' in text
    assert 'answer_text_so_far' in text
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update `export/graph_export.py` to:
- add a prominent answer display region
- add a collapsible trace-report area labeled `逻辑溯源`
- append streamed `answer_delta` content into the answer region
- render `trace_report` on `answer_done`
- keep legacy `answer` handling as a fallback for compatibility

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: render streamed ontology answer summaries"
```

### Task 4: Full verification and smoke checks

**Files:**
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/generator.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_app.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_service.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/export/graph_export.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/qa/test_generator.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/server/test_ontology_http_app.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/integration/test_definition_graph_export.py`

**Step 1: Run focused suites**
Run:
```bash
pytest tests/qa/test_generator.py -v
pytest tests/server/test_ontology_http_app.py -v
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: PASS.

**Step 2: Run full regression**
Run:
```bash
pytest tests -q
```
Expected: PASS.

**Step 3: Smoke check with fallback**
Without Qwen config, run the local server and verify:
- retrieval events still stream
- no `answer_delta` events are required before fallback completion if generator short-circuits
- `answer_done` contains `used_fallback=true`
- answer text is still visible

**Step 4: Smoke check with Qwen config**
With valid Qwen config, run the local server and verify:
- retrieval events appear first
- `answer_delta` starts arriving before the final completion event
- entity names remain in `中文名(ID)` format
- `trace_report` remains deterministic and separate from the generated answer

**Step 5: Commit**
```bash
git add qa/generator.py server/ontology_http_app.py server/ontology_http_service.py export/graph_export.py tests/qa/test_generator.py tests/server/test_ontology_http_app.py tests/integration/test_definition_graph_export.py docs/plans/2026-03-19-ontology-llm-answer-generation-design.md docs/plans/2026-03-19-ontology-llm-answer-generation.md
git commit -m "feat: add ontology llm answer generation"
```
