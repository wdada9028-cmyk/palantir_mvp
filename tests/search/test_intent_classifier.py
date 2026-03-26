from cloud_delivery_ontology_palantir.search.query_parser.intent_classifier import IntentClassifier


RULES = {
    'impact_analysis': {'priority': 100, 'keywords': ['\u5f71\u54cd', '\u98ce\u9669', '\u5ef6\u671f']},
    'relation_query': {'priority': 60, 'keywords': ['\u5173\u7cfb', '\u5173\u8054']},
    'listing_query': {'priority': 40, 'keywords': ['\u54ea\u4e9b']},
}


def test_intent_classifier_detects_impact_analysis():
    classifier = IntentClassifier.from_dict(RULES)

    result = classifier.classify('\u5ef6\u671f\u4f1a\u5f71\u54cd\u54ea\u4e9bPoD\u5b89\u88c5\u8ba1\u5212')

    assert result.name == 'impact_analysis'
    assert '\u5f71\u54cd' in result.matched_rules


def test_intent_classifier_detects_relation_query():
    classifier = IntentClassifier.from_dict(RULES)

    result = classifier.classify('\u673a\u623f\u548cPoD\u662f\u4ec0\u4e48\u5173\u7cfb')

    assert result.name == 'relation_query'
    assert '\u5173\u7cfb' in result.matched_rules


def test_intent_classifier_prefers_higher_priority_when_multiple_intents_match():
    classifier = IntentClassifier.from_dict(RULES)

    result = classifier.classify('\u8fd9\u4e9b\u5ef6\u671f\u98ce\u9669\u4f1a\u5f71\u54cd\u54ea\u4e9bPoD\u5b89\u88c5\u8ba1\u5212')

    assert result.name == 'impact_analysis'


def test_intent_classifier_defaults_to_listing_query_when_no_rule_matches():
    classifier = IntentClassifier.from_dict(RULES)

    result = classifier.classify('PoD\u5b89\u88c5\u8ba1\u5212')

    assert result.name == 'listing_query'
