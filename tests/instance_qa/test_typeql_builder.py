import pytest

from cloud_delivery_ontology_palantir.instance_qa.fact_query_models import FactQueryDSL, FactQueryFilter, FactQueryRoot, FactQueryTraversal
from cloud_delivery_ontology_palantir.instance_qa.question_models import IdentifierRef
from cloud_delivery_ontology_palantir.instance_qa.typeql_builder import build_typeql_query


def test_build_typeql_query_generates_match_for_anchor_lookup():
    query = FactQueryDSL(
        purpose='resolve_anchor',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01')),
        projection={'Room': ['room_id', 'room_status']},
        limit=20,
    )

    typeql = build_typeql_query(query)

    assert 'match' in typeql
    assert 'room-id "01"' in typeql
    assert 'get' in typeql
    assert 'limit 20' in typeql


def test_build_typeql_query_supports_single_hop_neighbor_traversal():
    query = FactQueryDSL(
        purpose='collect_neighbors',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01')),
        traversals=[
            FactQueryTraversal(
                from_entity='Room',
                relation='OCCURS_IN',
                typedb_relation='work-assignment-room',
                entity_role='assigned-room',
                neighbor_role='assignment-record',
                direction='in',
                to_entity='WorkAssignment',
                required=False,
            )
        ],
        projection={'Room': ['room_id'], 'WorkAssignment': ['assignment_id']},
        limit=10,
    )

    typeql = build_typeql_query(query)

    assert 'work-assignment-room' in typeql
    assert 'assignment-record: $n1' in typeql
    assert 'assigned-room: $root' in typeql


def test_build_typeql_query_rejects_unsupported_filter_ops():
    query = FactQueryDSL(
        purpose='resolve_anchor',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01')),
        filters=[FactQueryFilter(entity='Room', attribute='room_status', op='contains', value='active')],
        projection={'Room': ['room_id']},
        limit=20,
    )

    with pytest.raises(ValueError, match='Unsupported filter op'):
        build_typeql_query(query)


def test_build_typeql_query_rejects_non_root_filters():
    query = FactQueryDSL(
        purpose='collect_neighbors',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01')),
        traversals=[
            FactQueryTraversal(
                from_entity='Room',
                relation='OCCURS_IN',
                typedb_relation='work-assignment-room',
                entity_role='assigned-room',
                neighbor_role='assignment-record',
                direction='in',
                to_entity='WorkAssignment',
                required=False,
            )
        ],
        filters=[FactQueryFilter(entity='WorkAssignment', attribute='assignment_id', op='eq', value='WA-001')],
        projection={'Room': ['room_id'], 'WorkAssignment': ['assignment_id']},
        limit=10,
    )

    with pytest.raises(ValueError, match='Non-root filters are not supported'):
        build_typeql_query(query)



def test_build_typeql_query_preserves_pod_word_boundaries_in_entity_labels():
    query = FactQueryDSL(
        purpose='collect_neighbors',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='L1-A')),
        traversals=[
            FactQueryTraversal(
                from_entity='Room',
                relation='HAS',
                typedb_relation='room-position',
                entity_role='owner-room',
                neighbor_role='owned-position',
                direction='out',
                to_entity='PoDPosition',
                required=False,
            ),
            FactQueryTraversal(
                from_entity='PoDPosition',
                relation='APPLIES_TO',
                typedb_relation='pod-schedule-pod',
                entity_role='scheduled-pod',
                neighbor_role='owning-schedule',
                direction='in',
                to_entity='PoDSchedule',
                required=False,
            ),
        ],
        projection={'Room': ['room_id'], 'PoDPosition': ['position_id'], 'PoDSchedule': ['pod_schedule_id']},
        limit=10,
    )

    typeql = build_typeql_query(query)

    assert '$n1 isa pod-position;' in typeql
    assert '$n2 isa pod-schedule;' in typeql
