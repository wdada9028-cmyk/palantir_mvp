from __future__ import annotations

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


def build_reasoning_result(
    fact_pack: dict[str, object],
    *,
    mode: str,
    deadline: str | None = None,
) -> dict[str, object]:
    if mode == 'deadline_risk_check' and deadline:
        return assess_deadline_risk(fact_pack, deadline=deadline)

    affected_entities = _collect_affected_entities(fact_pack)
    return {
        'summary': {
            'answer_type': 'impact_list',
            'risk_level': 'medium' if affected_entities else 'unknown',
            'confidence': 'medium' if affected_entities else 'low',
        },
        'affected_entities': affected_entities,
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
    items: list[dict[str, object]] = []
    for entity_name, rows in _iter_instances(fact_pack):
        for row in rows:
            items.append(
                {
                    'entity': entity_name,
                    'id': _instance_identifier(entity_name, row),
                    'reason': 'Matched instance in fact pack',
                }
            )
    return items[:20]


def _instance_identifier(entity_name: str, row: dict[str, object]) -> str:
    for key in ('id', f'{entity_name.lower()}_id', 'pod_code', 'assignment_id'):
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
