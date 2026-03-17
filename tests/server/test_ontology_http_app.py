from pathlib import Path

from fastapi.testclient import TestClient

from cloud_delivery_ontology_palantir.server.ontology_http_app import create_app


def _write_minimal_ontology(input_file: Path) -> None:
    input_file.write_text(
        """# 测试本体

## 4. Object Types
## 4.1 项目与目标层
### `Project`
中文释义：项目
关键属性：
- `project_id`: 项目ID

### `Goal`
中文释义：目标
关键属性：
- `goal_id`: 目标ID

## 5. Link Types
### 5.1 项目与目标关系
- `Project HAS Goal`: 项目包含目标
""",
        encoding='utf-8',
    )


def _write_relation_ontology(input_file: Path) -> None:
    input_file.write_text(
        """# 测试本体

## 4. Object Types
## 4.3 设备与物流层
### `PoD`
中文释义：设备落位点
关键属性：
- `pod_id`: PoD ID

## 4.6 决策与解释层
### `ArrivalPlan`
中文释义：到货计划
关键属性：
- `arrival_plan_id`: 到货计划ID

## 5. Link Types
### 5.1 决策关系
- `ArrivalPlan APPLIES_TO PoD`: 到货计划作用于 PoD
""",
        encoding='utf-8',
    )


def test_create_app_serves_ontology_page_and_graph_payload(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_minimal_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)

    page = client.get('/ontology')
    graph = client.get('/api/graph')

    assert page.status_code == 200
    assert 'text/html' in page.headers['content-type']
    assert '智能问答助手' in page.text
    assert graph.status_code == 200
    assert 'elements' in graph.json()


def test_graph_api_returns_same_payload_shape_as_export(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_minimal_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    payload = client.get('/api/graph').json()

    assert 'elements' in payload
    assert 'relationLegend' in payload
    assert 'metricGroupId' in payload


def test_qa_stream_emits_sse_steps_and_final_answer(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'PoD 有什么关系'})

    assert response.status_code == 200
    text = response.text
    assert 'event: anchor_node' in text
    assert 'event: evidence' in text
    assert 'event: answer_done' in text


def test_qa_stream_keeps_legacy_event_order_and_payload_shape(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'PoD 有什么关系'})
    text = response.text

    assert text.index('event: anchor_node') < text.index('event: expand_neighbors')
    assert text.index('event: expand_neighbors') < text.index('event: filter_nodes')
    assert text.index('event: filter_nodes') < text.index('event: focus_subgraph')
    assert text.index('event: focus_subgraph') < text.index('event: evidence')
    assert text.index('event: evidence') < text.index('event: answer_done')
    assert 'step_title' not in text
    assert 'new_node_ids' not in text
    assert 'focus_node_ids' not in text


def test_qa_stream_emits_new_trace_events_in_order(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'PoD 有什么关系'})
    text = response.text

    assert 'event: trace_anchor' in text
    assert 'event: trace_expand' in text
    assert 'event: evidence_final' in text
    assert text.index('event: trace_anchor') < text.index('event: trace_expand')
    assert text.index('event: trace_expand') < text.index('event: evidence_final')
    assert text.index('event: evidence_final') < text.index('event: answer_done')
    assert '"delay_ms":' in text
