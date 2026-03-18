from cloud_delivery_ontology_palantir.qa.template_answering import build_template_answer
from cloud_delivery_ontology_palantir.search.ontology_query_models import (
    EvidenceItem,
    OntologyEvidenceBundle,
    RetrievalStep,
    SearchTrace,
    TraceExpansionStep,
)


def test_build_template_answer_mentions_evidence_ids_and_localized_insufficient_evidence():
    bundle = OntologyEvidenceBundle(
        question='哪些服务器宕机',
        seed_node_ids=['object_type:PoD'],
        matched_node_ids=['object_type:PoD'],
        matched_edge_ids=[],
        highlight_steps=[RetrievalStep(action='anchor_node', message='定位到 PoD', node_ids=['object_type:PoD'])],
        evidence_chain=[
            EvidenceItem(
                evidence_id='E1',
                kind='seed',
                label='PoD',
                message='问题命中了实体 设备落位点(PoD)',
                node_ids=['object_type:PoD'],
                why_matched=['实体名称匹配'],
            )
        ],
        insufficient_evidence=True,
        search_trace=SearchTrace(seed_node_ids=['object_type:PoD']),
        display_name_map={'object_type:PoD': '设备落位点(PoD)'},
        relation_name_map={},
    )

    answer = build_template_answer(bundle)

    assert '证据不足' in answer.answer
    assert '[E1]' in answer.answer
    assert '设备落位点(PoD)' in answer.answer
    assert answer.insufficient_evidence is True


def test_build_template_answer_localizes_trace_report():
    bundle = OntologyEvidenceBundle(
        question='到货计划和泊位是什么关系',
        seed_node_ids=['object_type:ArrivalPlan'],
        matched_node_ids=['object_type:ArrivalPlan', 'object_type:PoDPosition'],
        matched_edge_ids=['e1'],
        highlight_steps=[RetrievalStep(action='anchor_node', message='定位到 ArrivalPlan', node_ids=['object_type:ArrivalPlan'])],
        evidence_chain=[
            EvidenceItem(
                evidence_id='E1',
                kind='seed',
                label='ArrivalPlan',
                message='问题命中了实体 到货计划(ArrivalPlan)',
                node_ids=['object_type:ArrivalPlan'],
                why_matched=['语义解析认为问题在问到货计划'],
            ),
            EvidenceItem(
                evidence_id='E2',
                kind='relation',
                label='ArrivalPlan REFERENCES PoDPosition',
                message='到货计划引用泊位',
                node_ids=['object_type:ArrivalPlan', 'object_type:PoDPosition'],
                edge_ids=['e1'],
                why_matched=['关系邻接扩展'],
            ),
        ],
        insufficient_evidence=False,
        search_trace=SearchTrace(
            seed_node_ids=['object_type:ArrivalPlan'],
            seed_resolution_source='llm',
            seed_resolution_reasoning='语义解析认为问题在问到货计划',
            seed_resolution_error='',
            expansion_steps=[
                TraceExpansionStep(
                    step=1,
                    from_node_id='object_type:ArrivalPlan',
                    edge_id='e1',
                    to_node_id='object_type:PoDPosition',
                    relation='REFERENCES',
                    reason='关系邻接扩展',
                    snapshot_node_ids=['object_type:ArrivalPlan', 'object_type:PoDPosition'],
                    snapshot_edge_ids=['e1'],
                )
            ],
        ),
        display_name_map={
            'object_type:ArrivalPlan': '到货计划(ArrivalPlan)',
            'object_type:PoDPosition': '泊位(PoDPosition)',
        },
        relation_name_map={'REFERENCES': '引用'},
    )

    answer = build_template_answer(bundle)

    assert '检索路径报告' in answer.answer
    assert '语义解析认为问题在问到货计划' in answer.answer
    assert '到货计划(ArrivalPlan)' in answer.answer
    assert '[引用]' in answer.answer
    assert '泊位(PoDPosition)' in answer.answer
    assert 'REFERENCES' not in answer.answer
    assert 'ArrivalPlan REFERENCES PoDPosition' not in answer.answer
    assert answer.insufficient_evidence is False
