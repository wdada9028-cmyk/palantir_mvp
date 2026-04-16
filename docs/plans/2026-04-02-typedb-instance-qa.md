# TypeDB Instance QA Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current schema-only QA path with a TypeDB-backed instance QA path that keeps the existing `/api/qa/stream` entrypoint and answers questions from validated instance facts plus controlled reasoning.

**Architecture:** Keep the current query parser and ontology/schema graph as grounding assets, but add a new `instance_qa` orchestration layer. Natural language is converted into a controlled Question DSL, expanded into validated Fact Query DSL objects, rendered into backend-generated TypeQL, executed against a read-only single TypeDB database, then summarized via a structured reasoning layer and the existing streaming answer surface.

**Tech Stack:** Python 3.11, FastAPI, OpenAI-compatible Qwen API, TypeDB Python client, pathlib, dataclasses, PyYAML, pytest

---

### Task 1: Add TypeDB dependency and connection scaffolding

**Files:**
- Modify: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/requirements.txt`
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/__init__.py`
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/typedb_client.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_typedb_client.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.instance_qa.typedb_client import TypeDBConfig, load_typedb_config


def test_load_typedb_config_reads_single_database_env(monkeypatch):
    monkeypatch.setenv('TYPEDB_ADDRESS', 'localhost:1729')
    monkeypatch.setenv('TYPEDB_DATABASE', 'cloud_delivery')
    monkeypatch.setenv('TYPEDB_USERNAME', 'admin')
    monkeypatch.setenv('TYPEDB_PASSWORD', 'secret')

    config = load_typedb_config()

    assert config == TypeDBConfig(
        address='localhost:1729',
        database='cloud_delivery',
        username='admin',
        password='secret',
    )


def test_load_typedb_config_returns_none_when_required_env_missing(monkeypatch):
    monkeypatch.delenv('TYPEDB_ADDRESS', raising=False)
    monkeypatch.delenv('TYPEDB_DATABASE', raising=False)
    monkeypatch.delenv('TYPEDB_USERNAME', raising=False)
    monkeypatch.delenv('TYPEDB_PASSWORD', raising=False)

    assert load_typedb_config() is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_typedb_client.py -q`
Expected: FAIL because `instance_qa/typedb_client.py` does not exist yet.

**Step 3: Write minimal implementation**

- Add the TypeDB Python client dependency to `requirements.txt`
- Create `TypeDBConfig`
- Create `load_typedb_config()`
- Create a small read-only client wrapper skeleton with explicit config / connection / query errors

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_typedb_client.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add requirements.txt instance_qa/__init__.py instance_qa/typedb_client.py tests/instance_qa/test_typedb_client.py
git commit -m "feat: add typedb client scaffolding"
```

### Task 2: Build schema registry from the existing ontology graph

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/schema_registry.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_schema_registry.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import build_schema_registry
from cloud_delivery_ontology_palantir.ontology.definition_graph_builder import build_definition_graph
from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown


def test_build_schema_registry_collects_entity_attributes_and_adjacency():
    text = """# demo\n\n## Object Types（实体）\n\n### `Room`\n中文释义：机房\n关键属性：\n- `room_id`：机房ID\n\n### `WorkAssignment`\n中文释义：施工分配\n关键属性：\n- `assignment_id`：分配ID\n\n## Link Types（关系）\n- `WorkAssignment OCCURS_IN Room`：施工分配发生于机房\n"""
    spec = parse_definition_markdown(text, source_file='demo.md')
    graph = build_definition_graph(spec)

    registry = build_schema_registry(graph)

    assert 'Room' in registry.entities
    assert registry.entities['Room'].key_attributes == ['room_id']
    assert any(item.relation == 'OCCURS_IN' and item.direction == 'in' for item in registry.adjacency['Room'])
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_schema_registry.py -q`
Expected: FAIL because the registry module does not exist.

**Step 3: Write minimal implementation**

- Add registry dataclasses for entities, relations, adjacency entries
- Build registry from `OntologyGraph`
- Extract key properties from object attributes
- Build direction-aware adjacency

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_schema_registry.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/schema_registry.py tests/instance_qa/test_schema_registry.py
git commit -m "feat: add ontology-backed schema registry"
```

