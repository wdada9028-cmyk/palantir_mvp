from cloud_delivery_ontology_palantir.instance_qa.anchor_candidate_context_builder import build_anchor_candidate_context
from cloud_delivery_ontology_palantir.instance_qa.anchor_candidate_resolver import AnchorCandidate, AnchorResolutionResult
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry


def _schema_registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            'PoD': SchemaEntity(
                name='PoD',
                object_id='object_type:PoD',
                attributes=['pod_id', 'pod_code', 'pod_name', 'pod_model', 'pod_status', 'room_id', 'project_id'],
                key_attributes=['pod_id'],
                zh_label='PoD',
            ),
            'Room': SchemaEntity(
                name='Room',
                object_id='object_type:Room',
                attributes=['room_id', 'room_name', 'room_status'],
                key_attributes=['room_id'],
                zh_label='\u673a\u623f',
            ),
            'Project': SchemaEntity(
                name='Project',
                object_id='object_type:Project',
                attributes=['project_id', 'project_name', 'project_code', 'project_status'],
                key_attributes=['project_id'],
                zh_label='\u9879\u76ee',
            ),
        },
        relations=[],
        adjacency={
            'PoD': [
                SchemaAdjacency(entity='PoD', relation='ASSIGNED_TO', direction='out', neighbor_entity='Room'),
                SchemaAdjacency(entity='PoD', relation='DELIVERS', direction='in', neighbor_entity='Project'),
            ],
            'Room': [],
            'Project': [],
        },
    )


def _pod_resolution_result() -> AnchorResolutionResult:
    row = {
        '_entity': 'PoD',
        'iid': '0x123456',
        'pod_id': 'POD-001',
        'pod_code': 'CAB-001',
        'pod_name': '\u6838\u5fc3\u8bbe\u5907A',
        'pod_model': 'X123',
        'pod_status': 'Installing',
        'room_id': 'L1-A',
        'project_id': 'PRJ-001',
        'unused_field': 'SHOULD_NOT_LEAK',
    }
    candidate = AnchorCandidate(entity='PoD', attribute='pod_id', value='POD-001', source_row=row)
    return AnchorResolutionResult(
        raw_anchor_text='pod-001',
        match_stage='light',
        selected=candidate,
        candidates=[candidate],
    )


def _room_resolution_result() -> AnchorResolutionResult:
    row = {
        '_entity': 'Room',
        'iid': '0xroom',
        'room_id': 'L1-A',
        'room_name': 'L1-A\u673a\u623f',
        'room_status': 'ready',
    }
    candidate = AnchorCandidate(entity='Room', attribute='room_id', value='L1-A', source_row=row)
    return AnchorResolutionResult(
        raw_anchor_text='l1-a',
        match_stage='light',
        selected=candidate,
        candidates=[candidate],
    )


def _project_resolution_result() -> AnchorResolutionResult:
    row = {
        '_entity': 'Project',
        'iid': '0xproject',
        'project_id': 'PRJ-001',
        'project_name': 'L1\u673a\u623f\u4ea4\u4ed8\u9879\u76ee',
        'project_code': 'PJT-L1',
        'project_status': 'active',
    }
    candidate = AnchorCandidate(entity='Project', attribute='project_id', value='PRJ-001', source_row=row)
    return AnchorResolutionResult(
        raw_anchor_text='prj-001',
        match_stage='exact',
        selected=candidate,
        candidates=[candidate],
    )


