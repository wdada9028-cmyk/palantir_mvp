from cloud_delivery_ontology_palantir.qa.template_answering import build_template_answer
from cloud_delivery_ontology_palantir.search.ontology_query_models import EvidenceItem, OntologyEvidenceBundle, RetrievalStep


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