### Task 3: Add Question DSL models and extractor skeleton

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/question_models.py`
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/question_extractor.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_question_extractor.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.instance_qa.question_extractor import parse_question_dsl_payload


def test_parse_question_dsl_payload_normalizes_room_power_outage_question():
    payload = {
        'mode': 'impact_analysis',
        'anchor': {
            'entity': 'Room',
            'identifier': {'attribute': 'room_id', 'value': '01'},
            'surface': '01机房',
        },
        'scenario': {
            'event_type': 'power_outage',
            'duration': {'value': 7, 'unit': 'day'},
            'start_time': None,
            'severity': None,
            'raw_event': '断电',
        },
        'goal': {
            'type': 'list_impacts',
            'target_entity': None,
            'target_metric': None,
            'deadline': None,
        },
        'constraints': {'statuses': [], 'time_window': None, 'limit': 20},
    }

    question = parse_question_dsl_payload(payload)

    assert question.mode == 'impact_analysis'
    assert question.anchor.entity == 'Room'
    assert question.scenario.event_type == 'power_outage'
    assert question.scenario.duration.value == 7
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_extractor.py -q`
Expected: FAIL because the Question DSL modules do not exist.

**Step 3: Write minimal implementation**

- Define Question DSL dataclasses
- Add JSON payload parser
- Add the LLM prompt builder skeleton that only exposes allowed fields later

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_extractor.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/question_models.py instance_qa/question_extractor.py tests/instance_qa/test_question_extractor.py
git commit -m "feat: add question dsl models"
```

### Task 4: Add Question DSL validation against the schema registry

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/question_validator.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_question_validator.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.instance_qa.question_models import AnchorRef, GoalRef, QuestionDSL, ScenarioRef, DurationRef, ConstraintRef, IdentifierRef
from cloud_delivery_ontology_palantir.instance_qa.question_validator import validate_question_dsl


def test_validate_question_dsl_rejects_unknown_anchor_entity(schema_registry):
    question = QuestionDSL(
        mode='impact_analysis',
        anchor=AnchorRef(entity='UnknownRoom', identifier=IdentifierRef(attribute='room_id', value='01'), surface='01机房'),
        scenario=ScenarioRef(event_type='power_outage', duration=DurationRef(value=7, unit='day'), start_time=None, severity=None, raw_event='断电'),
        goal=GoalRef(type='list_impacts', target_entity=None, target_metric=None, deadline=None),
        constraints=ConstraintRef(statuses=[], time_window=None, limit=20),
    )

    error = validate_question_dsl(question, schema_registry)

    assert 'UnknownRoom' in error
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_validator.py -q`
Expected: FAIL because the validator module does not exist.

**Step 3: Write minimal implementation**

- Validate anchor entity, target entity, identifier attribute, limit, and event type
- Return explicit validation errors, not silent fallback

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_validator.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/question_validator.py tests/instance_qa/test_question_validator.py
git commit -m "feat: add question dsl validation"
```

### Task 5: Add Fact Query DSL models and planner

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/fact_query_models.py`
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/fact_query_planner.py`
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/event_profiles.yaml`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_fact_query_planner.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.instance_qa.fact_query_planner import build_fact_queries


def test_build_fact_queries_creates_anchor_and_neighbor_queries_for_room_power_outage(schema_registry):
    question = make_room_power_outage_question()

    queries = build_fact_queries(question, schema_registry)

    purposes = [item.purpose for item in queries]
    assert 'resolve_anchor' in purposes
    assert 'collect_neighbors' in purposes
    assert any(item.root.entity == 'Room' for item in queries)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_fact_query_planner.py -q`
Expected: FAIL because the planner modules do not exist.

**Step 3: Write minimal implementation**

- Define Fact Query DSL models
- Load event profiles from YAML
- Produce schema-driven anchor + neighbor queries
- Allow generic fallback when no event override exists

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_fact_query_planner.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/fact_query_models.py instance_qa/fact_query_planner.py instance_qa/event_profiles.yaml tests/instance_qa/test_fact_query_planner.py
git commit -m "feat: add fact query planner"
```

### Task 6: Add Fact Query DSL validation and deterministic TypeQL generation

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/fact_query_validator.py`
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/typeql_builder.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_fact_query_validator.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_typeql_builder.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.instance_qa.typeql_builder import build_typeql_query


def test_build_typeql_query_generates_match_for_room_anchor_lookup():
    fact_query = make_room_anchor_fact_query()

    typeql = build_typeql_query(fact_query)

    assert 'match' in typeql
    assert 'room_id' in typeql
    assert '01' in typeql
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_fact_query_validator.py tests/instance_qa/test_typeql_builder.py -q`
Expected: FAIL because the validator and builder modules do not exist.

**Step 3: Write minimal implementation**

