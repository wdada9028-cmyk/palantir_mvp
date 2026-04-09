from cloud_delivery_ontology_palantir.search.query_parser.surface_normalizer import normalize_query


def test_normalize_query_removes_question_marks():
    assert normalize_query('PoD\u6709\u4ec0\u4e48\u5173\u7cfb\uff1f\uff1f') == 'PoD\u6709\u4ec0\u4e48\u5173\u7cfb'


def test_normalize_query_applies_nfkc():
    assert normalize_query('\uff30\uff4f\uff24\u3000\u5b89\u88c5\u8ba1\u5212') == 'PoD\u5b89\u88c5\u8ba1\u5212'


def test_normalize_query_collapses_whitespace():
    assert normalize_query('  PoD\n\t\u5b89\u88c5\u8ba1\u5212   ') == 'PoD\u5b89\u88c5\u8ba1\u5212'


def test_normalize_query_removes_spaces_outside_english_words():
    assert normalize_query('\u5982\u679c \u673a\u623f \u5ef6\u671f , PoD \u5b89\u88c5\u8ba1\u5212 \u4f1a \u53d7\u5f71\u54cd') == '\u5982\u679c\u673a\u623f\u5ef6\u671f,PoD\u5b89\u88c5\u8ba1\u5212\u4f1a\u53d7\u5f71\u54cd'


def test_normalize_query_preserves_spaces_between_english_words():
    assert normalize_query('arrival   plan') == 'arrival plan'
