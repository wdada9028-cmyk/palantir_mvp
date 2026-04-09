from cloud_delivery_ontology_palantir.search.query_parser.alias_registry import AliasRegistry


def test_alias_registry_matches_exact_phrases_in_order():
    registry = AliasRegistry.from_dict({'Room': ['\u673a\u623f'], 'PoDSchedule': ['PoD\u5b89\u88c5\u8ba1\u5212']})

    mentions = registry.match('\u673a\u623f\u4f1a\u5f71\u54cdPoD\u5b89\u88c5\u8ba1\u5212')

    assert [(item.surface, item.canonical) for item in mentions] == [
        ('\u673a\u623f', 'Room'),
        ('PoD\u5b89\u88c5\u8ba1\u5212', 'PoDSchedule'),
    ]


def test_alias_registry_prefers_longest_match_first():
    registry = AliasRegistry.from_dict({'PoDSchedule': ['PoD\u5b89\u88c5\u8ba1\u5212', '\u5b89\u88c5\u8ba1\u5212']})

    mentions = registry.match('PoD\u5b89\u88c5\u8ba1\u5212\u6709\u54ea\u4e9b\u98ce\u9669')

    assert [(item.surface, item.canonical) for item in mentions] == [('PoD\u5b89\u88c5\u8ba1\u5212', 'PoDSchedule')]


def test_alias_registry_returns_non_overlapping_matches_with_positions():
    registry = AliasRegistry.from_dict({'Room': ['\u673a\u623f', '\u673a\u623f\u7a7a\u95f4']})

    mentions = registry.match('\u673a\u623f\u7a7a\u95f4\u548c\u673a\u623f')

    assert [(item.surface, item.start, item.end) for item in mentions] == [
        ('\u673a\u623f\u7a7a\u95f4', 0, 4),
        ('\u673a\u623f', 5, 7),
    ]
