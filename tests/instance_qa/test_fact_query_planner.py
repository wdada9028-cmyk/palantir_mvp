from cloud_delivery_ontology_palantir.instance_qa.fact_query_planner import build_fact_queries, build_propagation_queries
from cloud_delivery_ontology_palantir.instance_qa.question_models import AnchorRef, ConstraintRef, GoalRef, IdentifierRef, QuestionDSL, ScenarioRef
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry


def _schema_registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            'Room': SchemaEntity(name='Room', object_id='object_type:Room', attributes=['room_id', 'room_status'], key_attributes=['room_id']),
            'PoDPosition': SchemaEntity(name='PoDPosition', object_id='object_type:PoDPosition', attributes=['position_id', 'position_status'], key_attributes=['position_id']),
            'WorkAssignment': SchemaEntity(name='WorkAssignment', object_id='object_type:WorkAssignment', attributes=['assignment_id', 'assignment_status'], key_attributes=['assignment_id']),
            'PoD': SchemaEntity(name='PoD', object_id='object_type:PoD', attributes=['pod_id', 'pod_status'], key_attributes=['pod_id']),
            'ActivityInstance': SchemaEntity(name='ActivityInstance', object_id='object_type:ActivityInstance', attributes=['activity_id'], key_attributes=['activity_id']),
            'PoDSchedule': SchemaEntity(name='PoDSchedule', object_id='object_type:PoDSchedule', attributes=['pod_schedule_id'], key_attributes=['pod_schedule_id']),
        },
        relations=[],
        adjacency={
            'Room': [
                SchemaAdjacency(entity='Room', relation='OCCURS_IN', direction='in', neighbor_entity='WorkAssignment', typedb_relation='work-assignment-room', entity_role='assigned-room', neighbor_role='assignment-record'),
                SchemaAdjacency(entity='Room', relation='ASSIGNED_TO', direction='in', neighbor_entity='PoD', typedb_relation='pod-room-assignment', entity_role='assigned-room', neighbor_role='assigned-pod'),
                SchemaAdjacency(entity='Room', relation='HAS', direction='out', neighbor_entity='PoDPosition', typedb_relation='room-position', entity_role='owner-room', neighbor_role='owned-position'),
            ],
            'PoDPosition': [
                SchemaAdjacency(entity='PoDPosition', relation='HAS', direction='in', neighbor_entity='Room', typedb_relation='room-position', entity_role='owned-position', neighbor_role='owner-room'),
                SchemaAdjacency(entity='PoDPosition', relation='ASSIGNED_TO', direction='in', neighbor_entity='PoD', typedb_relation='pod-position-assignment', entity_role='assigned-position', neighbor_role='assigned-pod'),
                SchemaAdjacency(entity='PoDPosition', relation='OCCURS_AT', direction='in', neighbor_entity='WorkAssignment', typedb_relation='work-assignment-position', entity_role='assigned-position', neighbor_role='assignment-record'),
            ],
            'WorkAssignment': [
                SchemaAdjacency(entity='WorkAssignment', relation='OCCURS_IN', direction='out', neighbor_entity='Room', typedb_relation='work-assignment-room', entity_role='assignment-record', neighbor_role='assigned-room'),
                SchemaAdjacency(entity='WorkAssignment', relation='OCCURS_AT', direction='out', neighbor_entity='PoDPosition', typedb_relation='work-assignment-position', entity_role='assignment-record', neighbor_role='assigned-position'),
                SchemaAdjacency(entity='WorkAssignment', relation='ASSIGNS', direction='out', neighbor_entity='PoD', typedb_relation='work-assignment-pod', entity_role='assignment-record', neighbor_role='assigned-pod'),
            ],
            'PoD': [
                SchemaAdjacency(entity='PoD', relation='ASSIGNED_TO', direction='out', neighbor_entity='PoDPosition', typedb_relation='pod-position-assignment', entity_role='assigned-pod', neighbor_role='assigned-position'),
                SchemaAdjacency(entity='PoD', relation='HAS', direction='out', neighbor_entity='ActivityInstance', typedb_relation='pod-activity', entity_role='owning-pod', neighbor_role='owned-activity'),
                SchemaAdjacency(entity='PoD', relation='APPLIES_TO', direction='in', neighbor_entity='PoDSchedule', typedb_relation='pod-schedule-pod', entity_role='scheduled-pod', neighbor_role='owning-schedule'),
            ],
            'ActivityInstance': [],
            'PoDSchedule': [],
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


def test_build_fact_queries_keeps_neighbor_adjacency_as_parallel_queries():
    queries = build_fact_queries(_question('power_outage'), _schema_registry())

    anchor_query = next(item for item in queries if item.purpose == 'resolve_anchor')
    assert anchor_query.root.entity == 'Room'
    assert anchor_query.root.identifier.attribute == 'room_id'
    assert anchor_query.root.identifier.value == '01'

    neighbor_queries = [item for item in queries if item.purpose == 'collect_neighbors']
    assert len(neighbor_queries) == 3
    assert all(len(item.traversals) == 1 for item in neighbor_queries)

    relation_set = {item.traversals[0].relation for item in neighbor_queries}
    assert relation_set == {'OCCURS_IN', 'ASSIGNED_TO', 'HAS'}

    occurs_in_query = next(item for item in neighbor_queries if item.traversals[0].relation == 'OCCURS_IN')
    assert occurs_in_query.traversals[0].typedb_relation == 'work-assignment-room'
    assert occurs_in_query.traversals[0].entity_role == 'assigned-room'
    assert occurs_in_query.traversals[0].neighbor_role == 'assignment-record'


def test_build_fact_queries_uses_generic_fallback_when_event_profile_missing():
    queries = build_fact_queries(_question('unknown_event_type'), _schema_registry())

    neighbor_queries = [item for item in queries if item.purpose == 'collect_neighbors']
    assert neighbor_queries
    assert neighbor_queries[0].traversals[0].relation == 'OCCURS_IN'


def test_build_propagation_queries_bridge_from_pod_position_to_pod_and_work_assignment():
    queries = build_propagation_queries(
        _question('power_outage'),
        _schema_registry(),
        {'PoDPosition': {'POS-001'}},
    )

    propagation = [item for item in queries if item.purpose == 'propagate_neighbors']
    relations = {(item.root.entity, item.root.identifier.value, item.traversals[0].relation, item.traversals[0].to_entity) for item in propagation}

    assert relations == {
        ('PoDPosition', 'POS-001', 'ASSIGNED_TO', 'PoD'),
        ('PoDPosition', 'POS-001', 'OCCURS_AT', 'WorkAssignment'),
    }
