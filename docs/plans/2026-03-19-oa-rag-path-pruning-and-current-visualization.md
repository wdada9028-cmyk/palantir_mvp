# OA-RAG 路径剪枝与动态电流可视化重构 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 仅在因果类问答中触发意图对齐、加权路径剪枝和动态电流可视化，同时保持定义查询的自然展示模式与现有问答链路兼容。

**Architecture:** 新增独立的 `qa/intent_resolver.py` 负责 `impact_analysis` / `definition_query` 判定，并在 LLM 失败时用关键词兜底。检索层在因果类问题上执行加权最短路径并集近似 Steiner skeleton 剪枝，将 `critical_path` 写入 `OntologyEvidenceBundle` 和 `answer_done`；前端只在 `critical_path` 非空时启用背景降噪、seed 呼吸动画与 Canvas 电流层。

**Tech Stack:** Python 3.11, FastAPI, SSE, Cytoscape.js, Canvas 2D, OpenAI-compatible API, pytest

---

### Task 1: 为问答意图对齐增加失败优先测试与独立解析器

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/intent_resolver.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/qa/test_intent_resolver.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/__init__.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/intent_resolver.py`

**Step 1: Write the failing tests**
Add tests covering:
- valid LLM response returning `impact_analysis`
- valid LLM response returning `definition_query`
- invalid/empty `intent_type` falling back to keyword mode
- timeout/error falling back to keyword mode
- no LLM + no keyword hit falling back to `definition_query`

Suggested test shape:
```python
def test_resolve_qa_intent_uses_keyword_fallback_when_llm_returns_invalid_type(monkeypatch):
    class FakeClient:
        def post(self, *args, **kwargs):
            return FakeResponse({'intent_type': 'unknown'})

    monkeypatch.setattr('cloud_delivery_ontology_palantir.qa.intent_resolver.get_http_client', lambda: FakeClient())
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    result = resolve_qa_intent('延期会导致什么影响？')

    assert result.intent_type == 'impact_analysis'
    assert result.source == 'keyword'
    assert '延期' in result.matched_keywords
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/qa/test_intent_resolver.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Create `qa/intent_resolver.py` with:
- `QAIntentResolution` dataclass
- env-based config loading
- OpenAI-compatible HTTP client reuse pattern matching the existing resolver style
- strict enum validation for `impact_analysis|definition_query`
- keyword fallback using `['影响', '后果', '延期', '风险', '冲突', '依赖', '关联', '导致']`
- final downgrade to `definition_query` only when both LLM and keyword checks fail

**Step 4: Export the API**
Update `qa/__init__.py` to expose the new resolver symbols.

**Step 5: Run test to verify it passes**
Run:
```bash
pytest tests/qa/test_intent_resolver.py -v
```
Expected: PASS.

**Step 6: Commit**
```bash
git add qa/intent_resolver.py qa/__init__.py tests/qa/test_intent_resolver.py
git commit -m "feat: add qa intent fallback resolver"
```

### Task 2: 为因果剪枝准备数据模型和搜索测试

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_models.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/search/test_ontology_query_engine.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_engine.py`

**Step 1: Write the failing tests**
Extend search tests to assert:
- `impact_analysis` results expose `critical_path_edge_ids`
- `definition_query` keeps `critical_path_edge_ids` empty
- noisy structural leaf nodes (for example `Project`) are absent from the pruned cause skeleton when they are not required
- fallback path preservation keeps at least one route when pruning would otherwise empty the graph

Suggested test shape:
```python
def test_retrieve_ontology_evidence_prunes_non_causal_topology_for_impact_questions(monkeypatch):
    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_qa_intent',
        lambda question: QAIntentResolution(intent_type='impact_analysis', source='keyword', matched_keywords=['影响'])
    )
    bundle = retrieve_ontology_evidence(graph, '延期会影响落位吗？')
    assert bundle.intent_type == 'impact_analysis'
    assert bundle.critical_path_edge_ids
    assert 'object_type:Project' not in bundle.matched_node_ids
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: FAIL.

**Step 3: Extend the models minimally**
Add to `OntologyEvidenceBundle`:
- `intent_type`
- `critical_path_edge_ids`
- `critical_path_node_ids`
- `seeds`

Add a lightweight relation-weight structure, either as:
- a `RelationWeight` dataclass plus registry, or
- a typed constant map if that keeps the model surface smaller.

**Step 4: Run the tests again to confirm model-related failures remain red in engine logic**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: still FAIL, but now on missing engine behavior rather than missing fields.

**Step 5: Commit**
```bash
git add search/ontology_query_models.py tests/search/test_ontology_query_engine.py
git commit -m "test: define causal pruning search expectations"
```

