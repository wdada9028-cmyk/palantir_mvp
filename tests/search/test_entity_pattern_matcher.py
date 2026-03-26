import pytest

from cloud_delivery_ontology_palantir.search.query_parser.entity_pattern_matcher import EntityPatternMatcher


def test_pattern_matcher_maps_placement_plan_family_terms():
    matcher = EntityPatternMatcher.from_dict(
        {
            'PlacementPlan': {
                'root_terms': ['\u843d\u4f4d'],
                'suffix_terms': ['\u65b9\u6848', '\u8ba1\u5212', '\u5efa\u8bae\u65b9\u6848'],
            }
        }
    )

    mentions = matcher.match('\u54ea\u4e9b\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\u65b9\u6848\u6267\u884c')

    assert [(m.surface, m.canonical, m.source) for m in mentions] == [
        ('\u843d\u4f4d\u65b9\u6848', 'PlacementPlan', 'pattern_rule')
    ]


def test_pattern_matcher_prefers_longest_non_overlapping_match():
    matcher = EntityPatternMatcher.from_dict(
        {
            'PlacementPlan': {
                'root_terms': ['\u843d\u4f4d', '\u843d\u4f4d\u5efa\u8bae'],
                'suffix_terms': ['\u65b9\u6848'],
            }
        }
    )

    mentions = matcher.match('\u8bf7\u68c0\u67e5\u843d\u4f4d\u5efa\u8bae\u65b9\u6848\u662f\u5426\u53ef\u6267\u884c')

    assert [(m.surface, m.start, m.end) for m in mentions] == [
        ('\u843d\u4f4d\u5efa\u8bae\u65b9\u6848', 3, 9)
    ]


def test_pattern_matcher_from_dict_validates_payload_mapping():
    with pytest.raises(ValueError, match='must be a mapping'):
        EntityPatternMatcher.from_dict({'PlacementPlan': ['\u843d\u4f4d']})
