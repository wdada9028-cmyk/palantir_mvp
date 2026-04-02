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
