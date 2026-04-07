from cloud_delivery_ontology_palantir.instance_qa.evidence_subgraph_builder import build_evidence_subgraph


def test_build_evidence_subgraph_keeps_full_attributes_and_edges():
    fact_pack = {
        'instances': {
            'Room': [{'iid': '0xroom', 'room_id': 'L1-A'}],
            'PoDPosition': [{'iid': '0xpos1', 'position_id': 'POS-001', 'position_status': 'ready'}],
        },
        'links': [
            {
                'source_entity': 'Room',
                'source_id': 'L1-A',
                'relation': 'ROOM_POSITION',
                'target_entity': 'PoDPosition',
                'target_id': 'POS-001',
            }
        ],
        'metadata': {'anchor': {'entity': 'Room', 'id': 'L1-A'}},
    }

    subgraph = build_evidence_subgraph(fact_pack)

    assert subgraph.nodes['PoDPosition'][0].attributes['position_id'] == 'POS-001'
    assert subgraph.nodes['PoDPosition'][0].iid == '0xpos1'
    assert subgraph.edges[0].relation == 'ROOM_POSITION'
    assert subgraph.paths == ['Room(L1-A) --ROOM_POSITION--> PoDPosition(POS-001)']



def test_build_evidence_subgraph_preserves_relation_direction_when_anchor_is_link_target():
    fact_pack = {
        'instances': {
            'Room': [{'iid': '0xroom', 'room_id': 'L1-A'}],
            'PoDPosition': [{'iid': '0xpos1', 'position_id': 'POS-001'}],
        },
        'links': [
            {
                'source_entity': 'Room',
                'source_id': 'L1-A',
                'relation': 'ROOM_POSITION',
                'target_entity': 'PoDPosition',
                'target_id': 'POS-001',
            }
        ],
        'metadata': {'anchor': {'entity': 'PoDPosition', 'id': 'POS-001'}},
    }

    subgraph = build_evidence_subgraph(fact_pack)

    assert subgraph.paths == ['PoDPosition(POS-001) <--ROOM_POSITION-- Room(L1-A)']
