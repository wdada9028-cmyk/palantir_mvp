# Ontology HTTP SSE Local Single-Machine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local FastAPI HTTP page for the markdown-driven ontology graph, add deterministic ontology retrieval over the current schema graph, and stream retrieval animation + evidence chain to the browser via SSE without any LLM.

**Architecture:** The server loads the ontology markdown file into a single in-memory `OntologyGraph` and shared Cytoscape payload at startup. `/ontology` serves the page, `/api/graph` exposes the graph payload, and `/api/qa/stream` emits deterministic retrieval steps (`anchor_node`, `expand_neighbors`, `filter_nodes`, `focus_subgraph`, `evidence`, `answer_done`) that the existing Cytoscape front end replays as graph animations while rendering a persistent evidence chain and template answer.

**Tech Stack:** Python 3.11+, FastAPI, SSE (`StreamingResponse`), Cytoscape.js, existing markdown parser/build pipeline, `pytest`, `fastapi.testclient`, no LLM.

**Repository note:** This workspace has no `.git` directory. Replace normal commit steps with a `SESSION_LOG.md` checkpoint update after each completed task.

---

### Task 1: Create the FastAPI app shell and basic HTTP routes

**Files:**
- Create: `server/__init__.py`
- Create: `server/ontology_http_app.py`
- Test: `tests/server/test_ontology_http_app.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from fastapi.testclient import TestClient

from cloud_delivery_ontology_palantir.server.ontology_http_app import create_app


def test_create_app_serves_ontology_page_and_graph_payload(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    input_file.write_text(
        '# 测试本体\n\n## 4.1 项目与目标层\n### Project\n- 中文释义：项目\n',
        encoding='utf-8',
    )

    app = create_app(input_file=input_file)
    client = TestClient(app)

    page = client.get('/ontology')
    graph = client.get('/api/graph')

    assert page.status_code == 200
    assert 'text/html' in page.headers['content-type']
    assert '智能问答助手' in page.text
    assert graph.status_code == 200
    assert 'elements' in graph.json()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py::test_create_app_serves_ontology_page_and_graph_payload -v`
Expected: FAIL because `server/ontology_http_app.py` does not exist.

**Step 3: Write minimal implementation**

Create a FastAPI factory with:

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse


def create_app(*, input_file: Path) -> FastAPI:
    app = FastAPI()

    @app.get('/ontology', response_class=HTMLResponse)
    def ontology_page() -> str:
        return '<html><body>placeholder</body></html>'

    @app.get('/api/graph', response_class=JSONResponse)
    def graph_payload() -> dict[str, object]:
        return {'elements': []}

    return app
