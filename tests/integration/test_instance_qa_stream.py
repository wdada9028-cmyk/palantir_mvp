from pathlib import Path

from fastapi.testclient import TestClient

from cloud_delivery_ontology_palantir.server.ontology_http_app import create_app


def _write_ontology(input_file: Path) -> None:
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


def test_instance_qa_stream_emits_new_event_order(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01机房断电一周会不会影响到2026-04-10交付'})

    assert response.status_code == 200
    text = response.text
    assert text.index('event: question_parsed') < text.index('event: question_dsl')
    assert text.index('event: question_dsl') < text.index('event: fact_query_planned')
    assert text.index('event: fact_query_planned') < text.index('event: typedb_result')
    assert text.index('event: typedb_result') < text.index('event: reasoning_done')
    assert text.index('event: reasoning_done') < text.index('event: answer_done')
