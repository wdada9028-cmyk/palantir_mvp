from cloud_delivery_ontology_palantir.instance_qa.evidence_models import (
    EmptyEntityEvidence,
    EntityEvidenceGroup,
    EvidenceBundle,
    EvidenceEdge,
    InstanceEvidence,
    OmittedEntityEvidence,
    SchemaContext,
    UnrelatedEntityEvidence,
)


def test_instance_evidence_preserves_full_row_and_iid():
    evidence = InstanceEvidence(
        entity='Floor',
        iid='0x123',
        business_keys={'floor-id': 'L1'},
        attributes={'floor-id': 'L1', 'floor-no': 1, 'install-sequence': 1},
        schema_context=SchemaContext(
            entity_name='Floor',
            entity_zh='??',
            key_attributes=['floor-id'],
            relevant_relations=['floor-room'],
        ),
        paths=['Room(L1-A) <- floor-room - Floor(L1)'],
    )

    assert evidence.iid == '0x123'
    assert evidence.attributes['floor-no'] == 1
    assert 'install-sequence' in evidence.attributes


def test_evidence_bundle_to_dict_is_json_safe_and_complete():
    bundle = EvidenceBundle(
        question='L1-A??????????????',
        understanding={
            'anchor': {'entity': 'Room', 'id': 'L1-A'},
            'normalized_query': 'L1-A??????,??????',
        },
        positive_evidence=[
            EntityEvidenceGroup(
                entity='Floor',
                instances=[
                    InstanceEvidence(
                        entity='Floor',
                        iid='0x123',
                        business_keys={'floor-id': 'L1'},
                        attributes={'floor-id': 'L1', 'floor-no': 1, 'install-sequence': 1},
                        schema_context=SchemaContext(
                            entity_name='Floor',
                            entity_zh='??',
                            key_attributes=['floor-id'],
                            relevant_relations=['floor-room'],
                        ),
                        paths=['Room(L1-A) <- floor-room - Floor(L1)'],
                    )
                ],
            )
        ],
        edges=[
            EvidenceEdge(
                source_entity='Room',
                source_id='L1-A',
                relation='FLOOR_ROOM',
                target_entity='Floor',
                target_id='L1',
            )
        ],
        paths=['Room(L1-A) <- floor-room - Floor(L1)'],
        empty_entities=[
            EmptyEntityEvidence(entity='PoDSchedule', reason='schema???????????')
        ],
        unrelated_entities=[
            UnrelatedEntityEvidence(entity='WorkAssignment', reason='??????????????')
        ],
        omitted_entities=[
            OmittedEntityEvidence(entity='PoDPosition', omitted_count=20, reason='???????')
        ],
    )

    payload = bundle.to_dict()

    assert payload['question'] == 'L1-A??????????????'
    assert payload['positive_evidence'][0]['instances'][0]['attributes']['floor-no'] == 1
    assert payload['edges'][0]['relation'] == 'FLOOR_ROOM'
    assert payload['empty_entities'][0]['entity'] == 'PoDSchedule'
    assert payload['unrelated_entities'][0]['entity'] == 'WorkAssignment'
    assert payload['omitted_entities'][0]['omitted_count'] == 20
