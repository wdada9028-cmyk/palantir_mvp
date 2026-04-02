from cloud_delivery_ontology_palantir.instance_qa.fact_query_planner import build_fact_queries
from cloud_delivery_ontology_palantir.instance_qa.question_models import AnchorRef, ConstraintRef, GoalRef, IdentifierRef, QuestionDSL, ScenarioRef
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry


def _schema_registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            'Room': SchemaEntity(name='Room', object_id='object_type:Room', attributes=['room_id', 'room_status'], key_attributes=['room_id']),
            'WorkAssignment': SchemaEntity(name='WorkAssignment', object_id='object_type:WorkAssignment', attributes=['assignment_id', 'assignment_status'], key_attributes=['assignment_id']),
            'PoD': SchemaEntity(name='PoD', object_id='object_type:PoD', attributes=['pod_id', 'pod_status'], key_attributes=['pod_id']),
        },
        relations=[],
        adjacency={
            'Room': [
                SchemaAdjacency(entity='Room', relation='OCCURS_IN', direction='in', neighbor_entity='WorkAssignment'),
                SchemaAdjacency(entity='Room', relation='ASSIGNED_TO', direction='in', neighbor_entity='PoD'),
            ],
            'WorkAssignment': [],
            'PoD': [],
        },
    )


def _question(event_type: str = 'power_outage') -> QuestionDSL:
    return QuestionDSL(
        mode='impact_analysis',
        anchor=AnchorRef(entity='Room', identifier=IdentifierRef(attribute='room_id', value='01'), surface='room-01'),
        scenario=ScenarioRef(event_type=event_type, duration=None, start_time=None, severity=None, raw_event='event'),
        goal=GoalRef(type='list_impacts', target_entity=None, target_metric=None, deadline=None),
        constraints=ConstraintRef(statuses=[], time_window=None, limit=20),
    )


def test_build_fact_queries_creates_anchor_and_neighbor_queries_for_room_power_outage():
    queries = build_fact_queries(_question('power_outage'), _schema_registry())

    purposes = [item.purpose for item in queries]
    assert 'resolve_anchor' in purposes
    assert 'collect_neighbors' in purposes

    anchor_query = next(item for item in queries if item.purpose == 'resolve_anchor')
    assert anchor_query.root.entity == 'Room'
    assert anchor_query.root.identifier.attribute == 'room_id'
    assert anchor_query.root.identifier.value == '01'

    neighbor_query = next(item for item in queries if item.purpose == 'collect_neighbors')
    assert neighbor_query.traversals
    assert all(step.from_entity == 'Room' for step in neighbor_query.traversals)


def test_build_fact_queries_uses_generic_fallback_when_event_profile_missing():
    queries = build_fact_queries(_question('unknown_event_type'), _schema_registry())

    assert queries
    neighbor_query = next(item for item in queries if item.purpose == 'collect_neighbors')
    assert neighbor_query.traversals
    assert neighbor_query.traversals[0].relation == 'OCCURS_IN'
