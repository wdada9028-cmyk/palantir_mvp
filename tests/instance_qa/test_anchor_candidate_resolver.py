from cloud_delivery_ontology_palantir.instance_qa.anchor_candidate_resolver import resolve_anchor_candidates
from cloud_delivery_ontology_palantir.instance_qa.anchor_locator_registry import build_anchor_locator_registry
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaEntity, SchemaRegistry


def _schema_registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            'PoD': SchemaEntity(
                name='PoD',
                object_id='object_type:PoD',
                attributes=['pod_id', 'pod_code', 'pod_status'],
                key_attributes=['pod_id'],
            ),
            'Project': SchemaEntity(
                name='Project',
                object_id='object_type:Project',
                attributes=['project_id', 'project_name'],
                key_attributes=['project_id'],
            ),
            'Room': SchemaEntity(
                name='Room',
                object_id='object_type:Room',
                attributes=['room_id', 'room_name'],
                key_attributes=['room_id'],
            ),
        },
        relations=[],
        adjacency={'PoD': [], 'Project': [], 'Room': []},
    )


def test_build_anchor_locator_registry_uses_entity_specific_lookup_fields():
    registry = build_anchor_locator_registry(_schema_registry())

    assert registry['PoD'].lookup_attributes == ('pod_id', 'pod_code')
    assert registry['Project'].lookup_attributes == ('project_id', 'project_name')
    assert registry['Room'].lookup_attributes == ('room_id', 'room_name')


def test_resolve_anchor_candidates_exact_raw_match_wins():
    registry = build_anchor_locator_registry(_schema_registry())
    result = resolve_anchor_candidates(
        raw_anchor_text='POD-001',
        locator_registry=registry,
        candidate_rows_by_entity={
            'PoD': [
                {'pod_id': 'POD-001', 'pod_code': 'CAB-01'},
                {'pod_id': 'POD-002', 'pod_code': 'CAB-02'},
            ],
            'Project': [{'project_id': 'PJT-001', 'project_name': 'POD rollout'}],
        },
    )

    assert result.match_stage == 'exact'
    assert result.selected is not None
    assert result.selected.entity == 'PoD'
    assert result.selected.attribute == 'pod_id'
    assert result.selected.value == 'POD-001'
    assert len(result.candidates) == 1


def test_resolve_anchor_candidates_light_normalized_unique_match_wins():
    registry = build_anchor_locator_registry(_schema_registry())
    result = resolve_anchor_candidates(
        raw_anchor_text='pod-001',
        locator_registry=registry,
        candidate_rows_by_entity={
            'PoD': [{'pod_id': 'POD-001', 'pod_code': 'CAB-01'}],
        },
    )

    assert result.match_stage == 'light'
    assert result.selected is not None
    assert result.selected.entity == 'PoD'
    assert result.selected.attribute == 'pod_id'
    assert result.selected.value == 'POD-001'


def test_resolve_anchor_candidates_loose_match_stays_ambiguous():
    registry = build_anchor_locator_registry(_schema_registry())
    result = resolve_anchor_candidates(
        raw_anchor_text='pod001',
        locator_registry=registry,
        candidate_rows_by_entity={
            'PoD': [
                {'pod_id': 'POD-001', 'pod_code': 'CAB-01'},
                {'pod_id': 'POD 001', 'pod_code': 'CAB-02'},
            ],
        },
    )

    assert result.match_stage == 'loose'
    assert result.selected is None
    assert [candidate.value for candidate in result.candidates] == ['POD-001', 'POD 001']
