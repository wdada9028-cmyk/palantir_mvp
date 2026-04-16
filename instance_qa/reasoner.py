from __future__ import annotations

from collections import Counter
from datetime import date

_TIME_ATTRIBUTES = (
    'planned_handover_time',
    'actual_handover_time',
    'assignment_date',
    'planned_start_time',
    'planned_finish_time',
    'latest_finish_time',
    'due_time',
)
_IMPACT_MAX_DEPTH = 3
_IMPACT_PRIORITY = ('WorkAssignment', 'PoD', 'ActivityInstance', 'PoDSchedule', 'RoomMilestone', 'Floor', 'PlacementPlan', 'Crew')


def build_reasoning_result(
    fact_pack: dict[str, object],
    *,
    mode: str,
    deadline: str | None = None,
) -> dict[str, object]:
    if mode == 'deadline_risk_check' and deadline:
        return assess_deadline_risk(fact_pack, deadline=deadline)

    affected_entities = _collect_affected_entities(fact_pack)
    impact_summary = _build_impact_summary(affected_entities)
    return {
        'summary': {
            'answer_type': 'impact_list',
            'risk_level': _impact_risk_level(impact_summary),
            'confidence': _impact_confidence(impact_summary),
        },
        'affected_entities': affected_entities,
        'impact_summary': impact_summary,
        'deadline_assessment': {
            'deadline': deadline,
            'at_risk': False,
            'reason_codes': [],
            'supporting_facts': [],
        },
        'evidence_chains': _build_evidence_chains(affected_entities),
    }


def assess_deadline_risk(fact_pack: dict[str, object], *, deadline: str) -> dict[str, object]:
    deadline_date = _parse_date(deadline)
    supporting_facts: list[str] = []
    reason_codes: list[str] = []
    matched_items: list[dict[str, object]] = []

    for entity_name, rows in _iter_instances(fact_pack):
        for row in rows:
            for attribute in _TIME_ATTRIBUTES:
                value = row.get(attribute)
                parsed = _parse_date(value)
                if parsed is None:
                    continue
                if deadline_date is not None and parsed <= deadline_date:
                    matched_items.append({'entity': entity_name, 'id': _instance_identifier(entity_name, row), 'reason': f'{attribute}={value}'})
                    supporting_facts.append(f'{entity_name}.{attribute}={value} overlaps deadline window')
                    reason_codes.append('affected_instance_before_deadline')
                    break

    at_risk = bool(matched_items)
    risk_level = 'high' if at_risk else 'unknown'
    confidence = 'high' if at_risk else 'low'

    return {
        'summary': {
            'answer_type': 'deadline_risk',
            'risk_level': risk_level,
            'confidence': confidence,
        },
        'affected_entities': matched_items,
        'impact_summary': {'direct_counts': {}, 'propagated_counts': {}},
        'deadline_assessment': {
            'deadline': deadline,
            'at_risk': at_risk,
            'reason_codes': sorted(set(reason_codes)),
            'supporting_facts': supporting_facts,
        },
        'evidence_chains': _build_evidence_chains(matched_items),
    }


def _iter_instances(fact_pack: dict[str, object]):
    instances = fact_pack.get('instances')
    if not isinstance(instances, dict):
        return []
    result = []
    for entity, rows in instances.items():
        if not isinstance(rows, list):
            continue
        result.append((str(entity), [item for item in rows if isinstance(item, dict)]))
    return result


def _collect_affected_entities(fact_pack: dict[str, object]) -> list[dict[str, object]]:
    anchor = _anchor_from_metadata(fact_pack)
    links = _links(fact_pack)
    if anchor and links:
        return _collect_via_links(anchor, links, max_depth=_IMPACT_MAX_DEPTH)[:50]

    items: list[dict[str, object]] = []
    for entity_name, rows in _iter_instances(fact_pack):
        for row in rows:
            items.append(
                {
                    'entity': entity_name,
                    'id': _instance_identifier(entity_name, row),
                    'reason': 'Matched instance in fact pack',
                    'depth': 1,
                }
            )
    return items[:50]


