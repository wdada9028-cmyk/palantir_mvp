from cloud_delivery_ontology_palantir.instance_qa.anchor_normalizer import (
    normalize_anchor_text_light,
    normalize_anchor_text_loose,
)


def test_normalize_anchor_text_light_uppercases_and_trims():
    assert normalize_anchor_text_light('  pod-001  ') == 'POD-001'


def test_normalize_anchor_text_light_collapses_whitespace_and_normalizes_dashes():
    assert normalize_anchor_text_light('PoD — 001') == 'POD - 001'


def test_normalize_anchor_text_loose_compacts_separator_noise():
    assert normalize_anchor_text_loose(' pOd - 001 ') == 'POD001'


def test_normalize_anchor_text_loose_preserves_alphanumeric_signal_only():
    assert normalize_anchor_text_loose(' L1_A / Room ') == 'L1AROOM'
