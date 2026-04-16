from cloud_delivery_ontology_palantir.instance_qa.fact_query_models import (
    FactQueryDSL,
    FactQueryFilter,
    FactQueryRoot,
    FactQueryTraversal,
)
from cloud_delivery_ontology_palantir.instance_qa.question_models import IdentifierRef
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry
from cloud_delivery_ontology_palantir.instance_qa.fact_query_validator import validate_fact_query_dsl


def _schema_registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            'Room': SchemaEntity(name='Room', object_id='object_type:Room', attributes=['room_id', 'room_status'], key_attributes=['room_id']),
            'WorkAssignment': SchemaEntity(name='WorkAssignment', object_id='object_type:WorkAssignment', attributes=['assignment_id', 'assignment_status'], key_attributes=['assignment_id']),
        },
        relations=[],
        adjacency={
            'Room': [
                SchemaAdjacency(entity='Room', relation='OCCURS_IN', direction='in', neighbor_entity='WorkAssignment'),
            ],
            'WorkAssignment': [
                SchemaAdjacency(entity='WorkAssignment', relation='OCCURS_IN', direction='out', neighbor_entity='Room'),
            ],
        },
    )


def test_validate_fact_query_dsl_accepts_valid_anchor_query():
    query = FactQueryDSL(
        purpose='resolve_anchor',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01')),
        projection={'Room': ['room_id', 'room_status']},
        limit=20,
    )

    assert validate_fact_query_dsl(query, _schema_registry()) is None


def test_validate_fact_query_dsl_rejects_invalid_traversal_compatibility():
    query = FactQueryDSL(
        purpose='collect_neighbors',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01')),
        traversals=[
            FactQueryTraversal(
                from_entity='Room',
                relation='ASSIGNS',
                direction='in',
                to_entity='WorkAssignment',
            )
        ],
        projection={'Room': ['room_id'], 'WorkAssignment': ['assignment_id']},
        limit=20,
    )

    error = validate_fact_query_dsl(query, _schema_registry())

    assert error is not None
    assert 'ASSIGNS' in error


def test_validate_fact_query_dsl_rejects_non_positive_limit():
    query = FactQueryDSL(
        purpose='resolve_anchor',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01')),
        projection={'Room': ['room_id']},
        limit=0,
    )

    error = validate_fact_query_dsl(query, _schema_registry())

    assert error is not None
    assert 'limit' in error.lower()


def test_validate_fact_query_dsl_rejects_unsupported_aggregate():
    query = FactQueryDSL(
        purpose='resolve_anchor',
        root=FactQueryRoot(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01')),
        projection={'Room': ['room_id']},
        aggregate='sum',
        limit=10,
    )

    error = validate_fact_query_dsl(query, _schema_registry())

    assert error is not None
    assert 'aggregate' in error.lower()
