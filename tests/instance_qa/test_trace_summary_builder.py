from __future__ import annotations

from cloud_delivery_ontology_palantir.instance_qa.evidence_models import (
    EntityEvidenceGroup,
    EvidenceBundle,
    InstanceEvidence,
)
from cloud_delivery_ontology_palantir.instance_qa.question_models import (
    AnchorRef,
    ConstraintRef,
    GoalRef,
    QuestionDSL,
    ScenarioRef,
)
from cloud_delivery_ontology_palantir.instance_qa.trace_summary_builder import build_trace_summary


def _make_question() -> QuestionDSL:
    return QuestionDSL(
        mode='impact_analysis',
        anchor=AnchorRef(entity='Room', surface='Will outage impact room L1-A101'),
        scenario=ScenarioRef(event_type='power_outage', raw_event='outage'),
        goal=GoalRef(type='list_impacts'),
        constraints=ConstraintRef(limit=20),
    )


def _make_fact_pack() -> dict[str, object]:
    return {
        'instances': {
            'Room': [{'id': 'L1-A101', 'room_name': 'A101'}],
            'WorkAssignment': [{'assignment_id': 'WA-1', 'status': 'planned'}],
        }
    }


def _make_bundle() -> EvidenceBundle:
    return EvidenceBundle(
        question='Will outage impact room L1-A101',
        understanding={'mode': 'impact_analysis', 'anchor': {'entity': 'Room', 'id': 'L1-A101'}},
        positive_evidence=[
            EntityEvidenceGroup(
                entity='Room',
                instances=[
                    InstanceEvidence(
                        entity='Room',
                        iid='0x1',
                        business_keys={'id': 'L1-A101'},
                        attributes={'room_name': 'A101'},
                    )
                ],
            )
        ],
        paths=['Room(L1-A101) -> WorkAssignment(WA-1)'],
    )


def _make_reasoning() -> dict[str, object]:
    return {
        'summary': {'answer_type': 'impact_list', 'risk_level': 'medium', 'confidence': 'high'},
        'impact_summary': {'direct_counts': {'WorkAssignment': 1}, 'propagated_counts': {}},
    }


def test_build_trace_summary_returns_compact_and_expanded_sections() -> None:
    summary = build_trace_summary(
        question_dsl=_make_question(),
        fact_pack=_make_fact_pack(),
        evidence_bundle=_make_bundle(),
        reasoning_result=_make_reasoning(),
    )

    assert list(summary.keys()) == ['compact', 'expanded']
    assert 'question_understanding' in summary['compact']
    assert 'key_evidence' in summary['compact']
    assert 'data_gaps' in summary['compact']
    assert 'reasoning_basis' in summary['compact']
    assert 'detailed_evidence' in summary['expanded']
    assert 'key_paths' in summary['expanded']
    assert 'miss_explanations' in summary['expanded']
    assert 'detailed_reasoning_basis' in summary['expanded']
    assert 'fact_queries' not in summary['compact']
    assert 'decision_signal' not in summary['compact']


def test_build_trace_summary_uses_chinese_business_labels_only() -> None:
    summary = build_trace_summary(
        question_dsl=_make_question(),
        fact_pack=_make_fact_pack(),
        evidence_bundle=_make_bundle(),
        reasoning_result=_make_reasoning(),
    )

    understanding = summary['compact']['question_understanding']
    compact_reasoning = summary['compact']['reasoning_basis']
    detailed_reasoning = summary['expanded']['detailed_reasoning_basis']

    assert understanding['question_type'] == '影响分析'
    assert understanding['scenario'] == '断电'
    assert understanding['goal'] == '影响范围'

    assert '结论类型：影响范围列表' in compact_reasoning
    assert '风险等级：中' in compact_reasoning
    assert '置信度：高' in compact_reasoning

    assert {'label': '结论类型', 'value': '影响范围列表'} in detailed_reasoning
    assert {'label': '风险等级', 'value': '中'} in detailed_reasoning
    assert {'label': '置信度', 'value': '高'} in detailed_reasoning

    path = summary['expanded']['key_paths'][0]
    assert isinstance(path, dict)
    assert path['path_summary'] == 'Room L1-A101 影响 WorkAssignment WA-1'
    assert '->' not in path['path_summary']
    assert 'impact_analysis' not in str(summary)
    assert 'power_outage' not in str(summary)
    assert 'list_impacts' not in str(summary)
    assert 'impact_list' not in str(summary)


def test_anchor_id_falls_back_to_evidence_understanding_when_question_identifier_missing() -> None:
    summary = build_trace_summary(
        question_dsl=_make_question(),
        fact_pack=_make_fact_pack(),
        evidence_bundle=_make_bundle(),
        reasoning_result=_make_reasoning(),
    )

    assert summary['compact']['question_understanding']['anchor']['id'] == 'L1-A101'


def test_anchor_id_falls_back_to_fact_pack_when_evidence_understanding_missing_id() -> None:
    bundle = EvidenceBundle(
        question='Will outage impact room L1-A101',
        understanding={'anchor': {'entity': 'Room'}},
        positive_evidence=_make_bundle().positive_evidence,
        paths=_make_bundle().paths,
    )

    summary = build_trace_summary(
        question_dsl=_make_question(),
        fact_pack=_make_fact_pack(),
        evidence_bundle=bundle,
        reasoning_result=_make_reasoning(),
    )

    assert summary['compact']['question_understanding']['anchor']['id'] == 'L1-A101'


