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
    assert 'event: evidence_bundle_ready' in text
    assert 'event: llm_answer_context_ready' in text
    assert 'event: reasoning_done' in text
    assert 'event: trace_summary_ready' in text
    assert 'event: answer_done' in text


def test_qa_stream_emits_trace_summary_ready_and_answer_done_contains_trace_summary(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': '01??????????'})

    assert response.status_code == 200

    trace_summary_payload = _event_payloads(response.text, 'trace_summary_ready')[0]
    answer_done_payload = _event_payloads(response.text, 'answer_done')[0]

    assert set(trace_summary_payload['trace_summary']['compact'].keys()) == {
        'question_understanding',
        'key_evidence',
        'data_gaps',
        'reasoning_basis',
    }
    assert set(trace_summary_payload['trace_summary']['expanded'].keys()) == {
        'detailed_evidence',
        'key_paths',
        'miss_explanations',
        'detailed_reasoning_basis',
    }
    assert answer_done_payload['trace_summary'] == trace_summary_payload['trace_summary']
    assert 'trace_report' not in answer_done_payload
    assert 'typeql' not in json.dumps(answer_done_payload['trace_summary'], ensure_ascii=False)


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




def test_qa_stream_emits_evidence_bundle_and_llm_context_payloads(tmp_path: Path, monkeypatch):
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
    response = client.get('/api/qa/stream', params={'q': '01????????????'})

    assert response.status_code == 200

    evidence_payload = _event_payloads(response.text, 'evidence_bundle_ready')[0]
    llm_context_payload = _event_payloads(response.text, 'llm_answer_context_ready')[0]

    evidence_bundle = evidence_payload['evidence_bundle']
    assert evidence_bundle['question']
    assert 'positive_evidence' in evidence_bundle
    assert evidence_bundle['positive_evidence']

    llm_context = llm_context_payload['llm_answer_context']
    assert 'system_prompt' in llm_context
    assert 'user_payload' in llm_context
    assert llm_context['user_payload']['positive_evidence']

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



def test_qa_stream_propagates_room_event_impacts_across_work_assignment_and_pod(tmp_path: Path, monkeypatch):
    tql_file = tmp_path / 'ontology.tql'
    tql_file.write_text(
        """define
attribute room-id, value string;
attribute assignment-id, value string;
attribute pod-id, value string;
attribute activity-id, value string;
attribute pod-schedule-id, value string;
relation work-assignment-room,
  relates assignment-record,
  relates assigned-room;
relation work-assignment-pod,
  relates assignment-record,
  relates assigned-pod;
relation pod-activity,
  relates owning-pod,
  relates owned-activity;
relation pod-schedule-pod,
  relates owning-schedule,
  relates scheduled-pod;
entity room,
  owns room-id @key,
  plays work-assignment-room:assigned-room;
entity work-assignment,
  owns assignment-id @key,
  plays work-assignment-room:assignment-record,
  plays work-assignment-pod:assignment-record;
entity pod,
  owns pod-id @key,
  plays work-assignment-pod:assigned-pod,
  plays pod-activity:owning-pod,
  plays pod-schedule-pod:scheduled-pod;
entity activity-instance,
  owns activity-id @key,
  plays pod-activity:owned-activity;
entity pod-schedule,
  owns pod-schedule-id @key,
  plays pod-schedule-pod:owning-schedule;
""",
        encoding='utf-8',
    )

    import types
    import cloud_delivery_ontology_palantir.instance_qa.orchestrator as orch

    def fake_parse_query(raw_query: str):
        return types.SimpleNamespace(
            raw_query=raw_query,
            normalized_query=raw_query,
            high_confidence_entities=['Room'],
            candidate_entities=[],
        )

    def fake_run_typeql_readonly(typeql: str):
        if 'get $root;' in typeql and '$root isa room;' in typeql:
            return ([{'_entity': 'Room', 'room_id': 'L1-A'}], None)
        if 'isa work-assignment-room' in typeql:
            return ([{
                '_entity': 'WorkAssignment',
                'assignment_id': 'WA-001',
                '_source_entity': 'WorkAssignment',
                '_source_id': 'WA-001',
                '_relation': 'WORK_ASSIGNMENT_ROOM',
                '_target_entity': 'Room',
                '_target_id': 'L1-A',
            }], None)
        if 'isa work-assignment-pod' in typeql:
            return ([{
                '_entity': 'PoD',
                'pod_id': 'POD-001',
                '_source_entity': 'WorkAssignment',
                '_source_id': 'WA-001',
                '_relation': 'WORK_ASSIGNMENT_POD',
                '_target_entity': 'PoD',
                '_target_id': 'POD-001',
            }], None)
        if 'isa pod-activity' in typeql:
            return ([{
                '_entity': 'ActivityInstance',
                'activity_id': 'ACT-001',
                '_source_entity': 'PoD',
                '_source_id': 'POD-001',
                '_relation': 'POD_ACTIVITY',
                '_target_entity': 'ActivityInstance',
                '_target_id': 'ACT-001',
            }], None)
        if 'isa pod-schedule-pod' in typeql:
            return ([{
                '_entity': 'PoDSchedule',
                'pod_schedule_id': 'SCH-001',
                '_source_entity': 'PoDSchedule',
                '_source_id': 'SCH-001',
                '_relation': 'POD_SCHEDULE_POD',
                '_target_entity': 'PoD',
                '_target_id': 'POD-001',
            }], None)
        return ([], None)

    monkeypatch.setattr(orch, 'parse_query', fake_parse_query)
    monkeypatch.setattr(orch, '_run_typeql_readonly', fake_run_typeql_readonly)

    app = create_app(input_file=tql_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'L1-A\u673a\u623f\u65ad\u7535\u4e00\u5468\uff0c\u4f1a\u6709\u54ea\u4e9b\u5f71\u54cd\uff1f'})

    assert response.status_code == 200
    typedb_payload = _event_payloads(response.text, 'typedb_result')[0]
    fact_pack = typedb_payload['fact_pack']
    assert fact_pack['counts']['WorkAssignment'] == 1
    assert fact_pack['counts']['PoD'] == 1
    assert fact_pack['counts']['ActivityInstance'] == 1
    assert fact_pack['counts']['PoDSchedule'] == 1

    reasoning_payload = _event_payloads(response.text, 'reasoning_done')[0]
    assert reasoning_payload['reasoning']['impact_summary']['direct_counts'] == {'WorkAssignment': 1}
    assert reasoning_payload['reasoning']['impact_summary']['propagated_counts'] == {
        'PoD': 1,
        'ActivityInstance': 1,
        'PoDSchedule': 1,
    }

    answer_payload = _event_payloads(response.text, 'answer_done')[0]
    assert '\u5df2\u8bc6\u522b\u4ee5\u4e0b\u6f5c\u5728\u5f71\u54cd\uff1a' in answer_payload['answer']
    assert '\u4f20\u64ad\u5f71\u54cd\uff1aPoD 1 \u4e2a\u3001ActivityInstance 1 \u4e2a\u3001PoDSchedule 1 \u4e2a\u3002' in answer_payload['answer']


