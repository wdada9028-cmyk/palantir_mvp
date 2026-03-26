from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation
from cloud_delivery_ontology_palantir.search.ontology_query_engine import retrieve_ontology_evidence
from cloud_delivery_ontology_palantir.search.query_parser import parse_query


def build_process_graph() -> OntologyGraph:
    graph = OntologyGraph(metadata={'title': 'process'})
    for name, zh in [
        ('PoD', 'PoD'),
        ('PoDSchedule', 'PoD??'),
        ('ActivityInstance', '????'),
        ('ArrivalPlan', '????'),
    ]:
        graph.add_object(
            OntologyObject(
                id=f'object_type:{name}',
                type='ObjectType',
                name=name,
                attributes={'chinese_description': zh},
            )
        )
    graph.add_relation(OntologyRelation(source_id='object_type:PoDSchedule', target_id='object_type:PoD', relation='APPLIES_TO'))
    graph.add_relation(OntologyRelation(source_id='object_type:PoDSchedule', target_id='object_type:ActivityInstance', relation='CONTAINS'))
    graph.add_relation(OntologyRelation(source_id='object_type:ArrivalPlan', target_id='object_type:PoD', relation='APPLIES_TO'))
    return graph


def test_retrieve_ontology_evidence_uses_normalized_alias_match_for_schedule_seed(monkeypatch):
    graph = build_process_graph()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        lambda graph, query: type('R', (), {'seeds': ['object_type:PoD'], 'reasoning': '', 'source': 'llm', 'error': ''})(),
    )

    result = retrieve_ontology_evidence(graph, 'PoD 安装计划有哪些关系？')

    assert result.seed_node_ids == ['object_type:PoDSchedule']
    assert result.matched_edge_ids == ['e1', 'e2']


def test_retrieve_ontology_evidence_keeps_seed_selection_stable_for_question_mark_variants(monkeypatch):
    graph = build_process_graph()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        lambda graph, query: type('R', (), {'seeds': ['object_type:PoD'], 'reasoning': '', 'source': 'llm', 'error': ''})(),
    )

    left = retrieve_ontology_evidence(graph, 'PoD 安装计划有哪些关系？')
    right = retrieve_ontology_evidence(graph, 'PoD 安装计划有哪些关系')

    assert left.seed_node_ids == right.seed_node_ids == ['object_type:PoDSchedule']
    assert left.matched_edge_ids == right.matched_edge_ids == ['e1', 'e2']


def test_parse_query_real_question_includes_exact_and_candidate_entities():
    parsed = parse_query('\u54ea\u4e9b\u91cc\u7a0b\u7891\u4f1a\u56e0\u4e3a\u7ea6\u675f\u51b2\u7a81\u5f71\u54cd\u5230\u843d\u4f4d\u65b9\u6848\u7684\u6267\u884c\uff1f')

    assert parsed.high_confidence_entities == ['ConstraintViolation', 'PlacementPlan']
    assert parsed.candidate_entities == []
    assert parsed.canonical_entities == ['ConstraintViolation', 'PlacementPlan']
