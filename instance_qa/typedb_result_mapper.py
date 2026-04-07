from __future__ import annotations

from collections import defaultdict


_LINK_KEYS = ('_source_entity', '_source_id', '_relation', '_target_entity', '_target_id')
_GLOBAL_IDENTIFIER_CANDIDATES = (
    'iid',
    'id',
    'project_id',
    'building_id',
    'floor_id',
    'room_id',
    'position_id',
    'pod_id',
    'pod_code',
    'shipment_id',
    'arrival_event_id',
    'arrival_plan_id',
    'template_id',
    'dependency_template_id',
    'sla_id',
    'activity_id',
    'crew_id',
    'assignment_id',
    'placement_plan_id',
    'violation_id',
    'recommendation_id',
    'milestone_id',
)

_ENTITY_IDENTIFIER_PRIORITY = {
    'project': ('project_id', 'id'),
    'building': ('building_id', 'id'),
    'floor': ('floor_id', 'id'),
    'room': ('room_id', 'id'),
    'podposition': ('position_id', 'id'),
    'pod': ('pod_id', 'pod_code', 'id'),
    'shipment': ('shipment_id', 'id'),
    'arrivalevent': ('arrival_event_id', 'id'),
    'arrivalplan': ('arrival_plan_id', 'id'),
    'activitytemplate': ('template_id', 'id'),
    'activitydependencytemplate': ('dependency_template_id', 'id'),
    'slastandard': ('sla_id', 'id'),
    'activityinstance': ('activity_id', 'id'),
    'crew': ('crew_id', 'id'),
    'workassignment': ('assignment_id', 'id'),
    'placementplan': ('placement_plan_id', 'id'),
    'constraintviolation': ('violation_id', 'id'),
    'decisionrecommendation': ('recommendation_id', 'id'),
    'roommilestone': ('milestone_id', 'id'),
    'floormilestone': ('milestone_id', 'id'),
}


def map_typedb_rows_to_fact_pack(rows: list[dict[str, object]], *, purpose: str) -> dict[str, object]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    links: list[dict[str, str]] = []

    for row in rows:
        entity = str(row.get('_entity') or row.get('entity') or 'Unknown').strip() or 'Unknown'
        payload = {
            key: value
            for key, value in row.items()
            if key not in {'_entity', 'entity', *_LINK_KEYS}
        }
        iid_value = row.get('_iid') if isinstance(row, dict) else None
        if iid_value is not None and str(iid_value).strip():
            payload['iid'] = str(iid_value).strip()
        grouped[entity].append(payload)

        link = _extract_link(row)
        if link is not None:
            links.append(link)

    instances = {entity: _dedupe_instances(entity, items) for entity, items in grouped.items()}
    counts = {entity: len(items) for entity, items in instances.items()}
    return {
        'instances': instances,
        'counts': counts,
        'links': _dedupe_links(links),
        'metadata': {
            'purpose': purpose,
            'total_rows': len(rows),
        },
    }


def _extract_link(row: dict[str, object]) -> dict[str, str] | None:
    values = [row.get(key) for key in _LINK_KEYS]
    if any(value is None or not str(value).strip() for value in values):
        return None
    return {
        'source_entity': str(row['_source_entity']).strip(),
        'source_id': str(row['_source_id']).strip(),
        'relation': str(row['_relation']).strip(),
        'target_entity': str(row['_target_entity']).strip(),
        'target_id': str(row['_target_id']).strip(),
    }


def _dedupe_instances(entity: str, rows: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[object, ...]] = set()
    result: list[dict[str, object]] = []
    for row in rows:
        key = _instance_dedupe_key(entity, row)
        if key in seen:
            continue
        seen.add(key)
        result.append(row)
    return result


def _instance_dedupe_key(entity: str, row: dict[str, object]) -> tuple[object, ...]:
    entity_lower = _normalize_entity_key(entity)

    iid = row.get('iid')
    if iid is not None and str(iid).strip():
        return ('iid', entity, str(iid).strip())

    for attr in _ENTITY_IDENTIFIER_PRIORITY.get(entity_lower, ()):
        value = row.get(attr)
        if value is None or not str(value).strip():
            continue
        return ('id', entity, attr, str(value).strip())

    dynamic_key = f'{entity_lower}_id'
    value = row.get(dynamic_key)
    if value is not None and str(value).strip():
        return ('id', entity, dynamic_key, str(value).strip())

    for attr in _GLOBAL_IDENTIFIER_CANDIDATES:
        value = row.get(attr)
        if value is None or not str(value).strip():
            continue
        return ('id', entity, attr, str(value).strip())

    normalized_items = tuple(sorted((str(k), repr(v)) for k, v in row.items()))
    return ('row', entity, *normalized_items)


def _dedupe_links(links: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str, str, str]] = set()
    result: list[dict[str, str]] = []
    for item in links:
        key = (
            item['source_entity'],
            item['source_id'],
            item['relation'],
            item['target_entity'],
            item['target_id'],
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result



def _normalize_entity_key(entity: str) -> str:
    return "".join(ch for ch in str(entity or "").lower() if ch.isalnum())
