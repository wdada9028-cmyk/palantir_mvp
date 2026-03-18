# Ontology Intent Resolver Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Qwen2.5-32B semantic seed resolver that maps fuzzy Chinese questions to ontology schema IDs, while preserving deterministic fallback retrieval and improving user-facing trace wording.

**Architecture:** Introduce a standalone `intent_resolver` module that uses the in-memory ontology graph to build prompt context and call an OpenAI-compatible Qwen endpoint. `retrieve_ontology_evidence()` will consume that resolver output before the existing seed-selection path, then continue the current traversal unchanged. Answer rendering will use bundle-level display maps so path reports show localized `???(??ID)` entity labels and translated relation names.

**Tech Stack:** Python 3.11, `httpx`, dataclasses, pytest

---

### Task 1: Add failing tests for the new intent resolver module

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/tests/search/test_intent_resolver.py`
- Create: `D:/????/AI?????/??????/palantir_mvp/search/intent_resolver.py`
- Reference: `D:/????/AI?????/??????/palantir_mvp/models/ontology.py`

**Step 1: Write the failing tests**
Add tests that cover:
- valid OpenAI-compatible JSON returning ontology seeds
- invalid JSON falling back to empty seeds with error text
- missing config returning `source == "disabled"`
- returned seeds filtered to graph object IDs only

Suggested test shape:
```python
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject
from cloud_delivery_ontology_palantir.search.intent_resolver import resolve_intent


def test_resolve_intent_returns_filtered_llm_seeds(monkeypatch):
    graph = OntologyGraph()
    graph.add_object(OntologyObject(
        id='object_type:ArrivalPlan',
        type='ObjectType',
        name='ArrivalPlan',
        attributes={'chinese_description': '????'},
    ))

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.setenv('QWEN_MODEL', 'qwen2.5-32b-instruct')

    class FakeResponse:
        def raise_for_status(self):
            return None
        def json(self):
            return {
                'choices': [{
                    'message': {
                        'content': '{"seeds": ["object_type:ArrivalPlan", "object_type:Missing"], "reasoning": "????????"}'
                    }
                }]
            }

    class FakeClient:
        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr('cloud_delivery_ontology_palantir.search.intent_resolver.get_http_client', lambda: FakeClient())

    result = resolve_intent(graph, '?????')

    assert result.seeds == ['object_type:ArrivalPlan']
    assert result.source == 'llm'
    assert '????' in result.reasoning
```

**Step 2: Run tests to verify they fail**
Run:
```bash
pytest tests/search/test_intent_resolver.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Create `search/intent_resolver.py` with:
- `IntentResolution`
- environment-based config loading
- ontology prompt-context builder
- `get_http_client()` using `httpx.Client` and limits
- JSON parsing / validation / error capture
- non-throwing fallback behavior

**Step 4: Run tests to verify they pass**
Run:
```bash
pytest tests/search/test_intent_resolver.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add tests/search/test_intent_resolver.py search/intent_resolver.py
git commit -m "feat: add ontology intent resolver"
```

### Task 2: Wire semantic seed resolution into the query engine with fallback

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/search/ontology_query_engine.py`
- Modify: `D:/????/AI?????/??????/palantir_mvp/search/ontology_query_models.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/search/test_ontology_query_engine.py`
- Reference: `D:/????/AI?????/??????/palantir_mvp/search/intent_resolver.py`

**Step 1: Write the failing tests**
Extend `tests/search/test_ontology_query_engine.py` with tests that assert:
- resolver-provided seeds are used instead of keyword scoring
- resolver failure falls back to the current keyword path
- `SearchTrace` includes resolver source / reasoning / error
- the bundle carries `display_name_map` and `relation_name_map`

Suggested test shape:
```python
def test_retrieve_ontology_evidence_prefers_llm_seed_resolution(monkeypatch):
    graph = build_test_graph()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        lambda graph, query: IntentResolution(
            seeds=['object_type:ArrivalPlan'],
            reasoning='??????????????????',
            source='llm',
            error='',
        ),
    )

    result = retrieve_ontology_evidence(graph, '?????')

    assert result.seed_node_ids == ['object_type:ArrivalPlan']
    assert result.search_trace.seed_resolution_source == 'llm'
    assert '?????' not in result.search_trace.seed_resolution_reasoning