def _anchor_from_metadata(fact_pack: dict[str, object]) -> tuple[str, str] | None:
    metadata = fact_pack.get('metadata')
    if not isinstance(metadata, dict):
        return None
    anchor = metadata.get('anchor')
    if not isinstance(anchor, dict):
        return None
    entity = str(anchor.get('entity') or '').strip()
    anchor_id = str(anchor.get('id') or '').strip()
    if not entity or not anchor_id:
        return None
    return entity, anchor_id


def _links(fact_pack: dict[str, object]) -> list[dict[str, str]]:
    raw = fact_pack.get('links')
    if not isinstance(raw, list):
        return []
    result: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            result.append(
                {
                    'source_entity': str(item['source_entity']),
                    'source_id': str(item['source_id']),
                    'relation': str(item['relation']),
                    'target_entity': str(item['target_entity']),
                    'target_id': str(item['target_id']),
                }
            )
        except Exception:
            continue
    return result


def _collect_via_links(anchor: tuple[str, str], links: list[dict[str, str]], *, max_depth: int) -> list[dict[str, object]]:
    frontier = {anchor}
    visited = {anchor}
    affected: list[dict[str, object]] = []
    for depth in range(1, max_depth + 1):
        next_frontier: set[tuple[str, str]] = set()
        for link in links:
            source = (link['source_entity'], link['source_id'])
            target = (link['target_entity'], link['target_id'])
            if source in frontier and target not in visited:
                visited.add(target)
                next_frontier.add(target)
                affected.append({'entity': target[0], 'id': target[1], 'reason': f"{source[0]}({source[1]}) --{link['relation']}--> {target[0]}({target[1]})", 'depth': depth})
            if target in frontier and source not in visited:
                visited.add(source)
                next_frontier.add(source)
                affected.append({'entity': source[0], 'id': source[1], 'reason': f"{source[0]}({source[1]}) --{link['relation']}--> {target[0]}({target[1]})", 'depth': depth})
        frontier = next_frontier
        if not frontier:
            break
    return affected


def _build_impact_summary(items: list[dict[str, object]]) -> dict[str, object]:
    direct = Counter()
    propagated = Counter()
    for item in items:
        entity = str(item.get('entity') or '').strip()
        if not entity:
            continue
        depth = int(item.get('depth') or 1)
        if depth <= 1:
            direct[entity] += 1
        else:
            propagated[entity] += 1
    return {
        'direct_counts': _ordered_counts(direct),
        'propagated_counts': _ordered_counts(propagated),
    }


def _ordered_counts(counter: Counter) -> dict[str, int]:
    ordered_entities = [entity for entity in _IMPACT_PRIORITY if counter.get(entity)]
    ordered_entities.extend(sorted(entity for entity in counter if entity not in ordered_entities))
    return {entity: counter[entity] for entity in ordered_entities}


def _impact_risk_level(impact_summary: dict[str, object]) -> str:
    propagated = impact_summary.get('propagated_counts') if isinstance(impact_summary, dict) else {}
    direct = impact_summary.get('direct_counts') if isinstance(impact_summary, dict) else {}
    if isinstance(propagated, dict) and any(entity in propagated for entity in ('PoD', 'ActivityInstance', 'PoDSchedule')):
        return 'high'
    if isinstance(propagated, dict) and propagated:
        return 'medium'
    if isinstance(direct, dict) and direct:
        return 'medium'
    return 'unknown'


def _impact_confidence(impact_summary: dict[str, object]) -> str:
    propagated = impact_summary.get('propagated_counts') if isinstance(impact_summary, dict) else {}
    direct = impact_summary.get('direct_counts') if isinstance(impact_summary, dict) else {}
    if isinstance(propagated, dict) and propagated:
        return 'high'
    if isinstance(direct, dict) and direct:
        return 'medium'
    return 'low'


def _instance_identifier(entity_name: str, row: dict[str, object]) -> str:
    for key in ('id', f'{entity_name.lower()}_id', 'pod_code', 'assignment_id', 'activity_id', 'pod_schedule_id'):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return 'unknown'


def _build_evidence_chains(items: list[dict[str, object]]) -> list[list[str]]:
    chains: list[list[str]] = []
    for item in items[:20]:
        chains.append([f"{item.get('entity')}({item.get('id')})", str(item.get('reason', ''))])
    return chains


def _parse_date(value: object) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    token = text.split('T', 1)[0]
    token = token.replace('/', '-')
    try:
        return date.fromisoformat(token)
    except ValueError:
        return None
