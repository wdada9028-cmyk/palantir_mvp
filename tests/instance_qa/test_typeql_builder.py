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
    assert 'room_id "01"' in typeql
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
                direction='in',
                to_entity='WorkAssignment',
                required=False,
            )
        ],
        projection={'Room': ['room_id'], 'WorkAssignment': ['assignment_id']},
        limit=10,
    )

    typeql = build_typeql_query(query)

    assert 'occurs-in' in typeql
    assert '$n1' in typeql


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
