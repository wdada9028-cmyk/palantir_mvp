from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cloud_delivery_ontology_palantir.qa.generator import GeneratorResult
from cloud_delivery_ontology_palantir.server.ontology_http_app import create_app


def _event_payloads(text: str, name: str) -> list[dict[str, object]]:
    import json
    chunks = [chunk for chunk in text.split('\n\n') if chunk.strip()]
    payloads: list[dict[str, object]] = []
    for chunk in chunks:
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines or lines[0] != f'event: {name}':
            continue
        data_line = next((line for line in lines if line.startswith('data: ')), None)
        if data_line:
            payloads.append(json.loads(data_line[len('data: '):]))
    return payloads


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


@pytest.fixture(autouse=True)
def _disable_network_generation(monkeypatch):
    async def _fake_iter_generated_instance_answer(*args, **kwargs):
        yield GeneratorResult(answer_text='测试回答', used_fallback=True)

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.server.ontology_http_service.iter_generated_instance_answer',
        _fake_iter_generated_instance_answer,
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


@pytest.mark.parametrize(
    ('question', 'expected_event_type'),
    [
        ('01机房断电会有哪些影响', 'power_outage'),
        ('01机房发生火灾会有哪些影响', 'fire'),
        ('01机房延期会带来哪些风险', 'delay'),
        ('01机房延误会影响哪些任务', 'delay'),
        ('01机房封锁会影响哪些施工', 'access_blocked'),
        ('01机房无法进入会影响哪些施工', 'access_blocked'),
    ],
)
def test_instance_qa_stream_detects_chinese_event_keywords(tmp_path: Path, question: str, expected_event_type: str):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': question})

    assert response.status_code == 200
    question_payload = _event_payloads(response.text, 'question_dsl')[0]
    assert question_payload['question_dsl']['scenario']['event_type'] == expected_event_type


@pytest.mark.parametrize('deadline_keyword', ['交付', '截止日期'])
def test_instance_qa_stream_detects_deadline_mode(tmp_path: Path, deadline_keyword: str):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': f'01机房火灾会不会影响到2026-04-10{deadline_keyword}'})

    assert response.status_code == 200
    question_payload = _event_payloads(response.text, 'question_dsl')[0]
    assert question_payload['question_dsl']['mode'] == 'deadline_risk_check'
    assert question_payload['question_dsl']['scenario']['event_type'] == 'fire'
