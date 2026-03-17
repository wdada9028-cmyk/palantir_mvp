# Ontology Search Trace Playback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add deterministic retrieval trace capture, dual SSE protocols, graph playback animation, and a search-trace summary answer without breaking the current ontology QA flow.

**Architecture:** Extend the retrieval bundle with cumulative path snapshots, emit both legacy and new SSE events from the server, and let the generated Cytoscape front end prefer a trace-aware playback controller while preserving the old path as a fallback. Drive the change with focused red-green tests per layer so protocol compatibility remains explicit.

**Tech Stack:** Python 3.11, dataclasses, FastAPI SSE, Cytoscape.js, pytest

---

### Task 1: Add failing search-trace model and retrieval tests

**Files:**
- Modify: `D:\????\AI?????\??????\palantir_mvp	ests\search	est_ontology_query_engine.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp\search\ontology_query_models.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp\search\ontology_query_engine.py`

**Step 1: Write the failing test**
Add assertions that `retrieve_ontology_evidence(...)` returns:
- `result.search_trace.seed_node_ids == ["object_type:PoD"]`
- at least one expansion step with deterministic values
- cumulative `snapshot_node_ids` / `snapshot_edge_ids`

Suggested test shape:
```python
def test_retrieve_ontology_evidence_records_deterministic_search_trace():
    result = retrieve_ontology_evidence(graph, "PoD ?????")

    assert result.search_trace.seed_node_ids == ["object_type:PoD"]
    assert [step.edge_id for step in result.search_trace.expansion_steps] == ["e1"]
    step = result.search_trace.expansion_steps[0]
    assert step.from_node_id == "object_type:ArrivalPlan"
    assert step.to_node_id == "object_type:PoD"
    assert step.snapshot_node_ids == ["object_type:PoD", "object_type:ArrivalPlan"]
    assert step.snapshot_edge_ids == ["e1"]
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py::test_retrieve_ontology_evidence_records_deterministic_search_trace -v
```
Expected: FAIL because `OntologyEvidenceBundle` has no `search_trace`.

**Step 3: Write minimal implementation**
Modify `D:\????\AI?????\??????\palantir_mvp\search\ontology_query_models.py` to add:
- `TraceExpansionStep`
- `SearchTrace`
- `OntologyEvidenceBundle.search_trace`

Modify `D:\????\AI?????\??????\palantir_mvp\search\ontology_query_engine.py` to build deterministic search trace snapshots while traversing relations.

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add tests/search/test_ontology_query_engine.py search/ontology_query_models.py search/ontology_query_engine.py
git commit -m "feat: capture ontology retrieval trace"
```

### Task 2: Add failing SSE dual-protocol tests

**Files:**
- Modify: `D:\????\AI?????\??????\palantir_mvp	ests\server	est_ontology_http_app.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp\server\ontology_http_service.py`

**Step 1: Write the failing test**
Add a test asserting the response text contains:
- `event: trace_anchor`
- `event: trace_expand`
- `event: evidence_final`
- new-order constraint: `trace_anchor < trace_expand < evidence_final < answer_done`
- `"delay_ms":` in trace payloads

Keep the existing legacy-order test unchanged.

Suggested test shape:
```python
def test_qa_stream_emits_new_trace_events_in_order(tmp_path: Path):
    response = client.get('/api/qa/stream', params={'q': 'PoD ?????'})
    text = response.text

    assert 'event: trace_anchor' in text
    assert 'event: trace_expand' in text
    assert 'event: evidence_final' in text
    assert text.index('event: trace_anchor') < text.index('event: trace_expand')
    assert text.index('event: trace_expand') < text.index('event: evidence_final')
    assert text.index('event: evidence_final') < text.index('event: answer_done')
    assert '"delay_ms":' in text
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_new_trace_events_in_order -v
```
Expected: FAIL because the new events are not emitted yet.

**Step 3: Write minimal implementation**
Modify `D:\????\AI?????\??????\palantir_mvp\server\ontology_http_service.py`:
- extend `iter_qa_events(...)` with optional `trace_delay_ms`
- emit `trace_anchor` from `bundle.search_trace.seed_node_ids`
- emit `trace_expand` for each expansion step
- emit `evidence_final` with the final evidence chain
- keep all old events and `answer_done`

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add tests/server/test_ontology_http_app.py server/ontology_http_service.py
git commit -m "feat: emit ontology trace sse events"
```

### Task 3: Add failing exported HTML playback tests

