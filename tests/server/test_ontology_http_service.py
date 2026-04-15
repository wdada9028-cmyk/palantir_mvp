import json
from types import SimpleNamespace

from cloud_delivery_ontology_palantir.search.ontology_query_models import OntologyEvidenceBundle, SearchTrace
from cloud_delivery_ontology_palantir.server.ontology_http_service import _build_schema_trace_events


def _payloads(events):
    result = []
    for text in events:
        lines = [line for line in text.splitlines() if line.strip()]
        name = lines[0].split(': ', 1)[1]
        data = json.loads(lines[1][len('data: '):])
        result.append((name, data))
    return result


def test_build_schema_trace_events_uses_instance_evidence_entities_for_expand_graph():
    result = SimpleNamespace(
        blocked_before_retrieval=False,
        question_dsl=SimpleNamespace(anchor=SimpleNamespace(entity='Room'), reasoning_scope='expand_graph'),
        fact_pack={
            'instances': {
                'Room': [{'room_id': 'L1-A'}],
                'Floor': [{'floor_id': 'L1'}],
                'RoomMilestone': [{'milestone_id': 'RM-L1-A-001'}],
                'PoD': [{'pod_id': 'POD-001'}],
                'ActivityInstance': [{'activity_id': 'ACT-001'}],
            },
            'metadata': {'anchor': {'entity': 'Room', 'id': 'L1-A'}},
        },
        reasoning={
            'affected_entities': [
                {'entity': 'Floor', 'id': 'L1', 'depth': 1},
                {'entity': 'RoomMilestone', 'id': 'RM-L1-A-001', 'depth': 1},
                {'entity': 'PoD', 'id': 'POD-001', 'depth': 2},
                {'entity': 'ActivityInstance', 'id': 'ACT-001', 'depth': 2},
            ],
            'impact_summary': {
                'direct_counts': {'Floor': 1, 'RoomMilestone': 1},
                'propagated_counts': {'PoD': 1, 'ActivityInstance': 1},
            },
        },
        evidence_bundle=SimpleNamespace(positive_evidence=[]),
        schema_retrieval_bundle=OntologyEvidenceBundle(
            question='L1-A\u673a\u623f\u65ad\u7535\u4e00\u5468\uff0c\u4f1a\u6709\u54ea\u4e9b\u5f71\u54cd\uff1f',
            seed_node_ids=['object_type:Room'],
            matched_node_ids=['object_type:Room'],
            matched_edge_ids=[],
            highlight_steps=[],
            evidence_chain=[],
            insufficient_evidence=False,
            search_trace=SearchTrace(seed_node_ids=['object_type:Room']),
            display_name_map={
                'object_type:Room': '\u673a\u623f(Room)',
                'object_type:Floor': '\u697c\u5c42(Floor)',
                'object_type:RoomMilestone': '\u673a\u623f\u91cc\u7a0b\u7891(RoomMilestone)',
                'object_type:PoD': 'PoD(PoD)',
                'object_type:ActivityInstance': '\u6d3b\u52a8\u5b9e\u4f8b(ActivityInstance)',
            },
            relation_name_map={},
        ),
    )

    events, _ = _build_schema_trace_events(result, session_id='s1', start_step=2)
    payloads = _payloads(events)

    assert [name for name, _ in payloads] == [
        'trace_anchor',
        'trace_expand',
        'trace_expand',
        'trace_expand',
        'trace_expand',
        'trace_expand',
        'trace_expand',
        'evidence_final',
    ]
    assert payloads[0][1]['message'] == '\u5df2\u5b9a\u4f4d\u8d77\u70b9\u5b9e\u4f53\uff1a\u673a\u623f'
    assert payloads[0][1]['delay_ms'] == 600
    assert payloads[1][1]['message'] == '\u6b63\u5728\u5c55\u5f00\u76f4\u63a5\u5f71\u54cd\u5b9e\u4f53'
    assert payloads[1][1]['delay_ms'] == 600
    assert payloads[2][1]['message'] == '\u76f4\u63a5\u5f71\u54cd\u5b9e\u4f53\uff1a\u697c\u5c42'
    assert payloads[2][1]['delay_ms'] == 600
    assert payloads[3][1]['message'] == '\u76f4\u63a5\u5f71\u54cd\u5b9e\u4f53\uff1a\u673a\u623f\u91cc\u7a0b\u7891'
    assert payloads[4][1]['message'] == '\u6b63\u5728\u5c55\u5f00\u4f20\u64ad\u5f71\u54cd\u5b9e\u4f53'
    assert payloads[4][1]['delay_ms'] == 600
    assert payloads[5][1]['message'] == '\u4f20\u64ad\u5f71\u54cd\u5b9e\u4f53\uff1aPoD'
    assert payloads[6][1]['message'] == '\u4f20\u64ad\u5f71\u54cd\u5b9e\u4f53\uff1a\u6d3b\u52a8\u5b9e\u4f8b'
    assert payloads[6][1]['snapshot_node_ids'] == [
        'object_type:Room',
        'object_type:Floor',
        'object_type:RoomMilestone',
        'object_type:PoD',
        'object_type:ActivityInstance',
    ]
    assert payloads[7][1]['message'] == '\u5df2\u5b8c\u6210\u5f71\u54cd\u8303\u56f4\u5b9a\u4f4d'
    assert payloads[7][1]['evidence_chain'][0]['message'] == '\u5df2\u5b9a\u4f4d\u8d77\u70b9\u5b9e\u4f53\uff1a\u673a\u623f'
    assert payloads[7][1]['evidence_chain'][-1]['message'] == '\u4f20\u64ad\u5f71\u54cd\u5b9e\u4f53\uff1a\u6d3b\u52a8\u5b9e\u4f8b'


def test_build_schema_trace_events_falls_back_to_schema_trace_when_no_instance_evidence():
    result = SimpleNamespace(
        blocked_before_retrieval=False,
        question_dsl=SimpleNamespace(anchor=SimpleNamespace(entity='Room'), reasoning_scope='expand_graph'),
        fact_pack={'instances': {}, 'metadata': {'anchor': {'entity': 'Room', 'id': 'L1-A'}}},
        reasoning={'affected_entities': [], 'impact_summary': {'direct_counts': {}, 'propagated_counts': {}}},
        evidence_bundle=SimpleNamespace(positive_evidence=[]),
        schema_retrieval_bundle=OntologyEvidenceBundle(
            question='Room WorkAssignment relation',
            seed_node_ids=['object_type:Room'],
            matched_node_ids=['object_type:Room', 'object_type:WorkAssignment'],
            matched_edge_ids=['edge:1'],
            highlight_steps=[],
            evidence_chain=[],
            insufficient_evidence=False,
            search_trace=SearchTrace(
                seed_node_ids=['object_type:Room'],
                expansion_steps=[],
            ),
            display_name_map={'object_type:Room': '\u673a\u623f(Room)'},
            relation_name_map={},
        ),
    )

    events, _ = _build_schema_trace_events(result, session_id='s1', start_step=2)
    payloads = _payloads(events)

    assert payloads[0][0] == 'trace_anchor'
    assert payloads[0][1]['message'] == '\u5df2\u8bc6\u522b\u951a\u70b9\u5b9e\u4f53'
