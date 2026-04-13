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
关键属性:
- `room_id`：机房ID

### `WorkAssignment`
中文释义：施工分配
关键属性:
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
    assert text.index('event: typedb_result') < text.index('event: evidence_bundle_ready')
    assert text.index('event: evidence_bundle_ready') < text.index('event: llm_answer_context_ready')
    assert text.index('event: llm_answer_context_ready') < text.index('event: reasoning_done')
    assert text.index('event: reasoning_done') < text.index('event: trace_summary_ready')
    assert text.index('event: trace_summary_ready') < text.index('event: answer_done')


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



def test_instance_qa_stream_emits_schema_trace_events_before_typedb_queries(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'Room WorkAssignment relation'})

    assert response.status_code == 200
    text = response.text
    assert 'event: trace_anchor' in text
    assert 'event: evidence_final' in text
    assert text.index('event: question_dsl') < text.index('event: trace_anchor')
    assert text.index('event: evidence_final') < text.index('event: fact_query_planned')


def test_instance_qa_stream_trace_expand_payload_uses_search_trace_snapshots(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'Room WorkAssignment relation'})

    assert response.status_code == 200
    expand_payloads = _event_payloads(response.text, 'trace_expand')
    assert expand_payloads
    expand_payload = expand_payloads[0]
    assert 'snapshot_node_ids' in expand_payload
    assert 'snapshot_edge_ids' in expand_payload
    assert 'delay_ms' in expand_payload

def test_instance_qa_stream_answer_done_contains_trace_summary_sections(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01??????????'})

    assert response.status_code == 200
    trace_summary_payload = _event_payloads(response.text, 'trace_summary_ready')[0]
    answer_payload = _event_payloads(response.text, 'answer_done')[0]

    assert answer_payload['trace_summary'] == trace_summary_payload['trace_summary']
    assert set(answer_payload['trace_summary']['compact']) == {
        'question_understanding',
        'key_evidence',
        'data_gaps',
        'reasoning_basis',
    }
    assert set(answer_payload['trace_summary']['expanded']) == {
        'detailed_evidence',
        'key_paths',
        'miss_explanations',
        'detailed_reasoning_basis',
    }



def test_instance_qa_stream_prefers_router_anchor_for_attribute_lookup(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.md'
    input_file.write_text(
        """# Test Ontology

## Object Types

### `PoD`
?????PoD
?????
- `pod_id`?PoD ID
- `pod_status`?PoD??

## Link Types
- `PoD HAS PoD`: PoD self relation
""",
        encoding='utf-8',
    )

    import cloud_delivery_ontology_palantir.instance_qa.orchestrator as orch
    from cloud_delivery_ontology_palantir.instance_qa.question_router import AnchorLocator, QuestionRoute

    route = QuestionRoute(
        intent='attribute_lookup',
        anchor_entity='PoD',
        anchor_locator=AnchorLocator(match_type='key_attribute', attribute='pod_id', value='POD-001'),
        target_attributes=['pod_status'],
        reasoning_scope='anchor_only',
        confidence=0.97,
        why='attribute query',
    )

    def fake_run_typeql_readonly(typeql: str):
        if '$root isa pod;' in typeql and '$root has pod-id "POD-001";' in typeql:
            return ([{'_entity': 'PoD', 'pod_id': 'POD-001', 'pod_status': 'Installing'}], None)
        return ([], None)

    monkeypatch.setattr(orch, 'resolve_question_route', lambda *args, **kwargs: route)
    monkeypatch.setattr(orch, 'validate_question_route', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, 'validate_question_dsl', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, 'validate_fact_query_dsl', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, '_run_typeql_readonly', fake_run_typeql_readonly)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'POD-001的状态是什么？'})

    assert response.status_code == 200
    question_payload = _event_payloads(response.text, 'question_dsl')[0]
    assert question_payload['question_dsl']['anchor']['entity'] == 'PoD'
    assert question_payload['question_dsl']['anchor']['identifier'] == {'attribute': 'pod_id', 'value': 'POD-001'}
    assert question_payload['question_dsl']['reasoning_scope'] == 'anchor_only'

    planned_payload = _event_payloads(response.text, 'fact_query_planned')[0]
    assert [item['purpose'] for item in planned_payload['fact_queries']] == ['resolve_anchor']

    typedb_payload = _event_payloads(response.text, 'typedb_result')[0]
    assert typedb_payload['fact_pack']['counts'] == {'PoD': 1}