**Files:**
- Modify: `D:\????\AI?????\??????\palantir_mvp	ests\integration	est_definition_graph_export.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp\export\graph_export.py`

**Step 1: Write the failing test**
Add assertions that exported HTML contains:
- `searching-node`
- `trace-path`
- `trace-dimmed`
- `PlaybackController`
- `replayFromSnapshot`
- `evidence-timeline`
- `trace_anchor`
- `trace_expand`
- `evidence_final`

Suggested test shape:
```python
def test_exported_html_contains_trace_playback_controller_and_timeline(tmp_path: Path):
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'searching-node' in text
    assert 'trace-path' in text
    assert 'trace-dimmed' in text
    assert 'PlaybackController' in text
    assert 'replayFromSnapshot' in text
    assert 'evidence-timeline' in text
    assert 'trace_anchor' in text
    assert 'trace_expand' in text
    assert 'evidence_final' in text
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_trace_playback_controller_and_timeline -v
```
Expected: FAIL because the generated HTML lacks the new controller/timeline/classes.

**Step 3: Write minimal implementation**
Modify `D:\????\AI?????\??????\palantir_mvp\export\graph_export.py`:
- add CSS classes `.searching-node`, `.trace-path`, `.trace-dimmed`
- introduce `PlaybackController`
- add queue/snapshot/timer state
- add `replayFromSnapshot(...)`
- add `evidence-timeline` markup
- prefer new trace events for playback; keep legacy fallback
- ensure all template Chinese strings remain unicode-safe

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add tests/integration/test_definition_graph_export.py export/graph_export.py
git commit -m "feat: add ontology trace playback ui"
```

### Task 4: Add failing template-answer tests

**Files:**
- Modify: `D:\????\AI?????\??????\palantir_mvp	ests\qa	est_template_answering.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp\qa	emplate_answering.py`

**Step 1: Write the failing test**
Add a test asserting the answer includes:
- `??????`
- a relation-based expansion sentence
- evidence summary / insufficient-evidence behavior still present

Suggested test shape:
```python
def test_build_template_answer_includes_search_trace_report_and_summary():
    answer = build_template_answer(bundle)

    assert '??????' in answer.answer
    assert '??APPLIES_TO???????PoD?' in answer.answer or '??APPLIES_TO???????ArrivalPlan?' in answer.answer
    assert '???' in answer.answer
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/qa/test_template_answering.py::test_build_template_answer_includes_search_trace_report_and_summary -v
```
Expected: FAIL because the current answer has no trace report.

**Step 3: Write minimal implementation**
Modify `D:\????\AI?????\??????\palantir_mvp\qa	emplate_answering.py`:
- add helper(s) to summarize `bundle.search_trace`
- prepend a `??????` section
- retain the current conclusion/evidence summary behavior
- preserve insufficient-evidence runtime disclaimer

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/qa/test_template_answering.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add tests/qa/test_template_answering.py qa/template_answering.py
git commit -m "feat: summarize ontology search trace"
```

### Task 5: Verify the complete feature set

**Files:**
- Reference: `D:\????\AI?????\??????\palantir_mvp	ests\search	est_ontology_query_engine.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp	ests\server	est_ontology_http_app.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp	ests\integration	est_definition_graph_export.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp	ests\qa	est_template_answering.py`

**Step 1: Run focused verification**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
pytest tests/server/test_ontology_http_app.py -v
pytest tests/integration/test_definition_graph_export.py -v
pytest tests/qa/test_template_answering.py -v
```
Expected: PASS.

**Step 2: Run full regression**
Run:
```bash
pytest tests -q
```
Expected: PASS.

**Step 3: Smoke test the local server**
Run:
```bash
python -m cloud_delivery_ontology_palantir.cli serve-ontology --input-file "D:\????\AI?????\??????\palantir_mvp\[????] ????2?????v2.md" --host 127.0.0.1 --port 8000
```
Then manually verify in a browser:
- submitting a QA query auto-focuses the graph
- trace steps animate sequentially
- unrelated regions are dimmed
- evidence timeline buttons replay the saved path snapshot

**Step 4: Commit**
```bash
git add search/ontology_query_models.py search/ontology_query_engine.py server/ontology_http_service.py export/graph_export.py qa/template_answering.py tests/search/test_ontology_query_engine.py tests/server/test_ontology_http_app.py tests/integration/test_definition_graph_export.py tests/qa/test_template_answering.py docs/plans/2026-03-17-ontology-search-trace-playback-design.md docs/plans/2026-03-17-ontology-search-trace-playback.md
git commit -m "feat: add ontology search trace playback"
```
