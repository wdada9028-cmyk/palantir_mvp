from cloud_delivery_ontology_palantir.instance_qa.evidence_bundle_builder import build_evidence_bundle
from cloud_delivery_ontology_palantir.instance_qa.evidence_models import EvidenceEdge, InstanceEvidence
from cloud_delivery_ontology_palantir.instance_qa.evidence_subgraph_builder import EvidenceSubgraph
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry


def _registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            'PoDPosition': SchemaEntity(
                name='PoDPosition',
                object_id='object_type:PoDPosition',
                attributes=['position_id', 'position_status'],
                key_attributes=['position_id'],
                zh_label='PoD??',
            ),
            'PoDSchedule': SchemaEntity(
                name='PoDSchedule',
                object_id='object_type:PoDSchedule',
                attributes=['pod_schedule_id'],
                key_attributes=['pod_schedule_id'],
                zh_label='PoD??',
            ),
            'WorkAssignment': SchemaEntity(
                name='WorkAssignment',
                object_id='object_type:WorkAssignment',
                attributes=['assignment_id'],
                key_attributes=['assignment_id'],
                zh_label='????',
            ),
        },
        relations=[],
        adjacency={
            'PoDPosition': [
                SchemaAdjacency(entity='PoDPosition', relation='ASSIGNED_TO', direction='in', neighbor_entity='PoD', typedb_relation='pod-position-assignment'),
                SchemaAdjacency(entity='PoDPosition', relation='OCCURS_AT', direction='in', neighbor_entity='WorkAssignment', typedb_relation='work-assignment-position'),
            ],
            'PoDSchedule': [],
            'WorkAssignment': [],
        },
    )


def test_build_evidence_bundle_separates_positive_and_empty_entities():
    subgraph = EvidenceSubgraph(
        nodes={
            'PoDPosition': [
                InstanceEvidence(
                    entity='PoDPosition',
                    iid='0xpos1',
                    business_keys={'position_id': 'POS-001'},
                    attributes={'position_id': 'POS-001', 'position_status': 'ready'},
                    schema_context=None,
                    paths=[],
                )
            ]
        },
        edges=[
            EvidenceEdge(
                source_entity='Room',
                source_id='L1-A',
                relation='ROOM_POSITION',
                target_entity='PoDPosition',
                target_id='POS-001',
            )
        ],
        paths=['Room(L1-A) --ROOM_POSITION--> PoDPosition(POS-001)'],
    )

    bundle = build_evidence_bundle(
        question='L1-A room outage, what impacts?',
        schema_entities=['PoDPosition', 'PoDSchedule'],
        positive_entities={'PoDPosition'},
        empty_entities={'PoDSchedule': 'schema matched but no instances'},
        unrelated_entities={},
        omitted_entities={},
        subgraph=subgraph,
        registry=_registry(),
    )

    assert bundle.positive_evidence[0].entity == 'PoDPosition'
    assert bundle.positive_evidence[0].instances[0].schema_context is not None
    assert bundle.positive_evidence[0].instances[0].schema_context.key_attributes == ['position_id']
    assert bundle.empty_entities[0].entity == 'PoDSchedule'


def test_build_evidence_bundle_caps_instances_and_tracks_omitted_and_unrelated():
    subgraph = EvidenceSubgraph(
        nodes={
            'PoDPosition': [
                InstanceEvidence(
                    entity='PoDPosition',
                    iid='0xpos1',
                    business_keys={'position_id': 'POS-001'},
                    attributes={'position_id': 'POS-001'},
                    schema_context=None,
                    paths=[],
                ),
                InstanceEvidence(
                    entity='PoDPosition',
                    iid='0xpos2',
                    business_keys={'position_id': 'POS-002'},
                    attributes={'position_id': 'POS-002'},
                    schema_context=None,
                    paths=[],
                ),
            ]
        },
        edges=[],
        paths=[],
    )

    bundle = build_evidence_bundle(
        question='test',
        schema_entities=['PoDPosition', 'WorkAssignment'],
        positive_entities={'PoDPosition'},
        empty_entities={},
        unrelated_entities={'WorkAssignment': 'instances exist but unrelated'},
        omitted_entities={},
        subgraph=subgraph,
        registry=_registry(),
        max_instances_per_entity=1,
    )

    assert len(bundle.positive_evidence[0].instances) == 1
    assert bundle.omitted_entities[0].entity == 'PoDPosition'
    assert bundle.omitted_entities[0].omitted_count == 1
    assert bundle.unrelated_entities[0].entity == 'WorkAssignment'


def test_build_evidence_bundle_binds_paths_per_instance_not_per_entity():
    subgraph = EvidenceSubgraph(
        nodes={
            'PoDPosition': [
                InstanceEvidence(
                    entity='PoDPosition',
                    iid='0xpos1',
                    business_keys={'position_id': 'POS-001'},
                    attributes={'position_id': 'POS-001'},
                    schema_context=None,
                    paths=[],
                ),
                InstanceEvidence(
                    entity='PoDPosition',
                    iid='0xpos2',
                    business_keys={'position_id': 'POS-002'},
                    attributes={'position_id': 'POS-002'},
                    schema_context=None,
                    paths=[],
                ),
            ]
        },
        edges=[],
        paths=[
            'Room(L1-A) --ROOM_POSITION--> PoDPosition(POS-001)',
            'Room(L1-A) --ROOM_POSITION--> PoDPosition(POS-002)',
        ],
    )

    bundle = build_evidence_bundle(
        question='test',
        schema_entities=['PoDPosition'],
        positive_entities={'PoDPosition'},
        empty_entities={},
        unrelated_entities={},
        omitted_entities={},
        subgraph=subgraph,
        registry=_registry(),
    )

    first, second = bundle.positive_evidence[0].instances
    assert first.paths == ['Room(L1-A) --ROOM_POSITION--> PoDPosition(POS-001)']
    assert second.paths == ['Room(L1-A) --ROOM_POSITION--> PoDPosition(POS-002)']


def test_build_evidence_bundle_classifies_excluded_positive_entities_explicitly():
    subgraph = EvidenceSubgraph(
        nodes={
            'PoDPosition': [
                InstanceEvidence(
                    entity='PoDPosition',
                    iid='0xpos1',
                    business_keys={'position_id': 'POS-001'},
                    attributes={'position_id': 'POS-001'},
                    schema_context=None,
                    paths=[],
                )
            ],
            'WorkAssignment': [
                InstanceEvidence(
                    entity='WorkAssignment',
                    iid='0xwa1',
                    business_keys={'assignment_id': 'WA-001'},
                    attributes={'assignment_id': 'WA-001'},
                    schema_context=None,
                    paths=[],
                )
            ],
        },
        edges=[],
        paths=[],
    )

    bundle = build_evidence_bundle(
        question='test',
        schema_entities=['PoDPosition', 'WorkAssignment'],
        positive_entities={'PoDPosition'},
        empty_entities={},
        unrelated_entities={},
        omitted_entities={},
        subgraph=subgraph,
        registry=_registry(),
    )

    assert [group.entity for group in bundle.positive_evidence] == ['PoDPosition']
    assert bundle.unrelated_entities[0].entity == 'WorkAssignment'
    assert 'excluded by positive_entities filter' in bundle.unrelated_entities[0].reason
