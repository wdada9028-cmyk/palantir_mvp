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



def test_qa_stream_emits_answer_delta_and_extended_answer_done(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    from cloud_delivery_ontology_palantir.qa.generator import GeneratorChunk, GeneratorResult

    async def fake_generator(question, bundle, fallback_answer):
        yield GeneratorChunk(delta='???', answer_text_so_far='???')
        yield GeneratorChunk(delta='????(ArrivalPlan)', answer_text_so_far='???????(ArrivalPlan)')
        yield GeneratorResult(answer_text='???????(ArrivalPlan) ?????????(PoD)?', used_fallback=False)

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.server.ontology_http_service.iter_generated_answer',
        fake_generator,
    )

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '???????? PoD?'})
    text = response.text

    assert response.status_code == 200
    assert text.index('event: anchor_node') < text.index('event: expand_neighbors')
    assert text.index('event: expand_neighbors') < text.index('event: filter_nodes')
    assert text.index('event: filter_nodes') < text.index('event: focus_subgraph')
    assert text.index('event: evidence_final') < text.index('event: answer_delta')
    assert text.index('event: answer_delta') < text.index('event: answer_done')
    assert '"answer":' in text
    assert '"answer_text":' in text
    assert '"trace_report":' in text
    assert '"used_fallback": false' in text



def test_qa_stream_generator_failure_still_returns_fallback_answer_done(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    async def failing_generator(question, bundle, fallback_answer):
        raise RuntimeError('generator boom')
        yield  # pragma: no cover

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.server.ontology_http_service.iter_generated_answer',
        failing_generator,
    )

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '???????? PoD?'})
    text = response.text

    assert response.status_code == 200
    assert 'event: answer_done' in text
    assert '"used_fallback": true' in text
    assert '"answer_text":' in text


def test_create_app_resolves_tql_input_before_loading_graph(tmp_path: Path, monkeypatch):
    import cloud_delivery_ontology_palantir.server.ontology_http_app as app_module

    tql_file = tmp_path / 'ontology.tql'
    tql_file.write_text('SELECT * FROM ontology;', encoding='utf-8')
    converted_file = tmp_path / 'ontology.converted.md'
    converted_file.write_text('# converted ontology', encoding='utf-8')

    resolver_calls: list[Path] = []
    parse_source_files: list[str] = []

    def fake_resolve_input_file(path: Path) -> Path:
        resolver_calls.append(Path(path))
        return converted_file

    def fake_parse_definition_markdown(text: str, *, source_file: str):
        parse_source_files.append(source_file)
        return object()

    class _DummyGraph:
        metadata = {'title': 'dummy'}

    monkeypatch.setattr(app_module, 'resolve_input_file', fake_resolve_input_file, raising=False)
    monkeypatch.setattr(app_module, 'parse_definition_markdown', fake_parse_definition_markdown)
    monkeypatch.setattr(app_module, 'build_definition_graph', lambda spec: _DummyGraph())
    monkeypatch.setattr(app_module, 'build_graph_payload', lambda graph: {'elements': []})
    monkeypatch.setattr(app_module, 'build_interactive_graph_html', lambda graph, title: '<html></html>')

    app = app_module.create_app(input_file=tql_file)

    assert resolver_calls == [tql_file]
    assert parse_source_files == [str(converted_file)]