def test_build_anchor_candidate_context_has_required_shape_without_raw_leakage():
    payload = build_anchor_candidate_context(
        question='POD-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f',
        schema_registry=_schema_registry(),
        resolution=_pod_resolution_result(),
    )

    assert set(payload.keys()) == {'raw_anchor_text', 'question', 'candidate_entity', 'candidates'}
    assert payload['raw_anchor_text'] == 'pod-001'
    assert payload['candidate_entity'] == 'PoD'
    assert isinstance(payload['candidates'], list) and len(payload['candidates']) == 1

    candidate = payload['candidates'][0]
    assert set(candidate.keys()) == {'candidate_id', 'entity', 'locator', 'identity', 'core_attributes', 'business_context'}
    assert candidate['candidate_id'] == 'cand_1'
    assert candidate['entity'] == 'PoD'
    assert candidate['locator'] == {
        'matched_attribute': 'pod_id',
        'matched_value': 'POD-001',
        'match_stage': 'light',
    }
    assert candidate['identity']['primary_id'] == 'POD-001'
    assert candidate['identity']['aliases'] == ['CAB-001', '\u6838\u5fc3\u8bbe\u5907A']

    serialized = str(payload)
    assert 'iid' not in serialized
    assert 'unused_field' not in serialized


def test_status_question_prefers_status_attributes():
    payload = build_anchor_candidate_context(
        question='POD-001\u5f53\u524d\u72b6\u6001\u662f\u4ec0\u4e48\uff1f',
        schema_registry=_schema_registry(),
        resolution=_pod_resolution_result(),
    )

    core = payload['candidates'][0]['core_attributes']
    assert list(core.keys()) == ['pod_status']
    assert core['pod_status'] == 'Installing'


def test_location_question_prioritizes_location_business_context():
    payload = build_anchor_candidate_context(
        question='POD-001\u5728\u54ea\u4e2a\u673a\u623f\uff1f',
        schema_registry=_schema_registry(),
        resolution=_pod_resolution_result(),
    )

    business_context = payload['candidates'][0]['business_context']
    assert business_context
    assert business_context[0]['entity'] == 'Room'
    assert business_context[0]['id'] == 'L1-A'
    assert '\u673a\u623f' in business_context[0]['summary']


def test_model_name_question_prefers_model_name_code_attributes_and_context_cap():
    result = _pod_resolution_result()
    row = dict(result.candidates[0].source_row)
    row['project_id'] = 'PRJ-001'
    row['room_id'] = 'L1-A'
    candidate = AnchorCandidate(entity='PoD', attribute='pod_id', value='POD-001', source_row=row)
    result = AnchorResolutionResult(raw_anchor_text='POD-001', match_stage='exact', selected=candidate, candidates=[candidate])

    payload = build_anchor_candidate_context(
        question='\u578b\u53f7X123\u8fd9\u4e2aPoD\u540d\u79f0\u548c\u7f16\u7801\u662f\u4ec0\u4e48\uff1f',
        schema_registry=_schema_registry(),
        resolution=result,
    )

    core = payload['candidates'][0]['core_attributes']
    assert set(core.keys()) == {'pod_model', 'pod_name', 'pod_code'}
    assert 'pod_status' not in core

    business_context = payload['candidates'][0]['business_context']
    assert len(business_context) <= 4
    assert all('relation' in item and 'entity' in item and 'summary' in item for item in business_context)


def test_room_status_question_supports_chinese_hint():
    payload = build_anchor_candidate_context(
        question='L1-A\u673a\u623f\u72b6\u6001\u662f\u4ec0\u4e48\uff1f',
        schema_registry=_schema_registry(),
        resolution=_room_resolution_result(),
    )

    assert payload['candidate_entity'] == 'Room'
    core = payload['candidates'][0]['core_attributes']
    assert core == {'room_status': 'ready'}


def test_project_name_code_question_supports_chinese_hint():
    payload = build_anchor_candidate_context(
        question='PRJ-001\u9879\u76ee\u540d\u79f0\u548c\u7f16\u7801\u662f\u4ec0\u4e48\uff1f',
        schema_registry=_schema_registry(),
        resolution=_project_resolution_result(),
    )

    assert payload['candidate_entity'] == 'Project'
    core = payload['candidates'][0]['core_attributes']
    assert set(core.keys()) == {'project_name', 'project_code'}
    assert 'project_status' not in core
