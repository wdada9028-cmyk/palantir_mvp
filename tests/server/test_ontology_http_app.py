from pathlib import Path
import json

import pytest
from fastapi.testclient import TestClient

from cloud_delivery_ontology_palantir.qa.generator import GeneratorResult
from cloud_delivery_ontology_palantir.server.ontology_http_app import create_app


def _write_relation_ontology(input_file: Path) -> None:
    input_file.write_text(
        """# 测试本体

## Object Types（实体）

### `Room`
中文释义：机房
关键属性：
- `room_id`：机房ID

### `WorkAssignment`
中文释义：施工分配
关键属性：
- `assignment_id`：分配ID

## Link Types（关系）
- `WorkAssignment OCCURS_IN Room`：施工分配发生于机房
""",
        encoding='utf-8',
    )


@pytest.fixture(autouse=True)
def _disable_network_generation(monkeypatch):
    async def _fake_iter_generated_instance_answer(*args, **kwargs):
        yield GeneratorResult(answer_text='测试回答', used_fallback=True)

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.server.ontology_http_service.iter_generated_instance_answer',
        _fake_iter_generated_instance_answer,
    )


def _event_payloads(text: str, name: str) -> list[dict[str, object]]:
    chunks = [chunk for chunk in text.split('\n\n') if chunk.strip()]
    payloads: list[dict[str, object]] = []
    for chunk in chunks:
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines or lines[0] != f'event: {name}':
            continue
        data_line = next((line for line in lines if line.startswith('data: ')), None)
        if data_line:
            payloads.append(json.loads(data_line[len('data: ') :]))
    return payloads


def test_create_app_serves_ontology_page_and_graph_payload(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)

    page = client.get('/ontology')
    graph = client.get('/api/graph')

    assert page.status_code == 200
    assert graph.status_code == 200
    assert 'elements' in graph.json()


def test_qa_stream_emits_instance_qa_pipeline_events(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01机房断电一周会有哪些影响'})

    assert response.status_code == 200
    text = response.text
    assert 'event: question_parsed' in text
    assert 'event: question_dsl' in text
    assert 'event: fact_query_planned' in text
    assert 'event: typedb_result' in text
    assert 'event: reasoning_done' in text
    assert 'event: answer_done' in text


def test_qa_stream_question_dsl_detects_power_outage_mode(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01机房断电会有哪些影响'})

    assert response.status_code == 200
    question_payload = _event_payloads(response.text, 'question_dsl')[0]
    assert question_payload['question_dsl']['mode'] == 'impact_analysis'
    assert question_payload['question_dsl']['scenario']['event_type'] == 'power_outage'


def test_qa_stream_preserves_links_and_anchor_metadata_in_fact_pack(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    import cloud_delivery_ontology_palantir.instance_qa.orchestrator as orch

    def fake_run_typeql_readonly(typeql: str):
        return (
            [
                {
                    '_entity': 'WorkAssignment',
                    'assignment_id': 'WA-001',
                    '_source_entity': 'WorkAssignment',
                    '_source_id': 'WA-001',
                    '_relation': 'OCCURS_IN',
                    '_target_entity': 'Room',
                    '_target_id': '01',
                }
            ],
            None,
        )

    monkeypatch.setattr(orch, '_run_typeql_readonly', fake_run_typeql_readonly)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01机房断电一周会有哪些影响'})

    assert response.status_code == 200
    typedb_payload = _event_payloads(response.text, 'typedb_result')[0]
    fact_pack = typedb_payload['fact_pack']
    assert fact_pack['links'] == [
        {
            'source_entity': 'WorkAssignment',
            'source_id': 'WA-001',
            'relation': 'OCCURS_IN',
            'target_entity': 'Room',
            'target_id': '01',
        }
    ]
    anchor = fact_pack['metadata']['anchor']
    assert anchor['entity'] == 'Room'
    assert anchor['id'] == '01'
    assert anchor['identifier'] == {'attribute': 'room_id', 'value': '01'}


def test_create_app_resolves_tql_input_before_loading_graph(tmp_path: Path, monkeypatch):
    import cloud_delivery_ontology_palantir.server.ontology_http_app as app_module

    tql_file = tmp_path / 'ontology.tql'
    tql_file.write_text('SELECT * FROM ontology;', encoding='utf-8')
    converted_file = tmp_path / 'ontology.converted.md'
    converted_file.write_text('# converted ontology', encoding='utf-8')

    resolver_calls: list[Path] = []
    parse_source_files: list[str] = []

    def fake_resolve_input_to_markdown(path: Path) -> Path:
        resolver_calls.append(Path(path))
        return converted_file

    def fake_parse_definition_markdown(text: str, *, source_file: str):
        parse_source_files.append(source_file)
        return object()

    class _DummyGraph:
        metadata = {'title': 'dummy'}

    monkeypatch.setattr(app_module, 'resolve_input_to_markdown', fake_resolve_input_to_markdown, raising=False)
    monkeypatch.setattr(app_module, 'parse_definition_markdown', fake_parse_definition_markdown)
    monkeypatch.setattr(app_module, 'build_definition_graph', lambda spec: _DummyGraph())
    monkeypatch.setattr(app_module, 'build_graph_payload', lambda graph: {'elements': []})
    monkeypatch.setattr(app_module, 'build_interactive_graph_html', lambda graph, title: '<html></html>')

    app = app_module.create_app(input_file=tql_file)

    assert resolver_calls == [tql_file]
    assert parse_source_files == [str(converted_file)]
    assert app.state.input_file == tql_file
    assert app.state.resolved_input_file == converted_file
