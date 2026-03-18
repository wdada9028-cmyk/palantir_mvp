# Ontology Trace Simplification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make ontology path reports concise, deduped, and easier to scan while preserving retrieval accuracy.

**Architecture:** Keep retrieval and SSE trace production unchanged except for relation-label formatting, and move report dedupe + concise rendering into `qa/template_answering.py`. `SearchTrace` will still carry the full expansion sequence, but template rendering will collapse duplicate `(from, relation, to)` hops and emit a compact relation summary list.

**Tech Stack:** Python 3.11, dataclasses, pytest

---

### Task 1: Add failing answer-rendering tests for concise path text and dedupe

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/qa/test_template_answering.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/template_answering.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_models.py`

**Step 1: Write the failing tests**
Add tests that assert:
- path steps render as `中文名(ID)` only
- duplicate `(from, relation, to)` hops appear once in the path report
- relation summary is rendered as a deduped list, not repeated inline prose
- verbose semantic description text does not appear in the final answer

Suggested test shape:
```python
def test_build_template_answer_dedupes_trace_edges_and_uses_compact_labels():
    bundle = OntologyEvidenceBundle(
        question='项目和机房里程碑是什么关系',
        seed_node_ids=['object_type:Project'],
        matched_node_ids=['object_type:Project', 'object_type:RoomMilestone'],
        matched_edge_ids=['e1', 'e2'],
        highlight_steps=[],
        evidence_chain=[],
        insufficient_evidence=False,
        search_trace=SearchTrace(
            seed_node_ids=['object_type:Project'],
            expansion_steps=[
                TraceExpansionStep(
                    step=1,
                    from_node_id='object_type:Project',
                    edge_id='e1',
                    to_node_id='object_type:RoomMilestone',
                    relation='HAS',
                ),
                TraceExpansionStep(
                    step=2,
                    from_node_id='object_type:Project',
                    edge_id='e2',
                    to_node_id='object_type:RoomMilestone',
                    relation='HAS',
                ),
            ],
        ),
        display_name_map={
            'object_type:Project': '项目(Project)',
            'object_type:RoomMilestone': '机房里程碑(RoomMilestone)',
        },
        relation_name_map={'HAS': '[包含]'},
    )

    answer = build_template_answer(bundle)

    assert answer.answer.count('随后从 项目(Project) 沿 [包含] 扩展到 机房里程碑(RoomMilestone)') == 1
    assert '表示一个面向客户的交付项目' not in answer.answer
    assert '\n- 项目(Project) [包含] 机房里程碑(RoomMilestone)' in answer.answer
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/qa/test_template_answering.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update `qa/template_answering.py` to:
- add a helper that dedupes `TraceExpansionStep` edges by `(from_node_id, relation, to_node_id)` while preserving first-seen order
- render path text with spaces and the exact `中文名(ID)` / `[关系]` format
- build a compact list-style relation summary from the deduped edges
- keep insufficient-evidence behavior unchanged except for concise labels

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/qa/test_template_answering.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add qa/template_answering.py tests/qa/test_template_answering.py
git commit -m "feat: simplify ontology trace rendering"
```

### Task 2: Add failing retrieval-model tests for bracketed relation labels

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/search/test_ontology_query_engine.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_engine.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_models.py`

**Step 1: Write the failing tests**
Extend `tests/search/test_ontology_query_engine.py` to assert:
- `relation_name_map['REFERENCES'] == '[引用]'`
- `relation_name_map['APPLIES_TO'] == '[作用于]'`
- `relation_name_map['OCCURS_AT'] == '[发生于位置]'`
- every mapped relation returned for the current ontology uses the bracketed format

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update `search/ontology_query_engine.py` so `_build_relation_name_map()` returns bracketed labels directly from the translation table.

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add search/ontology_query_engine.py tests/search/test_ontology_query_engine.py
git commit -m "feat: bracket ontology relation labels"
```

### Task 3: Full verification and smoke check for concise trace output

**Files:**
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/template_answering.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/search/ontology_query_engine.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/qa/test_template_answering.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/search/test_ontology_query_engine.py`
- Reference: `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/tests/server/test_ontology_http_app.py`

**Step 1: Run focused suites**
Run:
```bash
pytest tests/qa/test_template_answering.py -v
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: PASS.

**Step 2: Run server verification**
Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
```
Expected: PASS.

**Step 3: Run full regression**
Run:
```bash
pytest tests -q
```
Expected: PASS.

**Step 4: Smoke check rendered answer text**
Run the local server and ask a complex relation question. Confirm:
- the report uses `中文名(ID)` only
- duplicate path hops do not repeat
- relation summary is list-style and deduped
- bracketed relations like `[包含]` / `[引用]` are visible

**Step 5: Commit**
```bash
git add qa/template_answering.py search/ontology_query_engine.py tests/qa/test_template_answering.py tests/search/test_ontology_query_engine.py docs/plans/2026-03-18-ontology-trace-dedup-design.md docs/plans/2026-03-18-ontology-trace-dedup.md
git commit -m "feat: simplify ontology trace reports"
```
