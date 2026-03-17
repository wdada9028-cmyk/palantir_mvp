from cloud_delivery_ontology_palantir.qa.template_answering import build_template_answer
from cloud_delivery_ontology_palantir.search.ontology_query_models import EvidenceItem, OntologyEvidenceBundle, RetrievalStep, SearchTrace, TraceExpansionStep


def test_build_template_answer_mentions_evidence_ids_and_insufficient_evidence():
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
                message='问题命中了实体 PoD',
                node_ids=['object_type:PoD'],
                why_matched=['实体名匹配'],
            )
        ],
        insufficient_evidence=True,
    )

    answer = build_template_answer(bundle)

    assert '证据不足' in answer.answer
    assert '[E1]' in answer.answer
    assert answer.insufficient_evidence is True


def test_build_template_answer_includes_search_trace_report_and_summary():
    bundle = OntologyEvidenceBundle(
        question='PoD 有什么关系',
        seed_node_ids=['object_type:PoD'],
        matched_node_ids=['object_type:PoD', 'object_type:ArrivalPlan'],
        matched_edge_ids=['e1'],
        highlight_steps=[RetrievalStep(action='anchor_node', message='定位到 PoD', node_ids=['object_type:PoD'])],
        evidence_chain=[
            EvidenceItem(
                evidence_id='E1',
                kind='seed',
                label='PoD',
                message='问题命中了实体 PoD',
                node_ids=['object_type:PoD'],
                why_matched=['实体名匹配'],
            ),
            EvidenceItem(
                evidence_id='E2',
                kind='relation',
                label='ArrivalPlan APPLIES_TO PoD',
                message='到货计划作用于 PoD',
                node_ids=['object_type:ArrivalPlan', 'object_type:PoD'],
                edge_ids=['e1'],
                why_matched=['关系邻接扩展'],
            ),
        ],
        insufficient_evidence=False,
        search_trace=SearchTrace(
            seed_node_ids=['object_type:PoD'],
            expansion_steps=[
                TraceExpansionStep(
                    step=1,
                    from_node_id='object_type:ArrivalPlan',
                    edge_id='e1',
                    to_node_id='object_type:PoD',
                    relation='APPLIES_TO',
                    reason='关系邻接扩展',
                    snapshot_node_ids=['object_type:PoD', 'object_type:ArrivalPlan'],
                    snapshot_edge_ids=['e1'],
                )
            ],
        ),
    )

    answer = build_template_answer(bundle)

    assert '检索路径报告' in answer.answer
    assert '沿“APPLIES_TO”关系扩展到“PoD”' in answer.answer
    assert '证据：' in answer.answer
    assert answer.insufficient_evidence is False