def test_anchor_id_does_not_fall_back_to_unrelated_entity_row() -> None:
    bundle = EvidenceBundle(
        question='Will outage impact room L1-A101',
        understanding={'anchor': {'entity': 'Room'}},
        positive_evidence=[],
        paths=[],
    )
    fact_pack = {
        'instances': {
            'WorkAssignment': [{'assignment_id': 'WA-1', 'status': 'planned'}],
        }
    }

    summary = build_trace_summary(
        question_dsl=_make_question(),
        fact_pack=fact_pack,
        evidence_bundle=bundle,
        reasoning_result=_make_reasoning(),
    )

    assert summary['compact']['question_understanding']['anchor']['id'] == ''


def test_trace_summary_includes_data_gaps_and_miss_explanations() -> None:
    from cloud_delivery_ontology_palantir.instance_qa.evidence_models import EmptyEntityEvidence, OmittedEntityEvidence, UnrelatedEntityEvidence

    bundle = EvidenceBundle(
        question='Will outage impact room L1-A101',
        understanding={'mode': 'impact_analysis', 'anchor': {'entity': 'Room', 'id': 'L1-A101'}},
        positive_evidence=_make_bundle().positive_evidence,
        paths=_make_bundle().paths,
        empty_entities=[EmptyEntityEvidence(entity='PoDSchedule', reason='schema matched but no instances')],
        unrelated_entities=[UnrelatedEntityEvidence(entity='Crew', reason='instances exist but unrelated to current evidence graph')],
        omitted_entities=[OmittedEntityEvidence(entity='PoDPosition', omitted_count=4, reason='cap')],
    )

    summary = build_trace_summary(
        question_dsl=_make_question(),
        fact_pack=_make_fact_pack(),
        evidence_bundle=bundle,
        reasoning_result=_make_reasoning(),
    )

    compact_gaps = summary['compact']['data_gaps']
    expanded_gaps = summary['expanded']['miss_explanations']

    assert {'entity': 'PoDSchedule', 'type': 'empty', 'message': 'PoDSchedule 当前未命中实例数据'} in compact_gaps
    assert {'entity': 'Crew', 'type': 'unrelated', 'message': 'Crew 当前与本次问题证据链无直接关联'} in compact_gaps
    assert {'entity': 'PoDPosition', 'type': 'omitted', 'message': 'PoDPosition 命中结果较多，已省略 4 条'} in compact_gaps

    assert {'entity': 'PoDSchedule', 'type': 'empty', 'reason': 'schema matched but no instances'} in expanded_gaps
    assert {'entity': 'Crew', 'type': 'unrelated', 'reason': 'instances exist but unrelated to current evidence graph'} in expanded_gaps
    assert {'entity': 'PoDPosition', 'type': 'omitted', 'reason': 'cap', 'omitted_count': 4} in expanded_gaps


def test_trace_summary_limits_instance_lists_and_keeps_counts() -> None:
    pod_positions = [
        InstanceEvidence(
            entity='PoDPosition',
            iid=f'0x{i}',
            business_keys={
                'position_id': f'POS-{i}',
            },
            attributes={
                'position_id': f'POS-{i}',
                'position_name': f'Position {i}',
                'position_status': 'active' if i % 2 else 'planned',
                'owner': f'team-{i}',
                'updated_at': f'2026-04-0{i}',
            },
        )
        for i in range(1, 4)
    ]
    bundle = EvidenceBundle(
        question='Will outage impact room L1-A101',
        understanding={'mode': 'impact_analysis', 'anchor': {'entity': 'Room', 'id': 'L1-A101'}},
        positive_evidence=[EntityEvidenceGroup(entity='PoDPosition', instances=pod_positions)],
        paths=['Room(L1-A101) -> PoDPosition(POS-1)'],
        omitted_entities=[],
    )

    summary = build_trace_summary(
        question_dsl=_make_question(),
        fact_pack=_make_fact_pack(),
        evidence_bundle=bundle,
        reasoning_result=_make_reasoning(),
    )

    positions = summary['compact']['key_evidence']['direct_hits']['PoDPosition']
    assert positions['total'] == 3
    assert len(positions['items']) <= 3
    assert all(len(item) <= 3 for item in positions['items'])
    assert all('position_id' in item for item in positions['items'])
    assert any('position_name' in item or 'position_status' in item for item in positions['items'])


def test_trace_summary_total_includes_omitted_entities() -> None:
    pod_positions = [
        InstanceEvidence(
            entity='PoDPosition',
            iid='0x1',
            business_keys={'position_id': 'POS-1'},
            attributes={'position_id': 'POS-1', 'position_name': 'Position 1', 'position_status': 'active'},
        )
    ]
    from cloud_delivery_ontology_palantir.instance_qa.evidence_models import OmittedEntityEvidence
    bundle = EvidenceBundle(
        question='Will outage impact room L1-A101',
        understanding={'mode': 'impact_analysis', 'anchor': {'entity': 'Room', 'id': 'L1-A101'}},
        positive_evidence=[EntityEvidenceGroup(entity='PoDPosition', instances=pod_positions)],
        paths=[],
        omitted_entities=[OmittedEntityEvidence(entity='PoDPosition', omitted_count=4, reason='cap')],
    )

    summary = build_trace_summary(
        question_dsl=_make_question(),
        fact_pack=_make_fact_pack(),
        evidence_bundle=bundle,
        reasoning_result=_make_reasoning(),
    )

    positions = summary['compact']['key_evidence']['direct_hits']['PoDPosition']
    assert positions['total'] == 5
