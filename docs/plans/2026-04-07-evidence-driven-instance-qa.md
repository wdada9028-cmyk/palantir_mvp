# Evidence-Driven TypeDB Instance QA Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current count-oriented instance QA answer path with an evidence-driven LLM answer path that uses full matched instance rows, aligned schema fragments, and relation paths.

**Architecture:** Keep deterministic schema-grounded TypeDB retrieval and controlled TypeQL generation in the backend, but add a new evidence assembly layer between retrieval and answer generation. The backend will package a bounded evidence bundle from matched instances plus negative evidence categories, then the generator will call the LLM with strict prompts that force evidence-only reasoning.

**Tech Stack:** Python 3.11, FastAPI, pytest, dataclasses, existing TypeDB client integration, existing OpenAI-compatible generator path

---

### Task 1: Add evidence data models

**Files:**
- Create: `instance_qa/evidence_models.py`
- Test: `tests/instance_qa/test_evidence_models.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.instance_qa.evidence_models import InstanceEvidence, SchemaContext


def test_instance_evidence_preserves_full_row_and_iid():
    evidence = InstanceEvidence(
        entity='Floor',
        iid='0x123',
        business_keys={'floor-id': 'L1'},
        attributes={'floor-id': 'L1', 'floor-no': 1, 'install-sequence': 1},
        schema_context=SchemaContext(entity_name='Floor', entity_zh='??', key_attributes=['floor-id'], relevant_relations=['floor-room']),
        paths=['Room(L1-A) <- floor-room - Floor(L1)'],
    )

    assert evidence.iid == '0x123'
    assert evidence.attributes['floor-no'] == 1
    assert 'install-sequence' in evidence.attributes
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_evidence_models.py -q`
Expected: FAIL because `instance_qa/evidence_models.py` does not exist.

**Step 3: Write minimal implementation**

- Add dataclasses for schema context, instance evidence, evidence edge, entity evidence group, empty entity record, unrelated entity record, omitted entity record, and evidence bundle.
- Add `to_dict()` helpers because the SSE layer will need JSON-safe payloads.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_evidence_models.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/evidence_models.py tests/instance_qa/test_evidence_models.py
git commit -m "feat: add evidence bundle models"
```

### Task 2: Build the evidence subgraph from TypeDB rows

**Files:**
- Create: `instance_qa/evidence_subgraph_builder.py`
- Modify: `instance_qa/typedb_result_mapper.py`
- Test: `tests/instance_qa/test_evidence_subgraph_builder.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.instance_qa.evidence_subgraph_builder import build_evidence_subgraph


def test_build_evidence_subgraph_keeps_full_attributes_and_edges():
    fact_pack = {
        'instances': {
            'Room': [{'iid': '0xroom', 'room_id': 'L1-A'}],
            'PoDPosition': [{'iid': '0xpos1', 'position_id': 'POS-001', 'position_status': 'ready'}],
        },
        'links': [
            {
                'source_entity': 'Room',
                'source_id': 'L1-A',
                'relation': 'ROOM_POSITION',
                'target_entity': 'PoDPosition',
                'target_id': 'POS-001',
            }
        ],
        'metadata': {'anchor': {'entity': 'Room', 'id': 'L1-A'}},
    }

    subgraph = build_evidence_subgraph(fact_pack)

    assert subgraph.nodes['PoDPosition'][0].attributes['position_id'] == 'POS-001'
    assert subgraph.edges[0].relation == 'ROOM_POSITION'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_evidence_subgraph_builder.py -q`
Expected: FAIL because the builder module does not exist yet.

**Step 3: Write minimal implementation**

- Extend `typedb_result_mapper.py` so matched rows preserve iid in a stable field.
- Build a node/edge/path structure from `fact_pack['instances']`, `fact_pack['links']`, and anchor metadata.
- Add dedupe by iid first, then business key fallback.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_evidence_subgraph_builder.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/evidence_subgraph_builder.py instance_qa/typedb_result_mapper.py tests/instance_qa/test_evidence_subgraph_builder.py
git commit -m "feat: build evidence subgraph from typedb facts"
```

