from cloud_delivery_ontology_palantir.search.query_parser.models import IntentResult, ParsedQuery
from cloud_delivery_ontology_palantir.search.query_parser.retrieval_planner import build_retrieval_plan, merge_seed_entities


def test_merge_seed_entities_keeps_alias_entities_first_and_deduped():
    merged = merge_seed_entities(['Room', 'PoDSchedule'], ['PoDSchedule', 'ActivityInstance'])

    assert merged == ['Room', 'PoDSchedule', 'ActivityInstance']


def test_build_retrieval_plan_for_impact_analysis_uses_expected_preferences():
    parsed = ParsedQuery(
        raw_query='\u5982\u679c\u673a\u623f\u5ef6\u671f\uff0c\u4f1a\u5f71\u54cd\u54ea\u4e9bPoD\u5b89\u88c5\u8ba1\u5212\uff1f',
        normalized_query='\u5982\u679c\u673a\u623f\u5ef6\u671f \u4f1a\u5f71\u54cd\u54ea\u4e9bPoD\u5b89\u88c5\u8ba1\u5212',
        mentions=[],
        canonical_entities=['Room', 'PoDSchedule'],
        intent=IntentResult(name='impact_analysis', confidence=1.0, matched_rules=['\u5ef6\u671f', '\u5f71\u54cd']),
        unmatched_terms=[],
    )

    plan = build_retrieval_plan(parsed)

    assert plan.seed_entities == ['Room', 'PoDSchedule']
    assert 'DEPENDS_ON' in (plan.allowed_relations or [])
    assert plan.max_hop == 3
    assert plan.answer_style == 'impact_chain'


def test_build_retrieval_plan_for_relation_query_uses_expected_preferences():
    parsed = ParsedQuery(
        raw_query='\u673a\u623f\u548cPoD\u6709\u4ec0\u4e48\u5173\u7cfb',
        normalized_query='\u673a\u623f\u548cPoD\u6709\u4ec0\u4e48\u5173\u7cfb',
        mentions=[],
        canonical_entities=['Room', 'PoD'],
        intent=IntentResult(name='relation_query', confidence=1.0, matched_rules=['\u5173\u7cfb']),
        unmatched_terms=[],
    )

    plan = build_retrieval_plan(parsed)

    assert 'HAS' in (plan.allowed_relations or [])
    assert plan.max_hop == 2
    assert plan.answer_style == 'triple_list'
