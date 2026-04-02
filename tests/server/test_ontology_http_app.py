from pathlib import Path

from fastapi.testclient import TestClient

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
