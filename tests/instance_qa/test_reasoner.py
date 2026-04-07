from cloud_delivery_ontology_palantir.instance_qa.reasoner import assess_deadline_risk, build_reasoning_result


def test_assess_deadline_risk_marks_overlap_as_at_risk():
    fact_pack = {
        'instances': {
            'PoD': [
                {
                    'pod_code': 'POD-001',
                    'planned_handover_time': '2026-04-09',
                }
            ]
        },
        'metadata': {'purpose': 'collect_neighbors'},
    }

    result = assess_deadline_risk(fact_pack, deadline='2026-04-10')

    assert result['deadline_assessment']['at_risk'] is True
    assert result['summary']['risk_level'] in {'high', 'medium'}


def test_build_reasoning_result_returns_unknown_without_time_evidence():
    fact_pack = {
        'instances': {
            'WorkAssignment': [
                {'assignment_id': 'WA-001', 'assignment_status': 'open'}
            ]
        },
        'metadata': {'purpose': 'collect_neighbors'},
    }

    result = build_reasoning_result(fact_pack, mode='deadline_risk_check', deadline='2026-04-10')

    assert result['summary']['risk_level'] == 'unknown'
    assert result['deadline_assessment']['at_risk'] is False



def test_build_reasoning_result_uses_generic_link_propagation_for_impacts():
    fact_pack = {
        'instances': {
            'Room': [{'room_id': '01'}],
            'WorkAssignment': [{'assignment_id': 'WA-001'}],
            'PoD': [{'pod_code': 'POD-001'}],
        },
        'links': [
            {
                'source_entity': 'WorkAssignment',
                'source_id': 'WA-001',
                'relation': 'OCCURS_IN',
                'target_entity': 'Room',
                'target_id': '01',
            },
            {
                'source_entity': 'WorkAssignment',
                'source_id': 'WA-001',
                'relation': 'ASSIGNS',
                'target_entity': 'PoD',
                'target_id': 'POD-001',
            },
        ],
        'metadata': {
            'purpose': 'collect_neighbors',
            'anchor': {'entity': 'Room', 'id': '01'},
        },
    }

    result = build_reasoning_result(fact_pack, mode='impact_analysis')

    affected = {(item['entity'], item['id']) for item in result['affected_entities']}
    assert ('WorkAssignment', 'WA-001') in affected
    assert ('PoD', 'POD-001') in affected
    assert result['evidence_chains']


def test_assess_deadline_risk_includes_reason_codes_and_supporting_facts():
    fact_pack = {
        'instances': {
            'ActivityInstance': [
                {'activity_id': 'ACT-01', 'planned_finish_time': '2026-04-08'},
            ]
        },
        'links': [],
        'metadata': {'purpose': 'collect_deadline_targets'},
    }

    result = assess_deadline_risk(fact_pack, deadline='2026-04-10')

    assert result['deadline_assessment']['at_risk'] is True
    assert result['deadline_assessment']['reason_codes']
    assert result['deadline_assessment']['supporting_facts']
    assert result['summary']['confidence'] == 'high'



def test_build_reasoning_result_classifies_direct_and_propagated_impacts_from_three_hop_chain():
    fact_pack = {
        'instances': {
            'Room': [{'room_id': 'L1-A'}],
            'WorkAssignment': [{'assignment_id': 'WA-001'}],
            'PoD': [{'pod_id': 'POD-001'}],
            'ActivityInstance': [{'activity_id': 'ACT-001'}],
            'PoDSchedule': [{'pod_schedule_id': 'SCH-001'}],
        },
        'links': [
            {
                'source_entity': 'WorkAssignment',
                'source_id': 'WA-001',
                'relation': 'WORK_ASSIGNMENT_ROOM',
                'target_entity': 'Room',
                'target_id': 'L1-A',
            },
            {
                'source_entity': 'WorkAssignment',
                'source_id': 'WA-001',
                'relation': 'WORK_ASSIGNMENT_POD',
                'target_entity': 'PoD',
                'target_id': 'POD-001',
            },
            {
                'source_entity': 'PoD',
                'source_id': 'POD-001',
                'relation': 'POD_ACTIVITY',
                'target_entity': 'ActivityInstance',
                'target_id': 'ACT-001',
            },
            {
                'source_entity': 'PoDSchedule',
                'source_id': 'SCH-001',
                'relation': 'POD_SCHEDULE_POD',
                'target_entity': 'PoD',
                'target_id': 'POD-001',
            },
        ],
        'metadata': {
            'purpose': 'instance_qa',
            'anchor': {'entity': 'Room', 'id': 'L1-A'},
        },
    }

    result = build_reasoning_result(fact_pack, mode='impact_analysis')

    assert result['impact_summary']['direct_counts'] == {'WorkAssignment': 1}
    assert result['impact_summary']['propagated_counts'] == {
        'PoD': 1,
        'ActivityInstance': 1,
        'PoDSchedule': 1,
    }
    assert result['summary']['risk_level'] == 'high'
