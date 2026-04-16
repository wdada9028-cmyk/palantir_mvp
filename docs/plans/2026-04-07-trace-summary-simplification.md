# Trace Summary Simplification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current logic trace with a compact + expanded customer-facing trace summary and remove technical debug noise from the normal QA UI.

**Architecture:** Add a deterministic backend trace summary builder that consumes the existing evidence-driven QA outputs. The orchestrator will attach the new summary to `InstanceQAResult`, the SSE layer will send it, and the front end will render only the compact/expanded summary instead of raw query logs.

**Tech Stack:** Python 3.11, FastAPI SSE, current evidence-driven instance QA modules, existing graph-export front-end, pytest

---

### Task 1: Add trace summary models and builder

**Files:**
- Create: `instance_qa/trace_summary_builder.py`
- Test: `tests/instance_qa/test_trace_summary_builder.py`

**Step 1: Write the failing test**

```python
def test_build_trace_summary_returns_compact_and_expanded_sections():
    summary = build_trace_summary(question_dsl=make_question(), fact_pack=make_fact_pack(), evidence_bundle=make_bundle(), reasoning_result=make_reasoning())

    assert 'question_understanding' in summary['compact']
    assert 'key_evidence' in summary['compact']
    assert 'detailed_evidence' in summary['expanded']
    assert 'key_paths' in summary['expanded']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_trace_summary_builder.py -q`
Expected: FAIL because the builder module does not exist yet.

**Step 3: Write minimal implementation**

- Build a deterministic `build_trace_summary(...)` helper
- Produce `compact` and `expanded` sections only
- Use concise business-facing fields only

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_trace_summary_builder.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/trace_summary_builder.py tests/instance_qa/test_trace_summary_builder.py
git commit -m "feat: add compact trace summary builder"
```

### Task 2: Add evidence compression rules to the trace builder

**Files:**
- Modify: `instance_qa/trace_summary_builder.py`
- Test: `tests/instance_qa/test_trace_summary_builder.py`

**Step 1: Write the failing test**

```python
def test_trace_summary_limits_instance_lists_and_keeps_counts():
    summary = build_trace_summary(...)

    positions = summary['compact']['key_evidence']['direct_hits']['PoDPosition']
    assert positions['total'] == 5
    assert len(positions['items']) <= 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_trace_summary_builder.py::test_trace_summary_limits_instance_lists_and_keeps_counts -q`
Expected: FAIL because compression rules are not implemented yet.

**Step 3: Write minimal implementation**

- Add short-list compression for many instances
- Keep total counts
- Keep only a few useful attributes per instance

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_trace_summary_builder.py::test_trace_summary_limits_instance_lists_and_keeps_counts -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/trace_summary_builder.py tests/instance_qa/test_trace_summary_builder.py
git commit -m "feat: compress trace evidence for customer display"
```

### Task 3: Attach trace summary to the orchestrator result

**Files:**
- Modify: `instance_qa/orchestrator.py`
- Test: `tests/server/test_ontology_http_app.py`

**Step 1: Write the failing test**

```python
def test_qa_stream_emits_trace_summary_ready(tmp_path):
    response = client.get('/api/qa/stream', params={'q': 'L1-A??????????????'})
    assert 'event: trace_summary_ready' in response.text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_trace_summary_ready -q`
Expected: FAIL because the orchestrator result does not yet include trace summary.

**Step 3: Write minimal implementation**

- Extend `InstanceQAResult` with `trace_summary`
- Build it after `reasoning` is available

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_trace_summary_ready -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/orchestrator.py tests/server/test_ontology_http_app.py
git commit -m "feat: attach trace summary to instance qa result"
```

### Task 4: Emit trace summary through SSE and remove user-facing debug trace payloads

**Files:**
- Modify: `server/ontology_http_service.py`
- Modify: `tests/server/test_ontology_http_app.py`
- Modify: `tests/integration/test_instance_qa_stream.py`

**Step 1: Write the failing test**

```python
def test_answer_done_contains_trace_summary_not_raw_debug_trace(tmp_path):
    payload = answer_done_payload(...)
    assert 'trace_summary' in payload
    assert 'fact_queries' not in payload.get('trace_summary', {})
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py::test_answer_done_contains_trace_summary_not_raw_debug_trace -q`
Expected: FAIL because the SSE payload does not yet include the new trace summary.

**Step 3: Write minimal implementation**

- Emit `trace_summary_ready`
- Include `trace_summary` in `answer_done`
- Stop using raw query logs as the normal trace payload source

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py::test_answer_done_contains_trace_summary_not_raw_debug_trace -q`
Expected: PASS

**Step 5: Commit**

```bash
git add server/ontology_http_service.py tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: stream compact trace summary"
```

### Task 5: Update the front end to render compact + expanded trace summary only

**Files:**
- Modify: `export/graph_export.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_prefers_trace_summary_sections_over_debug_log_text():
    html = build_graph_html(...)
    assert '????' in html
    assert '????' in html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py -q`
Expected: FAIL because the front end still renders raw trace text.

**Step 3: Write minimal implementation**

- Render compact trace sections by default
- Add one expand interaction for detailed sections
- Stop showing raw TypeQL / query-log style text in the logic trace card

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: simplify logic trace UI"
```

### Task 6: Run verification

**Files:**
- Modify only if follow-up fixes are required.

**Step 1: Run instance QA tests**

Run: `pytest tests/instance_qa -q`
Expected: PASS

**Step 2: Run server and integration tests**

Run: `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 3: Run full suite**

Run: `pytest tests -q`
Expected: PASS

**Step 4: Review working tree**

Run: `git status --short --branch`
Expected: only intended trace-summary files are modified.

**Step 5: Commit final fixups if needed**

```bash
git add <intended files>
git commit -m "feat: finalize compact trace summary"
```
