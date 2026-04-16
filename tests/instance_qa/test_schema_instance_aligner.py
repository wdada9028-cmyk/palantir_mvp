from cloud_delivery_ontology_palantir.instance_qa.schema_instance_aligner import align_schema_context
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry


def _registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            'Floor': SchemaEntity(
                name='Floor',
                object_id='object_type:Floor',
                attributes=['floor_id', 'floor_no', 'install_sequence'],
                key_attributes=['floor_id'],
                zh_label='??',
            ),
            'Room': SchemaEntity(
                name='Room',
                object_id='object_type:Room',
                attributes=['room_id'],
                key_attributes=['room_id'],
                zh_label='??',
            ),
            'RoomMilestone': SchemaEntity(
                name='RoomMilestone',
                object_id='object_type:RoomMilestone',
                attributes=['milestone_id'],
                key_attributes=['milestone_id'],
            ),
        },
        relations=[],
        adjacency={
            'Floor': [
                SchemaAdjacency(entity='Floor', relation='HAS', direction='out', neighbor_entity='Room', typedb_relation='floor-room'),
                SchemaAdjacency(entity='Floor', relation='CONSTRAINS', direction='out', neighbor_entity='RoomMilestone', typedb_relation='floor-milestone-constraint'),
            ],
            'Room': [],
            'RoomMilestone': [],
        },
    )


def test_align_schema_context_returns_minimal_fragment_for_matched_entity():
    aligned = align_schema_context(
        entity='Floor',
        registry=_registry(),
        relevant_relations=['floor-room'],
    )

    assert aligned.entity_name == 'Floor'
    assert aligned.entity_zh == '??'
    assert aligned.key_attributes == ['floor_id']
    assert aligned.relevant_relations == ['floor-room']


def test_align_schema_context_supports_semantic_relation_filter_and_omits_unmatched():
    aligned = align_schema_context(
        entity='Floor',
        registry=_registry(),
        relevant_relations=['HAS', 'UNKNOWN_REL'],
    )

    assert aligned.relevant_relations == ['HAS']


def test_align_schema_context_defaults_to_minimal_semantic_relations_when_not_requested():
    aligned = align_schema_context(
        entity='Floor',
        registry=_registry(),
        relevant_relations=None,
    )

    assert aligned.relevant_relations == ['HAS', 'CONSTRAINS']