### Task 3: Align matched instances to minimal schema fragments

**Files:**
- Create: `instance_qa/schema_instance_aligner.py`
- Modify: `instance_qa/schema_registry.py`
- Test: `tests/instance_qa/test_schema_instance_aligner.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.instance_qa.schema_instance_aligner import align_schema_context


def test_align_schema_context_returns_minimal_fragment_for_matched_entity(schema_registry):
    aligned = align_schema_context(
        entity='Floor',
        registry=schema_registry,
        relevant_relations=['floor-room'],
    )

    assert aligned.entity_name == 'Floor'
    assert 'floor_id' in aligned.key_attributes
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_schema_instance_aligner.py -q`
Expected: FAIL because the aligner module does not exist.

**Step 3: Write minimal implementation**

- Add a helper that converts `SchemaRegistry` entries into a compact schema context payload.
- Include entity name, optional Chinese label if available, key attributes, and only the relations that actually appear in the current evidence paths.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_schema_instance_aligner.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/schema_instance_aligner.py instance_qa/schema_registry.py tests/instance_qa/test_schema_instance_aligner.py
git commit -m "feat: align schema fragments to matched instances"
```

### Task 4: Build the evidence bundle with positive / empty / unrelated / omitted sections

**Files:**
- Create: `instance_qa/evidence_bundle_builder.py`
- Test: `tests/instance_qa/test_evidence_bundle_builder.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.instance_qa.evidence_bundle_builder import build_evidence_bundle


def test_build_evidence_bundle_separates_positive_and_empty_entities():
    bundle = build_evidence_bundle(
        question='L1-A??????????????',
        schema_entities=['Room', 'PoDPosition', 'PoDSchedule'],
        positive_entities={'PoDPosition'},
        empty_entities={'PoDSchedule': 'schema???????????'},
        unrelated_entities={},
        omitted_entities={},
        subgraph=make_subgraph(),
        registry=make_registry(),
    )

    assert bundle.positive_evidence[0].entity == 'PoDPosition'
    assert bundle.empty_entities[0].entity == 'PoDSchedule'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_evidence_bundle_builder.py -q`
Expected: FAIL because the builder module does not exist.

**Step 3: Write minimal implementation**

- Assemble positive evidence groups from the subgraph.
- Attach aligned schema context to every included instance.
- Classify empty, unrelated, and omitted entities with explicit reasons.
- Add a size cap per entity and capture overflow in `omitted_entities`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_evidence_bundle_builder.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/evidence_bundle_builder.py tests/instance_qa/test_evidence_bundle_builder.py
git commit -m "feat: assemble evidence bundle for instance qa"
```

### Task 5: Build LLM answer context and prompts

**Files:**
- Create: `instance_qa/llm_answer_context_builder.py`
- Create: `instance_qa/prompts.py`
- Test: `tests/instance_qa/test_llm_answer_context_builder.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.instance_qa.llm_answer_context_builder import build_llm_answer_context


def test_build_llm_answer_context_contains_full_instance_rows_and_negative_evidence():
    context = build_llm_answer_context(make_evidence_bundle())

    assert 'positive_evidence' in context.user_payload
    assert 'empty_entities' in context.user_payload
    assert 'floor-no' in context.user_payload
    assert '???????????' in context.system_prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_llm_answer_context_builder.py -q`
Expected: FAIL because the context builder and prompts modules do not exist.

**Step 3: Write minimal implementation**

- Add prompt constants in `instance_qa/prompts.py` for system/task/evidence/style constraints.
- Build a compact JSON-like user payload from the evidence bundle.
- Include instructions about full-row attribute use, empty entities, unrelated entities, omitted entities, and iid semantics.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_llm_answer_context_builder.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/llm_answer_context_builder.py instance_qa/prompts.py tests/instance_qa/test_llm_answer_context_builder.py
git commit -m "feat: add evidence-driven llm answer context"
```

### Task 6: Route the generator through the new evidence-driven prompt contract

**Files:**
- Modify: `qa/generator.py`
- Modify: `qa/template_answering.py`
- Test: `tests/qa/test_generator.py`
- Test: `tests/qa/test_template_answering.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.qa.generator import _build_instance_messages


