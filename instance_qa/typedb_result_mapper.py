from __future__ import annotations

from collections import defaultdict


def map_typedb_rows_to_fact_pack(rows: list[dict[str, object]], *, purpose: str) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        entity = str(row.get('_entity') or row.get('entity') or 'Unknown').strip() or 'Unknown'
        payload = {key: value for key, value in row.items() if key not in {'_entity', 'entity'}}
        grouped[entity].append(payload)

    instances = {key: value for key, value in grouped.items()}
    counts = {entity: len(items) for entity, items in instances.items()}
    return {
        'instances': instances,
        'counts': counts,
        'metadata': {
            'purpose': purpose,
            'total_rows': len(rows),
        },
    }