```

**Step 2: Run tests to verify they fail**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update:
- `SearchTrace` to record resolver metadata
- `OntologyEvidenceBundle` to carry display/relation maps
- `retrieve_ontology_evidence()` to call `resolve_intent()` first and fallback to `_select_seed_node_ids()` if needed
- helper functions to build localized entity/relation maps from the graph

**Step 4: Run tests to verify they pass**
Run:
```bash
pytest tests/search/test_ontology_query_engine.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add search/ontology_query_engine.py search/ontology_query_models.py tests/search/test_ontology_query_engine.py
git commit -m "feat: add semantic seed fallback flow"
```

### Task 3: Localize template answers and search-trace wording

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/qa/template_answering.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/qa/test_template_answering.py`
- Reference: `D:/????/AI?????/??????/palantir_mvp/search/ontology_query_models.py`

**Step 1: Write the failing tests**
Extend `tests/qa/test_template_answering.py` to assert:
- entity labels render as `???(??ID)`
- relation names render in Chinese brackets such as `[??]`
- path reports no longer contain raw English-only phrases like `REFERENCES` / `PoD`

Suggested test shape:
```python
def test_build_template_answer_localizes_trace_report():
    bundle = OntologyEvidenceBundle(
        question='?????',
        seed_node_ids=['object_type:ArrivalPlan'],
        matched_node_ids=['object_type:ArrivalPlan', 'object_type:PoDPosition'],
        matched_edge_ids=['e1'],
        highlight_steps=[],
        evidence_chain=[],
        insufficient_evidence=False,
        search_trace=SearchTrace(
            seed_node_ids=['object_type:ArrivalPlan'],
            seed_resolution_source='llm',
            seed_resolution_reasoning='??????????????????',
            expansion_steps=[
                TraceExpansionStep(
                    step=1,
                    from_node_id='object_type:ArrivalPlan',
                    edge_id='e1',
                    to_node_id='object_type:PoDPosition',
                    relation='REFERENCES',
                )
            ],
        ),
        display_name_map={
            'object_type:ArrivalPlan': '????(ArrivalPlan)',
            'object_type:PoDPosition': '??(PoDPosition)',
        },
        relation_name_map={'REFERENCES': '??'},
    )

    answer = build_template_answer(bundle)

    assert '????(ArrivalPlan)' in answer.answer
    assert '[??]' in answer.answer
    assert '??(PoDPosition)' in answer.answer
```

**Step 2: Run tests to verify they fail**
Run:
```bash
pytest tests/qa/test_template_answering.py -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update `qa/template_answering.py` to:
- render seed and expansion names from `display_name_map`
- render relations from `relation_name_map`
- include resolver reasoning in the path report when available
- keep insufficient-evidence behavior unchanged except for localized labels

**Step 4: Run tests to verify they pass**
Run:
```bash
pytest tests/qa/test_template_answering.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add qa/template_answering.py tests/qa/test_template_answering.py
git commit -m "feat: localize ontology trace reports"
```

### Task 4: End-to-end verification for semantic retrieval and fallback

**Files:**
- Reference: `D:/????/AI?????/??????/palantir_mvp/search/intent_resolver.py`
- Reference: `D:/????/AI?????/??????/palantir_mvp/search/ontology_query_engine.py`
- Reference: `D:/????/AI?????/??????/palantir_mvp/qa/template_answering.py`
- Reference: `D:/????/AI?????/??????/palantir_mvp/tests/search/test_intent_resolver.py`
- Reference: `D:/????/AI?????/??????/palantir_mvp/tests/search/test_ontology_query_engine.py`
- Reference: `D:/????/AI?????/??????/palantir_mvp/tests/qa/test_template_answering.py`

**Step 1: Run focused suites**
Run:
```bash
pytest tests/search/test_intent_resolver.py -v
pytest tests/search/test_ontology_query_engine.py -v
pytest tests/qa/test_template_answering.py -v
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

**Step 4: Optional smoke checks**
If Qwen config is available:
```bash
python -m cloud_delivery_ontology_palantir.cli serve-ontology --input-file "D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md" --host 127.0.0.1 --port 8000
```
Manual checks:
- ask `?????`
- confirm ArrivalPlan to PoDPosition style chain is highlighted
- confirm trace wording uses localized labels

If Qwen config is unavailable, ask `ArrivalPlan` and confirm the legacy keyword path still works.

**Step 5: Commit**
```bash
git add search/intent_resolver.py search/ontology_query_engine.py search/ontology_query_models.py qa/template_answering.py tests/search/test_intent_resolver.py tests/search/test_ontology_query_engine.py tests/qa/test_template_answering.py docs/plans/2026-03-18-ontology-intent-resolver-design.md docs/plans/2026-03-18-ontology-intent-resolver.md
git commit -m "feat: add ontology semantic seed resolution"
```