```

Then replace placeholders by actually loading the ontology graph through the existing markdown build pipeline helpers.

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py::test_create_app_serves_ontology_page_and_graph_payload -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 1 completion.

### Task 2: Expose a shared graph payload builder for both export and HTTP server

**Files:**
- Modify: `export/graph_export.py`
- Modify: `server/ontology_http_app.py`
- Test: `tests/integration/test_definition_graph_export.py`
- Test: `tests/server/test_ontology_http_app.py`

**Step 1: Write the failing test**

Add this to `tests/server/test_ontology_http_app.py`:

```python
def test_graph_api_returns_same_payload_shape_as_export(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    input_file.write_text(
        '# 测试本体\n\n## 4.1 项目与目标层\n### Project\n- 中文释义：项目\n- 关键属性：project_id：项目ID\n',
        encoding='utf-8',
    )

    app = create_app(input_file=input_file)
    client = TestClient(app)
    payload = client.get('/api/graph').json()

    assert 'elements' in payload
    assert 'relationLegend' in payload
    assert 'metricGroupId' in payload
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py::test_graph_api_returns_same_payload_shape_as_export -v`
Expected: FAIL because the server does not yet reuse the exporter payload builder.

**Step 3: Write minimal implementation**

In `export/graph_export.py`:
- rename private `_build_graph_payload(graph)` to public `build_graph_payload(graph)`
- update `build_interactive_graph_html()` to call the public function

In `server/ontology_http_app.py`:
- build the graph with the existing parser/builder pipeline
- call `build_graph_payload(graph)` for `/api/graph`
- use the same `graph` when rendering `/ontology`

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py::test_graph_api_returns_same_payload_shape_as_export -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 2 completion.

### Task 3: Add deterministic ontology retrieval models and query engine

**Files:**
- Create: `search/__init__.py`
- Create: `search/ontology_query_models.py`
- Create: `search/ontology_query_engine.py`
- Test: `tests/search/test_ontology_query_engine.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation
from cloud_delivery_ontology_palantir.search.ontology_query_engine import retrieve_ontology_evidence


def test_retrieve_ontology_evidence_returns_animation_steps_and_chain():
    graph = OntologyGraph(metadata={'title': '本体'})
    graph.add_object(
        OntologyObject(
            id='object_type:PoD',
            type='ObjectType',
            name='PoD',
            attributes={
                'group': '4.3 设备与物流层',
                'chinese_description': '设备落位点',
                'key_properties': [{'name': 'pod_id', 'description': 'PoD ID'}],
            },
        )
    )
    graph.add_object(
        OntologyObject(
            id='object_type:ArrivalPlan',
            type='ObjectType',
            name='ArrivalPlan',
            attributes={'group': '4.6 决策与解释层', 'chinese_description': '到货计划'},
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id='object_type:ArrivalPlan',
            target_id='object_type:PoD',
            relation='APPLIES_TO',
            attributes={'description': '到货计划作用于PoD'},
        )
    )

    result = retrieve_ontology_evidence(graph, 'PoD 有什么相关关系')

    assert result.seed_node_ids == ['object_type:PoD']
    assert result.highlight_steps
    assert result.evidence_chain
    assert any(step.action == 'anchor_node' for step in result.highlight_steps)
    assert any(item.kind == 'relation' for item in result.evidence_chain)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_ontology_query_engine.py::test_retrieve_ontology_evidence_returns_animation_steps_and_chain -v`
Expected: FAIL because the search package does not exist.

**Step 3: Write minimal implementation**

Create models like:

```python
from dataclasses import dataclass, field

@dataclass(slots=True)
class RetrievalStep:
    action: str
    message: str
    node_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

@dataclass(slots=True)
class EvidenceItem:
    evidence_id: str
    kind: str
    label: str
    message: str
    node_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    why_matched: list[str] = field(default_factory=list)

@dataclass(slots=True)
class OntologyEvidenceBundle:
    question: str
    seed_node_ids: list[str]
    matched_node_ids: list[str]
    matched_edge_ids: list[str]
    highlight_steps: list[RetrievalStep]
    evidence_chain: list[EvidenceItem]
    insufficient_evidence: bool
```

Implement `retrieve_ontology_evidence(graph, question)` to:
- normalize question tokens
- score node names, Chinese descriptions, group names, property names, property descriptions, notes, rules, and relation labels
- choose top seed nodes
- expand one-hop adjacent business edges
- produce ordered `highlight_steps`
- produce ordered `evidence_chain`
- mark `insufficient_evidence=True` if nothing meaningful is matched

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_ontology_query_engine.py::test_retrieve_ontology_evidence_returns_animation_steps_and_chain -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 3 completion.

### Task 4: Add template-based answer assembly from ontology evidence

**Files:**
- Create: `qa/__init__.py`
- Create: `qa/template_answering.py`
- Test: `tests/qa/test_template_answering.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.qa.template_answering import build_template_answer
from cloud_delivery_ontology_palantir.search.ontology_query_models import EvidenceItem, OntologyEvidenceBundle, RetrievalStep


def test_build_template_answer_mentions_evidence_ids_and_insufficient_evidence():
    bundle = OntologyEvidenceBundle(
        question='哪些服务器宕机',
        seed_node_ids=['object_type:PoD'],
        matched_node_ids=['object_type:PoD'],
        matched_edge_ids=[],
        highlight_steps=[RetrievalStep(action='anchor_node', message='定位到 PoD', node_ids=['object_type:PoD'])],
        evidence_chain=[
            EvidenceItem(
                evidence_id='E1',
                kind='seed',
                label='PoD',
                message='问题命中了实体 PoD',
                node_ids=['object_type:PoD'],
                why_matched=['实体名匹配'],
            )
        ],
        insufficient_evidence=True,
    )

    answer = build_template_answer(bundle)

    assert '证据不足' in answer.answer
    assert '[E1]' in answer.answer
    assert answer.insufficient_evidence is True
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/qa/test_template_answering.py::test_build_template_answer_mentions_evidence_ids_and_insufficient_evidence -v`
Expected: FAIL because the template answer module does not exist.

**Step 3: Write minimal implementation**

Create:

```python
from dataclasses import dataclass

@dataclass(slots=True)
class TemplateAnswer:
    answer: str
    insufficient_evidence: bool
```

Implement `build_template_answer(bundle)` to generate:
- a positive schema answer when entity/relation evidence exists
- an explicit insufficiency answer when the question asks beyond schema evidence
- mandatory evidence references like `[E1][E2]`

**Step 4: Run test to verify it passes**

Run: `pytest tests/qa/test_template_answering.py::test_build_template_answer_mentions_evidence_ids_and_insufficient_evidence -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 4 completion.

### Task 5: Add SSE streaming service that converts retrieval results into browser events

**Files:**
- Create: `server/ontology_http_service.py`
- Modify: `server/ontology_http_app.py`
- Test: `tests/server/test_ontology_http_app.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from fastapi.testclient import TestClient

from cloud_delivery_ontology_palantir.server.ontology_http_app import create_app


def test_qa_stream_emits_sse_steps_and_final_answer(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    input_file.write_text(
        '# 测试本体\n\n## 4.3 设备与物流层\n### PoD\n- 中文释义：设备落位点\n\n## 5. 关系\n- ArrivalPlan APPLIES_TO PoD：到货计划作用于 PoD\n',
        encoding='utf-8',
    )

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'PoD 有什么关系'})

    assert response.status_code == 200
    text = response.text
    assert 'event: anchor_node' in text
    assert 'event: evidence' in text
    assert 'event: answer_done' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_sse_steps_and_final_answer -v`
Expected: FAIL because `/api/qa/stream` does not exist.

**Step 3: Write minimal implementation**

In `server/ontology_http_service.py`, create helpers:

```python
import json
from collections.abc import Iterable


def sse_event(name: str, payload: dict[str, object]) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def iter_qa_events(...):
    yield sse_event('anchor_node', {...})
    yield sse_event('expand_neighbors', {...})
    yield sse_event('evidence', {...})
    yield sse_event('answer_done', {...})
```

In `server/ontology_http_app.py`:
- add `GET /api/qa/stream`
- call `retrieve_ontology_evidence()`
- call `build_template_answer()`
- return `StreamingResponse(iter_qa_events(...), media_type='text/event-stream')`

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_sse_steps_and_final_answer -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 5 completion.

### Task 6: Extend the Cytoscape page into HTTP/SSE interactive mode

**Files:**
- Modify: `export/graph_export.py`
- Modify: `server/ontology_http_app.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from cloud_delivery_ontology_palantir.export.graph_export import export_interactive_graph_html
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph


def test_exported_html_contains_sse_qa_hooks_and_evidence_clickback(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '本体建模 v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'EventSource' in text
    assert 'playRetrievalEvent' in text
    assert 'startQaStream' in text
    assert 'renderEvidenceChain' in text
    assert 'replayEvidenceFocus' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_sse_qa_hooks_and_evidence_clickback -v`
Expected: FAIL because the page has no SSE client logic.

**Step 3: Write minimal implementation**

In `export/graph_export.py`:
- add an HTTP/SSE mode switch or default the page to call `/api/qa/stream`
- wire the QA submit button to `startQaStream(question)`
- consume SSE events with `EventSource`
- implement `playRetrievalEvent(eventType, payload)` to animate the graph
- implement `renderEvidenceChain(chain)` and `replayEvidenceFocus(evidenceId)`
- keep existing node detail float card behavior unchanged
- keep current layout baseline unchanged

Suggested front-end functions:

```javascript
function startQaStream(question) { ... }
function playRetrievalEvent(eventType, payload) { ... }
function renderEvidenceChain(chain) { ... }
function replayEvidenceFocus(evidenceId) { ... }
function persistFinalEvidence(result) { ... }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_sse_qa_hooks_and_evidence_clickback -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 6 completion.

### Task 7: Add CLI entrypoint for local serving and verify end-to-end

**Files:**
- Modify: `cli.py`
- Modify: `__init__.py`
- Modify: `server/ontology_http_app.py`
- Test: `tests/integration/test_ontology_http_cli.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.cli import main


def test_cli_exposes_serve_ontology_subcommand():
    rc = main([
        'serve-ontology',
        '--help',
    ])
    assert rc == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_ontology_http_cli.py::test_cli_exposes_serve_ontology_subcommand -v`
Expected: FAIL because `serve-ontology` is not registered.

**Step 3: Write minimal implementation**

In `cli.py`:
- add subcommand `serve-ontology`
- required args: `--input-file`
- optional args: `--host`, `--port`
- implement it by constructing the FastAPI app and calling `uvicorn.run(...)`

Example shape:

```python
serve_parser = subparsers.add_parser('serve-ontology', help='Serve ontology HTTP page locally')
serve_parser.add_argument('--input-file', type=str, required=True)
serve_parser.add_argument('--host', type=str, default='127.0.0.1')
serve_parser.add_argument('--port', type=int, default=8000)
```

Keep `build-ontology` behavior untouched.

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_ontology_http_cli.py::test_cli_exposes_serve_ontology_subcommand -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 7 completion.

### Task 8: Run the complete verification set and manual smoke test

**Files:**
- Modify if needed: `SESSION_LOG.md`
- Smoke-test target: `[本体建模] 围绕美团2个核心决策v2.md`

**Step 1: Run focused tests**

Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
pytest tests/search/test_ontology_query_engine.py -v
pytest tests/qa/test_template_answering.py -v
pytest tests/integration/test_definition_graph_export.py -v
pytest tests/integration/test_ontology_http_cli.py -v
```

Expected: all PASS.

**Step 2: Run full suite**

Run: `pytest tests -q`
Expected: PASS with zero failures.

**Step 3: Manual smoke test**

Run:
```bash
python -m cloud_delivery_ontology_palantir.cli serve-ontology --input-file "D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/[本体建模] 围绕美团2个核心决策v2.md" --host 127.0.0.1 --port 8000
```

Open: `http://127.0.0.1:8000/ontology`

Verify manually:
- 页面正常显示图谱
- 点击节点仍显示浮层详情
- 提问后图谱按步骤高亮
- 证据链显示在问答面板中
- 点击证据条目会重新聚焦对应节点/边
- 对实例/实时状态问题显示“证据不足”而不是编造答案

**Step 4: Final checkpoint**

Update `SESSION_LOG.md` with:
- verification commands used
- test results
- manual smoke result
- remaining gaps (if any)