- Validate entity names, attributes, traversal compatibility, projection, aggregate, and limits
- Deterministically generate read-only TypeQL from the validated DSL
- Keep builder narrow: only support the current DSL, reject everything else

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_fact_query_validator.py tests/instance_qa/test_typeql_builder.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/fact_query_validator.py instance_qa/typeql_builder.py tests/instance_qa/test_fact_query_validator.py tests/instance_qa/test_typeql_builder.py
git commit -m "feat: add controlled typeql generation"
```

### Task 7: Add TypeDB result mapping and reasoning layer

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/typedb_result_mapper.py`
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/reasoner.py`
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/result_formatter.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_typedb_result_mapper.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/instance_qa/test_reasoner.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.instance_qa.reasoner import assess_deadline_risk


def test_assess_deadline_risk_marks_overlap_as_at_risk():
    fact_pack = {
        'instances': {
            'PoD': [
                {
                    'pod_code': 'POD-001',
                    'planned_handover_time': '2026-04-09',
                }
            ]
        }
    }

    result = assess_deadline_risk(fact_pack, deadline='2026-04-10')

    assert result['deadline_assessment']['at_risk'] is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_typedb_result_mapper.py tests/instance_qa/test_reasoner.py -q`
Expected: FAIL because the mapper and reasoner modules do not exist.

**Step 3: Write minimal implementation**

- Map TypeDB rows into normalized fact packs
- Add generic propagation-based affected entity collection
- Add deadline heuristics over known time-bearing attributes
- Format structured reasoning output with confidence and evidence chains

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_typedb_result_mapper.py tests/instance_qa/test_reasoner.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/typedb_result_mapper.py instance_qa/reasoner.py instance_qa/result_formatter.py tests/instance_qa/test_typedb_result_mapper.py tests/instance_qa/test_reasoner.py
git commit -m "feat: add typedb result reasoning layer"
```

### Task 8: Add the instance QA orchestrator and replace the server path

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/instance_qa/orchestrator.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/server/ontology_http_app.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/server/ontology_http_service.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/qa/generator.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/qa/template_answering.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/server/test_ontology_http_app.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/integration/test_instance_qa_stream.py`

**Step 1: Write the failing tests**

```python
from fastapi.testclient import TestClient
from cloud_delivery_ontology_palantir.server.ontology_http_app import create_app


def test_qa_stream_emits_instance_qa_pipeline_events(tmp_path, monkeypatch):
    input_file = tmp_path / 'ontology.md'
    input_file.write_text(MINIMAL_ONTOLOGY_MARKDOWN, encoding='utf-8')

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.instance_qa.orchestrator.run_instance_qa',
        fake_instance_qa_result,
    )

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01机房断电一周会有哪些影响'})

    text = response.text
    assert 'event: question_dsl' in text
    assert 'event: fact_query_planned' in text
    assert 'event: typedb_result' in text
    assert 'event: reasoning_done' in text
    assert 'event: answer_done' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py -q`
Expected: FAIL because the orchestrator and new stream shape do not exist.

**Step 3: Write minimal implementation**

- Add `run_instance_qa(...)` orchestration entrypoint
- Replace `/api/qa/stream` backend path to call the orchestrator
- Update streaming service to emit the new step events
- Update `qa/generator.py` to summarize from schema summary + fact pack + reasoning result instead of schema-only relation facts
- Update deterministic fallback answer generation accordingly

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/orchestrator.py server/ontology_http_app.py server/ontology_http_service.py qa/generator.py qa/template_answering.py tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: replace schema qa path with typedb instance orchestrator"
```

### Task 9: Update the front-end QA panel to reflect instance-QA stages

**Files:**
- Modify: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/export/graph_export.py`
- Test: `C:/Users/w00949875/.codex/worktrees/8e93/palantir_mvp/tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_contains_instance_qa_stage_handlers():
    html = build_interactive_graph_html(graph)

    assert 'question_dsl' in html
    assert 'fact_query_planned' in html
    assert 'typedb_result' in html
    assert 'reasoning_done' in html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py -q`
Expected: FAIL because the front-end does not know the new event types yet.

**Step 3: Write minimal implementation**

- Teach the QA panel to render the new streamed step summaries
- Preserve answer streaming behavior
- Keep graph rendering stable; only change QA presentation and status trace

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: expose instance qa stream stages in ui"
```

### Task 10: Run full verification and smoke the end-to-end path

**Files:**
- Verify only

**Step 1: Run focused instance QA suite**

Run:
```bash
pytest tests/instance_qa -q
```
Expected: PASS

**Step 2: Run server and integration verification**

Run:
```bash
pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q
```
Expected: PASS

**Step 3: Run full test suite**

Run:
```bash
pytest tests -q
```
Expected: PASS

**Step 4: Run local serve smoke**

Run:
```bash
python -m cloud_delivery_ontology_palantir.cli serve-ontology --input-file typedb_schema_v4.tql --host 127.0.0.1 --port 8000
```
Expected: server starts successfully; `/api/qa/stream` emits instance-QA events and completes with `answer_done`.

**Step 5: Commit final verification touch-ups if any**

```bash
git add -A
git commit -m "test: verify typedb instance qa path"
```