def test_qa_stream_propagates_room_event_impacts_via_pod_position_bridge(tmp_path: Path, monkeypatch):
    tql_file = tmp_path / 'ontology.tql'
    tql_file.write_text(
        """define
attribute room-id, value string;
attribute floor-id, value string;
attribute milestone-id, value string;
attribute position-id, value string;
attribute assignment-id, value string;
attribute pod-id, value string;
attribute activity-id, value string;
attribute pod-schedule-id, value string;
relation floor-room,
  relates owning-floor,
  relates room-in-floor;
relation room-milestone-constraint,
  relates constrained-room,
  relates governing-milestone;
relation room-position,
  relates owner-room,
  relates owned-position;
relation work-assignment-position,
  relates assignment-record,
  relates assigned-position;
relation pod-position-assignment,
  relates assigned-pod,
  relates assigned-position;
relation pod-activity,
  relates owning-pod,
  relates owned-activity;
relation pod-schedule-pod,
  relates owning-schedule,
  relates scheduled-pod;
entity room,
  owns room-id @key,
  plays floor-room:room-in-floor,
  plays room-milestone-constraint:constrained-room,
  plays room-position:owner-room;
entity floor,
  owns floor-id @key,
  plays floor-room:owning-floor;
entity room-milestone,
  owns milestone-id @key,
  plays room-milestone-constraint:governing-milestone;
entity pod-position,
  owns position-id @key,
  plays room-position:owned-position,
  plays work-assignment-position:assigned-position,
  plays pod-position-assignment:assigned-position;
entity work-assignment,
  owns assignment-id @key,
  plays work-assignment-position:assignment-record;
entity pod,
  owns pod-id @key,
  plays pod-position-assignment:assigned-pod,
  plays pod-activity:owning-pod,
  plays pod-schedule-pod:scheduled-pod;
entity activity-instance,
  owns activity-id @key,
  plays pod-activity:owned-activity;
entity pod-schedule,
  owns pod-schedule-id @key,
  plays pod-schedule-pod:owning-schedule;
""",
        encoding='utf-8',
    )

    import types
    import cloud_delivery_ontology_palantir.instance_qa.orchestrator as orch

    def fake_parse_query(raw_query: str):
        return types.SimpleNamespace(
            raw_query=raw_query,
            normalized_query=raw_query,
            high_confidence_entities=['Room'],
            candidate_entities=[],
        )

    def fake_run_typeql_readonly(typeql: str):
        if 'get $root;' in typeql and '$root isa room;' in typeql:
            return ([{'_entity': 'Room', 'room_id': 'L1-A'}], None)
        if 'isa floor-room' in typeql:
            return ([{
                '_entity': 'Floor',
                'floor_id': 'F1',
                '_source_entity': 'Floor',
                '_source_id': 'F1',
                '_relation': 'FLOOR_ROOM',
                '_target_entity': 'Room',
                '_target_id': 'L1-A',
            }], None)
        if 'isa room-milestone-constraint' in typeql:
            return ([{
                '_entity': 'RoomMilestone',
                'milestone_id': 'RM-1',
                '_source_entity': 'RoomMilestone',
                '_source_id': 'RM-1',
                '_relation': 'ROOM_MILESTONE_CONSTRAINT',
                '_target_entity': 'Room',
                '_target_id': 'L1-A',
            }], None)
        if 'isa room-position' in typeql:
            return ([
                {
                    '_entity': 'PoDPosition',
                    'position_id': 'POS-001',
                    '_source_entity': 'Room',
                    '_source_id': 'L1-A',
                    '_relation': 'ROOM_POSITION',
                    '_target_entity': 'PoDPosition',
                    '_target_id': 'POS-001',
                },
                {
                    '_entity': 'PoDPosition',
                    'position_id': 'POS-002',
                    '_source_entity': 'Room',
                    '_source_id': 'L1-A',
                    '_relation': 'ROOM_POSITION',
                    '_target_entity': 'PoDPosition',
                    '_target_id': 'POS-002',
                },
            ], None)
        if 'isa pod-position-assignment' in typeql:
            if 'POS-001' in typeql:
                return ([{
                    '_entity': 'PoD',
                    'pod_id': 'POD-001',
                    '_source_entity': 'PoD',
                    '_source_id': 'POD-001',
                    '_relation': 'POD_POSITION_ASSIGNMENT',
                    '_target_entity': 'PoDPosition',
                    '_target_id': 'POS-001',
                }], None)
            if 'POS-002' in typeql:
                return ([{
                    '_entity': 'PoD',
                    'pod_id': 'POD-002',
                    '_source_entity': 'PoD',
                    '_source_id': 'POD-002',
                    '_relation': 'POD_POSITION_ASSIGNMENT',
                    '_target_entity': 'PoDPosition',
                    '_target_id': 'POS-002',
                }], None)
        if 'isa work-assignment-position' in typeql:
            if 'POS-001' in typeql:
                return ([{
                    '_entity': 'WorkAssignment',
                    'assignment_id': 'WA-001',
                    '_source_entity': 'WorkAssignment',
                    '_source_id': 'WA-001',
                    '_relation': 'WORK_ASSIGNMENT_POSITION',
                    '_target_entity': 'PoDPosition',
                    '_target_id': 'POS-001',
                }], None)
            if 'POS-002' in typeql:
                return ([{
                    '_entity': 'WorkAssignment',
                    'assignment_id': 'WA-002',
                    '_source_entity': 'WorkAssignment',
                    '_source_id': 'WA-002',
                    '_relation': 'WORK_ASSIGNMENT_POSITION',
                    '_target_entity': 'PoDPosition',
                    '_target_id': 'POS-002',
                }], None)
        if 'isa pod-activity' in typeql:
            if 'POD-001' in typeql:
                return ([{
                    '_entity': 'ActivityInstance',
                    'activity_id': 'ACT-001',
                    '_source_entity': 'PoD',
                    '_source_id': 'POD-001',
                    '_relation': 'POD_ACTIVITY',
                    '_target_entity': 'ActivityInstance',
                    '_target_id': 'ACT-001',
                }], None)
            if 'POD-002' in typeql:
                return ([{
                    '_entity': 'ActivityInstance',
                    'activity_id': 'ACT-002',
                    '_source_entity': 'PoD',
                    '_source_id': 'POD-002',
                    '_relation': 'POD_ACTIVITY',
                    '_target_entity': 'ActivityInstance',
                    '_target_id': 'ACT-002',
                }], None)
        if 'isa pod-schedule-pod' in typeql:
            if 'POD-001' in typeql:
                return ([{
                    '_entity': 'PoDSchedule',
                    'pod_schedule_id': 'SCH-001',
                    '_source_entity': 'PoDSchedule',
                    '_source_id': 'SCH-001',
                    '_relation': 'POD_SCHEDULE_POD',
                    '_target_entity': 'PoD',
                    '_target_id': 'POD-001',
                }], None)
            if 'POD-002' in typeql:
                return ([{
                    '_entity': 'PoDSchedule',
                    'pod_schedule_id': 'SCH-002',
                    '_source_entity': 'PoDSchedule',
                    '_source_id': 'SCH-002',
                    '_relation': 'POD_SCHEDULE_POD',
                    '_target_entity': 'PoD',
                    '_target_id': 'POD-002',
                }], None)
        return ([], None)

    monkeypatch.setattr(orch, 'parse_query', fake_parse_query)
    monkeypatch.setattr(orch, '_run_typeql_readonly', fake_run_typeql_readonly)

    app = create_app(input_file=tql_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'L1-A\u673a\u623f\u65ad\u7535\u4e00\u5468\uff0c\u4f1a\u6709\u54ea\u4e9b\u5f71\u54cd\uff1f'})

    assert response.status_code == 200
    typedb_payload = _event_payloads(response.text, 'typedb_result')[0]
    fact_pack = typedb_payload['fact_pack']
    assert fact_pack['counts']['PoDPosition'] == 2
    assert fact_pack['counts']['WorkAssignment'] == 2
    assert fact_pack['counts']['PoD'] == 2
    assert fact_pack['counts']['ActivityInstance'] == 2
    assert fact_pack['counts']['PoDSchedule'] == 2

    reasoning_payload = _event_payloads(response.text, 'reasoning_done')[0]
    assert reasoning_payload['reasoning']['impact_summary']['direct_counts'] == {
        'RoomMilestone': 1,
        'Floor': 1,
        'PoDPosition': 2,
    }
    assert reasoning_payload['reasoning']['impact_summary']['propagated_counts'] == {
        'WorkAssignment': 2,
        'PoD': 2,
        'ActivityInstance': 2,
        'PoDSchedule': 2,
    }

    answer_payload = _event_payloads(response.text, 'answer_done')[0]
    assert '\u5df2\u8bc6\u522b\u4ee5\u4e0b\u6f5c\u5728\u5f71\u54cd\uff1a' in answer_payload['answer']
    assert '\u76f4\u63a5\u5f71\u54cd\uff1aRoomMilestone 1 \u4e2a\u3001Floor 1 \u4e2a\u3001PoDPosition 2 \u4e2a\u3002' in answer_payload['answer']
    assert '\u4f20\u64ad\u5f71\u54cd\uff1aWorkAssignment 2 \u4e2a\u3001PoD 2 \u4e2a\u3001ActivityInstance 2 \u4e2a\u3001PoDSchedule 2 \u4e2a\u3002' in answer_payload['answer']