def test_instance_qa_stream_attribute_lookup_schema_trace_stays_on_anchor_only(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.md'
    input_file.write_text(
        """# Test Ontology

## Object Types

### `PoD`
????: PoD
????:
- `pod_id`: PoD ID
- `pod_status`: PoD status

## Link Types
- `PoD HAS PoD`: PoD self relation
""",
        encoding='utf-8',
    )

    import cloud_delivery_ontology_palantir.instance_qa.orchestrator as orch
    from cloud_delivery_ontology_palantir.instance_qa.question_router import AnchorLocator, QuestionRoute

    route = QuestionRoute(
        intent='attribute_lookup',
        anchor_entity='PoD',
        anchor_locator=AnchorLocator(match_type='key_attribute', attribute='pod_id', value='POD-001'),
        target_attributes=['pod_status'],
        reasoning_scope='anchor_only',
        confidence=0.97,
        why='attribute query',
    )

    def fake_run_typeql_readonly(typeql: str):
        if '$root isa pod;' in typeql and '$root has pod-id "POD-001";' in typeql:
            return ([{'_entity': 'PoD', 'pod_id': 'POD-001', 'pod_status': 'Installing'}], None)
        return ([], None)

    monkeypatch.setattr(orch, 'resolve_question_route', lambda *args, **kwargs: route)
    monkeypatch.setattr(orch, 'validate_question_route', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, 'validate_question_dsl', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, 'validate_fact_query_dsl', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, '_run_typeql_readonly', fake_run_typeql_readonly)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'POD-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f'})

    assert response.status_code == 200
    trace_anchor = _event_payloads(response.text, 'trace_anchor')
    trace_expand = _event_payloads(response.text, 'trace_expand')
    evidence_final = _event_payloads(response.text, 'evidence_final')[0]

    assert trace_anchor
    assert trace_anchor[0]['node_ids'] == ['object_type:PoD']
    assert trace_expand == []
    assert evidence_final['search_trace']['expansion_steps'] == []



def test_instance_qa_stream_emits_clean_schema_trace_messages(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'Room WorkAssignment relation'})

    assert response.status_code == 200
    anchor_payload = _event_payloads(response.text, 'trace_anchor')[0]
    final_payload = _event_payloads(response.text, 'evidence_final')[0]
    expand_payloads = _event_payloads(response.text, 'trace_expand')

    assert anchor_payload['message'] == '\u5df2\u8bc6\u522b\u951a\u70b9\u5b9e\u4f53'
    assert final_payload['message'] == '\u5df2\u5b8c\u6210\u672c\u4f53\u68c0\u7d22\u5b9a\u4f4d'
    assert all('\u6269\u5c55\u5230' in payload['message'] for payload in expand_payloads)
    assert '?' not in anchor_payload['message']
    assert '?' not in final_payload['message']


def test_instance_qa_stream_anchor_only_trace_message_is_clean(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.md'
    input_file.write_text(
        """# Test Ontology

## Object Types

### `PoD`
\u4e2d\u6587\u91ca\u4e49\uff1aPoD\n\u5173\u952e\u5c5e\u6027:
- `pod_id`: PoD ID
- `pod_status`: PoD status

## Link Types
- `PoD HAS PoD`: PoD self relation
""",
        encoding='utf-8',
    )

    import cloud_delivery_ontology_palantir.instance_qa.orchestrator as orch
    from cloud_delivery_ontology_palantir.instance_qa.question_router import AnchorLocator, QuestionRoute

    route = QuestionRoute(
        intent='attribute_lookup',
        anchor_entity='PoD',
        anchor_locator=AnchorLocator(match_type='key_attribute', attribute='pod_id', value='POD-001'),
        target_attributes=['pod_status'],
        reasoning_scope='anchor_only',
        confidence=0.97,
        why='attribute query',
    )

    def fake_run_typeql_readonly(typeql: str):
        if '$root isa pod;' in typeql and '$root has pod-id "POD-001";' in typeql:
            return ([{'_entity': 'PoD', 'pod_id': 'POD-001', 'pod_status': 'Installing'}], None)
        return ([], None)

    monkeypatch.setattr(orch, 'resolve_question_route', lambda *args, **kwargs: route)
    monkeypatch.setattr(orch, 'validate_question_route', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, 'validate_question_dsl', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, 'validate_fact_query_dsl', lambda *args, **kwargs: None)
    monkeypatch.setattr(orch, '_run_typeql_readonly', fake_run_typeql_readonly)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'POD-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f'})

    assert response.status_code == 200
    anchor_payload = _event_payloads(response.text, 'trace_anchor')[0]
    assert anchor_payload['message'] == '\u5df2\u8bc6\u522b\u951a\u70b9\u5b9e\u4f53'
    assert '?' not in anchor_payload['message']

