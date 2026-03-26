from cloud_delivery_ontology_palantir.search.query_parser.alias_registry import AliasRegistry
from cloud_delivery_ontology_palantir.search.query_parser.entity_pattern_matcher import EntityPatternMatcher
from cloud_delivery_ontology_palantir.search.query_parser.models import EntityMention, IntentResult, ParsedQuery, RetrievalPlan
from cloud_delivery_ontology_palantir.search.query_parser.parser import parse_query


def test_query_parser_models_construct_expected_shapes():
    mention = EntityMention(surface='机房', canonical='Room', start=0, end=2, source='alias_rule')
    intent = IntentResult(name='relation_query', confidence=1.0, matched_rules=['关系'])
    parsed = ParsedQuery(
        raw_query='机房有什么关系？',
        normalized_query='机房有什么关系',
        mentions=[mention],
        canonical_entities=['Room'],
        high_confidence_entities=['Room'],
        candidate_entities=[],
        intent=intent,
        unmatched_terms=['有什么关系'],
    )
    plan = RetrievalPlan(
        seed_entities=['Room'],
        allowed_relations=['HAS'],
        blocked_relations=None,
        max_hop=2,
        answer_style='triple_list',
        ranking_policy='relation_first',
        debug_reason=['intent=relation_query'],
    )

    assert parsed.canonical_entities == ['Room']
    assert parsed.high_confidence_entities == ['Room']
    assert parsed.candidate_entities == []
    assert plan.seed_entities == ['Room']


def test_parse_query_extracts_canonical_entities_and_intent():
    parsed = parse_query('如果机房延期，会影响哪些 PoD 安装计划？')

    assert parsed.canonical_entities == ['Room', 'PoDSchedule']
    assert parsed.high_confidence_entities == ['Room', 'PoDSchedule']
    assert parsed.candidate_entities == []
    assert parsed.intent.name == 'impact_analysis'
    assert [item.surface for item in parsed.mentions] == ['机房', 'PoD安装计划']


def test_parse_query_is_stable_for_question_mark_variants():
    left = parse_query('如果机房延期，会影响哪些 PoD 安装计划？')
    right = parse_query('如果机房延期，会影响哪些PoD安装计划')

    assert left.normalized_query == right.normalized_query
    assert left.canonical_entities == right.canonical_entities
    assert left.high_confidence_entities == right.high_confidence_entities
    assert left.candidate_entities == right.candidate_entities
    assert left.intent.name == right.intent.name


def test_parse_query_suppresses_pattern_mentions_that_overlap_exact_alias_mentions():
    matcher = EntityPatternMatcher.from_dict(
        {
            'PlacementPlan': {
                'root_terms': ['落位'],
                'suffix_terms': ['计划'],
            }
        }
    )
    parsed = parse_query(
        '落位计划有哪些约束',
        entity_pattern_matcher=matcher,
    )

    assert parsed.high_confidence_entities == ['PlacementPlan']
    assert parsed.candidate_entities == []
    assert [(item.surface, item.source) for item in parsed.mentions] == [
        ('落位计划', 'alias_rule'),
    ]


def test_parse_query_separates_exact_entities_from_pattern_candidates():
    alias_registry = AliasRegistry.from_dict(
        {
            'ConstraintViolation': ['约束冲突'],
        }
    )
    matcher = EntityPatternMatcher.from_dict(
        {
            'PlacementPlan': {
                'root_terms': ['落位'],
                'suffix_terms': ['方案', '计划', '建议方案'],
            }
        }
    )
    parsed = parse_query(
        '哪些里程碑会因为约束冲突影响到落位方案的执行',
        alias_registry=alias_registry,
        entity_pattern_matcher=matcher,
    )

    assert parsed.high_confidence_entities == ['ConstraintViolation']
    assert parsed.candidate_entities == ['PlacementPlan']
    assert parsed.canonical_entities == ['ConstraintViolation', 'PlacementPlan']
    assert [(item.surface, item.source) for item in parsed.mentions] == [
        ('约束冲突', 'alias_rule'),
        ('落位方案', 'pattern_rule'),
    ]