### Task 3: 实现意图驱动的加权骨架剪枝

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_engine.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/intent_resolver.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_models.py`

**Step 1: Wire intent resolution into retrieval**
Resolve `intent_type` near the start of `retrieve_ontology_evidence()` without disturbing existing seed resolution.

**Step 2: Build weighted candidate graph helpers**
Add minimal helpers for:
- relation weight lookup
- candidate adjacency construction from matched edges
- weighted shortest-path search between seed pairs
- skeleton node/edge union

**Step 3: Implement pruning branch**
For `impact_analysis`:
- compute pairwise shortest paths between seeds
- union those paths into the causal skeleton
- drop non-seed leaf nodes outside the skeleton
- drop weak-topology chains below threshold when they are not the only route

**Step 4: Implement fallback preservation**
If pruning empties or disconnects the graph:
- preserve at least one weighted shortest path
- if still empty, keep the original expanded result

**Step 5: Populate bundle fields**
Write `intent_type`, `critical_path_edge_ids`, `critical_path_node_ids`, and `seeds` into the returned bundle.

**Step 6: Run tests to verify they pass**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: PASS.

**Step 7: Commit**
```bash
git add search/ontology_query_engine.py search/ontology_query_models.py tests/search/test_ontology_query_engine.py qa/intent_resolver.py tests/qa/test_intent_resolver.py qa/__init__.py
git commit -m "feat: prune causal ontology paths"
```

### Task 4: 升级 SSE 协议并为意图模式写服务端测试

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_app.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_service.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/server/test_ontology_http_app.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/generator.py`

**Step 1: Write the failing tests**
Extend server tests to assert:
- `answer_done` includes `full_answer`, `trace_report`, `critical_path`, `seeds`
- impact questions produce non-empty `critical_path`
- definition questions produce empty `critical_path`
- legacy `answer` / `answer_text` fields remain present

Suggested test shape:
```python
def test_qa_stream_returns_critical_path_only_for_impact_queries(tmp_path, monkeypatch):
    ...
    response = client.get('/api/qa/stream', params={'q': '延期会影响落位吗？'})
    text = response.text
    assert '"critical_path": ["e1"]' in text
    assert '"seeds":' in text
    assert '"full_answer":' in text
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update:
- `server/ontology_http_app.py` to keep passing the now-enriched bundle through the existing path
- `server/ontology_http_service.py` to emit the new fields from bundle/result data
- `answer_done` to set `critical_path` from `bundle.critical_path_edge_ids`
- `full_answer` to mirror the final LLM-or-fallback text while preserving `answer` and `answer_text`

**Step 4: Run tests to verify it passes**
Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add server/ontology_http_app.py server/ontology_http_service.py tests/server/test_ontology_http_app.py
git commit -m "feat: expose critical path in qa stream"
```

### Task 5: 为前端条件渲染与 Canvas 电流层写回归测试

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/integration/test_definition_graph_export.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/export/graph_export.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_service.py`

**Step 1: Write the failing tests**
Add assertions that exported HTML contains:
- a Canvas overlay shell for current animation
- conditional guards based on `critical_path`
- seed pulse styling / animation hook
- fallback branch when Canvas creation fails
- default-mode branch that skips current animation when `critical_path` is empty

Suggested test shape:
```python
def test_exported_html_contains_conditional_current_animation_hooks(tmp_path):
    graph = OntologyGraph(metadata={'title': 'ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'critical_path' in text
    assert 'createCurrentOverlayCanvas' in text
    assert 'animateCriticalCurrent' in text
    assert 'if (!criticalPath.length)' in text
    assert 'seed-pulse' in text
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update `export/graph_export.py` to:
- add Canvas overlay markup or JS-created overlay helper
- add conditional render path using `critical_path`
- dim the background only in causal mode
- animate seeds and critical edges in causal mode
- preserve current plain highlight mode when `critical_path` is empty
- catch Canvas errors and fall back to base highlighting only

**Step 4: Run tests to verify it passes**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: add conditional critical current visualization"
```

### Task 6: 全量验证与本地烟雾检查

**Files:**
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/intent_resolver.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_models.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_engine.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/server/ontology_http_service.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/export/graph_export.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/qa/test_intent_resolver.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/search/test_ontology_query_engine.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/server/test_ontology_http_app.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/integration/test_definition_graph_export.py`

**Step 1: Run focused suites**
Run:
```bash
pytest tests/qa/test_intent_resolver.py -v
pytest tests/search/test_ontology_query_engine.py -v
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

**Step 3: Smoke check fallback intent mode**
Without Qwen config, run the local server and verify:
- impact question still returns `critical_path` because keyword fallback fires
- definition question returns empty `critical_path`
- no Canvas support still leaves normal highlighter usable

**Step 4: Smoke check LLM intent mode**
With valid Qwen config, run the local server and verify:
- impact question returns pruned `trace_report`
- non-causal query keeps natural graph display with no current animation
- first visible path motion appears quickly after `trace_anchor`

**Step 5: Commit**
```bash
git add qa/intent_resolver.py qa/__init__.py search/ontology_query_models.py search/ontology_query_engine.py server/ontology_http_app.py server/ontology_http_service.py export/graph_export.py tests/qa/test_intent_resolver.py tests/search/test_ontology_query_engine.py tests/server/test_ontology_http_app.py tests/integration/test_definition_graph_export.py docs/plans/2026-03-19-oa-rag-path-pruning-and-current-visualization-design.md docs/plans/2026-03-19-oa-rag-path-pruning-and-current-visualization.md
git commit -m "feat: add causal pruning and current visualization"
```
