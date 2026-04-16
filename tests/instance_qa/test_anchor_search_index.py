from pathlib import Path

from cloud_delivery_ontology_palantir.instance_qa.anchor_search_index import (
    build_anchor_search_index,
    search_anchor_candidates,
)


def test_anchor_search_index_prefers_exact_raw_value_match(tmp_path: Path):
    db_path = tmp_path / 'anchor.sqlite3'
    build_anchor_search_index(
        [
            {
                'entity': 'PoD',
                'attribute': 'pod_id',
                'raw_value': 'POD-001',
                'iid': 'iid-1',
                'payload': {'pod_id': 'POD-001'},
            },
            {
                'entity': 'PoD',
                'attribute': 'pod_id',
                'raw_value': 'Pod-001',
                'iid': 'iid-2',
                'payload': {'pod_id': 'Pod-001'},
            },
        ],
        db_path=db_path,
    )

    hits = search_anchor_candidates(db_path, 'POD-001', top_k=5)

    assert hits[0]['iid'] == 'iid-1'
    assert hits[0]['match_stage'] == 'exact'


def test_anchor_search_index_limits_top_k(tmp_path: Path):
    db_path = tmp_path / 'anchor.sqlite3'
    rows = [
        {
            'entity': 'PoD',
            'attribute': 'pod_id',
            'raw_value': f'POD-{i:03d}',
            'iid': f'iid-{i}',
            'payload': {'pod_id': f'POD-{i:03d}'},
        }
        for i in range(20)
    ]
    build_anchor_search_index(rows, db_path=db_path)

    hits = search_anchor_candidates(db_path, 'POD', top_k=5)

    assert len(hits) <= 5


def test_anchor_search_index_falls_back_to_normalized_match(tmp_path: Path):
    db_path = tmp_path / 'anchor.sqlite3'
    build_anchor_search_index(
        [
            {
                'entity': 'PoD',
                'attribute': 'pod_id',
                'raw_value': 'POD-001',
                'iid': 'iid-1',
                'payload': {'pod_id': 'POD-001'},
            },
        ],
        db_path=db_path,
    )

    hits = search_anchor_candidates(db_path, 'pod001', top_k=5)

    assert hits[0]['iid'] == 'iid-1'
    assert hits[0]['match_stage'] == 'normalized'