def test_build_instance_messages_uses_evidence_bundle_payload():
    messages = _build_instance_messages(question='?????', llm_context=make_llm_context())

    assert messages[0]['role'] == 'system'
    assert 'empty_entities' in messages[1]['content']
    assert 'attributes' in messages[1]['content']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/qa/test_generator.py::test_build_instance_messages_uses_evidence_bundle_payload -q`
Expected: FAIL because the generator does not yet accept the new context.

**Step 3: Write minimal implementation**

- Add an instance-answer message builder that consumes the new LLM answer context object.
- Keep template fallback as the no-model / no-context fallback only.
- Do not remove the old generic generator path.

**Step 4: Run test to verify it passes**

Run: `pytest tests/qa/test_generator.py::test_build_instance_messages_uses_evidence_bundle_payload -q`
Expected: PASS

**Step 5: Commit**

```bash
git add qa/generator.py qa/template_answering.py tests/qa/test_generator.py tests/qa/test_template_answering.py
git commit -m "feat: use evidence-driven prompts for instance answers"
```

### Task 7: Integrate the orchestrator and SSE service with evidence stages

**Files:**
- Modify: `instance_qa/orchestrator.py`
- Modify: `server/ontology_http_service.py`
- Test: `tests/server/test_ontology_http_app.py`
- Test: `tests/integration/test_instance_qa_stream.py`

**Step 1: Write the failing test**

```python
def test_qa_stream_emits_evidence_bundle_stage(client):
    response = client.get('/api/qa/stream', params={'q': 'L1-A??????????????'})

    assert 'event: evidence_bundle_ready' in response.text
    assert 'event: llm_answer_context_ready' in response.text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_evidence_bundle_stage -q`
Expected: FAIL because the stream does not emit the new stages.

**Step 3: Write minimal implementation**

- Extend `InstanceQAResult` with evidence-bundle and llm-context fields.
- Build the evidence bundle in the orchestrator after `fact_pack` is created.
- Emit SSE stages for evidence build and context readiness.
- Feed the generator from the new evidence-driven context.

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_evidence_bundle_stage -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/orchestrator.py server/ontology_http_service.py tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: stream evidence-driven instance qa stages"
```

### Task 8: Add full regression coverage for evidence-driven answers

**Files:**
- Modify: `tests/server/test_ontology_http_app.py`
- Modify: `tests/integration/test_instance_qa_stream.py`
- Modify: `tests/instance_qa/test_typedb_result_mapper.py`
- Modify: `tests/instance_qa/test_reasoner.py`
- Modify: `tests/test_...` only if strictly needed

**Step 1: Write the failing tests**

```python
def test_answer_payload_references_concrete_instance_attributes():
    payload = stream_answer_payload_for_room_outage()

    assert 'position_id' in payload['answer_context']
    assert 'PoDPosition' in payload['answer_context']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py -q`
Expected: FAIL because the evidence-driven output is not fully wired yet.

**Step 3: Write minimal implementation**

- Tighten mapper and stream assertions around iid preservation, full-row preservation, and negative evidence categories.
- Reduce or remove any old count-only assumptions from tests that no longer reflect the main answer path.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/instance_qa tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py
git commit -m "test: cover evidence-driven instance qa output"
```

### Task 9: Run final verification

**Files:**
- Modify only if failures require follow-up fixes.

**Step 1: Run focused QA verification**

Run: `pytest tests/instance_qa -q`
Expected: PASS

**Step 2: Run server and integration verification**

Run: `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 3: Run full suite**

Run: `pytest tests -q`
Expected: PASS

**Step 4: Review working tree**

Run: `git status --short --branch`
Expected: only the intended evidence-driven files are modified.

**Step 5: Commit final fixups if needed**

```bash
git add <intended files>
git commit -m "feat: finalize evidence-driven instance qa path"
```
