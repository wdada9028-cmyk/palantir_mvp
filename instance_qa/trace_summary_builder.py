from __future__ import annotations

import re
from typing import Any

from .evidence_models import EvidenceBundle, EntityEvidenceGroup
from .question_models import QuestionDSL

_MODE_LABELS = {
    'impact_analysis': '\u5f71\u54cd\u5206\u6790',
    'deadline_risk_check': '\u4ea4\u4ed8\u98ce\u9669\u5224\u65ad',
    'fact_lookup': '\u5b9e\u4f8b\u67e5\u8be2',
}

_EVENT_LABELS = {
    'power_outage': '\u65ad\u7535',
    'fire': '\u706b\u707e',
    'delay': '\u5ef6\u671f',
    'capacity_loss': '\u4ea7\u80fd\u4e0d\u8db3',
    'access_blocked': '\u65e0\u6cd5\u8fdb\u5165',
    'generic_incident': '\u8fd0\u8425\u4e8b\u4ef6',
}

_GOAL_LABELS = {
    'list_impacts': '\u5f71\u54cd\u8303\u56f4',
    'yes_no_risk': '\u98ce\u9669\u786e\u8ba4',
    'instance_lookup': '\u5b9e\u4f8b\u8be6\u60c5',
}

_ANSWER_TYPE_LABELS = {
    'impact_list': '\u5f71\u54cd\u8303\u56f4\u5217\u8868',
    'deadline_risk': '\u4ea4\u4ed8\u98ce\u9669\u5224\u65ad',
}

_RISK_LABELS = {
    'high': '\u9ad8',
    'medium': '\u4e2d',
    'low': '\u4f4e',
    'unknown': '\u672a\u77e5',
}

_CONFIDENCE_LABELS = {
    'high': '\u9ad8',
    'medium': '\u4e2d',
    'low': '\u4f4e',
}

_ID_KEYS = ('id', 'room_id', 'floor_id', 'position_id', 'assignment_id', 'pod_id', 'pod_code', 'activity_id', 'pod_schedule_id')
_MAX_COMPACT_ITEMS_PER_ENTITY = 3
_MAX_INSTANCE_FIELDS = 3


def build_trace_summary(
    *,
    question_dsl: QuestionDSL,
    fact_pack: dict[str, object],
    evidence_bundle: EvidenceBundle,
    reasoning_result: dict[str, object],
) -> dict[str, object]:
    return {
        'compact': {
            'question_understanding': _build_question_understanding(question_dsl, fact_pack, evidence_bundle),
            'key_evidence': _build_key_evidence(evidence_bundle),
            'data_gaps': _build_compact_data_gaps(evidence_bundle),
            'reasoning_basis': _build_reasoning_basis(reasoning_result),
        },
        'expanded': {
            'detailed_evidence': _build_detailed_evidence(evidence_bundle),
            'key_paths': _build_key_paths(evidence_bundle.paths),
            'miss_explanations': _build_miss_explanations(evidence_bundle),
            'detailed_reasoning_basis': _build_detailed_reasoning_basis(reasoning_result),
        },
    }


def _build_question_understanding(
    question_dsl: QuestionDSL,
    fact_pack: dict[str, object],
    evidence_bundle: EvidenceBundle,
) -> dict[str, object]:
    return {
        'question_type': _mode_label(question_dsl.mode),
        'anchor': {
            'entity': question_dsl.anchor.entity,
            'id': _resolve_anchor_id(question_dsl, fact_pack, evidence_bundle),
        },
        'scenario': _event_label(question_dsl.scenario.event_type if question_dsl.scenario else ''),
        'goal': _goal_label(question_dsl.goal.type),
    }


def _resolve_anchor_id(
    question_dsl: QuestionDSL,
    fact_pack: dict[str, object],
    evidence_bundle: EvidenceBundle,
) -> str:
    direct = question_dsl.anchor.identifier.value if question_dsl.anchor.identifier else ''
    if str(direct).strip():
        return str(direct).strip()

    evidence_id = _anchor_id_from_evidence_understanding(evidence_bundle)
    if evidence_id:
        return evidence_id

    return _anchor_id_from_fact_pack(fact_pack, question_dsl.anchor.entity)


def _anchor_id_from_evidence_understanding(evidence_bundle: EvidenceBundle) -> str:
    understanding = evidence_bundle.understanding if isinstance(evidence_bundle.understanding, dict) else {}
    anchor = understanding.get('anchor') if isinstance(understanding, dict) else None
    if not isinstance(anchor, dict):
        return ''
    value = anchor.get('id')
    return str(value).strip() if value is not None else ''


def _anchor_id_from_fact_pack(fact_pack: dict[str, object], anchor_entity: str) -> str:
    metadata = fact_pack.get('metadata') if isinstance(fact_pack, dict) else None
    if isinstance(metadata, dict):
        anchor = metadata.get('anchor')
        if isinstance(anchor, dict):
            anchor_id = anchor.get('id')
            if anchor_id is not None and str(anchor_id).strip():
                return str(anchor_id).strip()

    instances = fact_pack.get('instances') if isinstance(fact_pack, dict) else None
    if not isinstance(instances, dict):
        return ''

    rows = instances.get(anchor_entity)
    if isinstance(rows, list) and rows:
        first = rows[0]
        if isinstance(first, dict):
            for key in _ID_KEYS:
                value = first.get(key)
                if value is not None and str(value).strip():
                    return str(value).strip()
    return ''


def _build_key_evidence(evidence_bundle: EvidenceBundle) -> dict[str, object]:
    direct_hits: dict[str, object] = {}
    omitted_counts = {item.entity: int(item.omitted_count) for item in evidence_bundle.omitted_entities}
    for group in evidence_bundle.positive_evidence:
        compact_items = [_compact_instance_view(item.business_keys, item.attributes) for item in group.instances[:_MAX_COMPACT_ITEMS_PER_ENTITY]]
        direct_hits[group.entity] = {
            'label': _entity_label(group),
            'total': len(group.instances) + omitted_counts.get(group.entity, 0),
            'items': compact_items,
        }

    return {
        'direct_hits': direct_hits,
        'empty_entities': [item.entity for item in evidence_bundle.empty_entities],
    }


def _build_compact_data_gaps(evidence_bundle: EvidenceBundle) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for item in evidence_bundle.empty_entities:
        items.append({
            'entity': item.entity,
            'type': 'empty',
            'message': f'{item.entity} \u5f53\u524d\u672a\u547d\u4e2d\u5b9e\u4f8b\u6570\u636e',
        })
    for item in evidence_bundle.unrelated_entities:
        items.append({
            'entity': item.entity,
            'type': 'unrelated',
            'message': f'{item.entity} \u5f53\u524d\u4e0e\u672c\u6b21\u95ee\u9898\u8bc1\u636e\u94fe\u65e0\u76f4\u63a5\u5173\u8054',
        })
    for item in evidence_bundle.omitted_entities:
        items.append({
            'entity': item.entity,
            'type': 'omitted',
            'message': f'{item.entity} \u547d\u4e2d\u7ed3\u679c\u8f83\u591a\uff0c\u5df2\u7701\u7565 {int(item.omitted_count)} \u6761',
        })
    return items


def _build_miss_explanations(evidence_bundle: EvidenceBundle) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for item in evidence_bundle.empty_entities:
        items.append({
            'entity': item.entity,
            'type': 'empty',
            'reason': item.reason,
        })
    for item in evidence_bundle.unrelated_entities:
        items.append({
            'entity': item.entity,
            'type': 'unrelated',
            'reason': item.reason,
        })
    for item in evidence_bundle.omitted_entities:
        items.append({
            'entity': item.entity,
            'type': 'omitted',
            'reason': item.reason,
            'omitted_count': int(item.omitted_count),
        })
    return items


def _build_reasoning_basis(reasoning_result: dict[str, object]) -> list[str]:
    summary = _summary(reasoning_result)
    impact_summary = _impact_summary(reasoning_result)
    deadline_assessment = _deadline_assessment(reasoning_result)

    items: list[str] = []
    answer_type = _answer_type_label(str(summary.get('answer_type', '')))
    if answer_type:
        items.append(f'\u7ed3\u8bba\u7c7b\u578b\uff1a{answer_type}')

    direct_counts = impact_summary.get('direct_counts') if isinstance(impact_summary, dict) else {}
    if isinstance(direct_counts, dict) and direct_counts:
        items.append(f'\u76f4\u63a5\u5f71\u54cd\uff1a{_format_counts(direct_counts)}')

    propagated_counts = impact_summary.get('propagated_counts') if isinstance(impact_summary, dict) else {}
    if isinstance(propagated_counts, dict) and propagated_counts:
        items.append(f'\u4f20\u64ad\u5f71\u54cd\uff1a{_format_counts(propagated_counts)}')

    risk_level = _risk_label(str(summary.get('risk_level', '')))
    if risk_level:
        items.append(f'\u98ce\u9669\u7b49\u7ea7\uff1a{risk_level}')

    confidence = _confidence_label(str(summary.get('confidence', '')))
    if confidence:
        items.append(f'\u7f6e\u4fe1\u5ea6\uff1a{confidence}')

    deadline = str(deadline_assessment.get('deadline') or '').strip()
    if deadline:
        items.append(f'\u5224\u65ad\u622a\u6b62\u65e5\u671f\uff1a{deadline}')
    if 'at_risk' in deadline_assessment:
        items.append(f'\u662f\u5426\u5b58\u5728\u4ea4\u4ed8\u98ce\u9669\uff1a{_yes_no(deadline_assessment.get("at_risk"))}')

    return items


def _build_detailed_reasoning_basis(reasoning_result: dict[str, object]) -> list[dict[str, object]]:
    summary = _summary(reasoning_result)
    impact_summary = _impact_summary(reasoning_result)
    deadline_assessment = _deadline_assessment(reasoning_result)

    items: list[dict[str, object]] = []
    answer_type = _answer_type_label(str(summary.get('answer_type', '')))
    if answer_type:
        items.append({'label': '\u7ed3\u8bba\u7c7b\u578b', 'value': answer_type})

    risk_level = _risk_label(str(summary.get('risk_level', '')))
    if risk_level:
        items.append({'label': '\u98ce\u9669\u7b49\u7ea7', 'value': risk_level})

    confidence = _confidence_label(str(summary.get('confidence', '')))
    if confidence:
        items.append({'label': '\u7f6e\u4fe1\u5ea6', 'value': confidence})

    direct_counts = impact_summary.get('direct_counts') if isinstance(impact_summary, dict) else {}
    if isinstance(direct_counts, dict) and direct_counts:
        items.append({'label': '\u76f4\u63a5\u5f71\u54cd', 'value': _format_counts(direct_counts)})

    propagated_counts = impact_summary.get('propagated_counts') if isinstance(impact_summary, dict) and impact_summary else {}
    if isinstance(propagated_counts, dict) and propagated_counts:
        items.append({'label': '\u4f20\u64ad\u5f71\u54cd', 'value': _format_counts(propagated_counts)})

    deadline = str(deadline_assessment.get('deadline') or '').strip()
    if deadline:
        items.append({'label': '\u5224\u65ad\u622a\u6b62\u65e5\u671f', 'value': deadline})
    if 'at_risk' in deadline_assessment:
        items.append({'label': '\u662f\u5426\u5b58\u5728\u4ea4\u4ed8\u98ce\u9669', 'value': _yes_no(deadline_assessment.get('at_risk'))})

    supporting_facts = deadline_assessment.get('supporting_facts') if isinstance(deadline_assessment, dict) else None
    if isinstance(supporting_facts, list) and supporting_facts:
        items.append({'label': '\u5173\u952e\u4f9d\u636e', 'value': '\uff1b'.join(str(item) for item in supporting_facts if str(item).strip())})

    return items


def _build_detailed_evidence(evidence_bundle: EvidenceBundle) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for group in evidence_bundle.positive_evidence:
        result.append(
            {
                'entity': group.entity,
                'label': _entity_label(group),
                'instances': [_instance_business_view(item.business_keys, item.attributes) for item in group.instances],
            }
        )
    return result


def _build_key_paths(paths: list[str]) -> list[dict[str, object]]:
    return [{'path_summary': _path_summary(path)} for path in paths]


def _path_summary(path: str) -> str:
    text = str(path)
    tokens = re.findall(r'([A-Za-z][A-Za-z0-9_]*)\(([^)]*)\)', text)
    if len(tokens) >= 2:
        source_entity, source_id = tokens[0]
        target_entity, target_id = tokens[-1]
        return f'{source_entity} {source_id} \u5f71\u54cd {target_entity} {target_id}'
    return text.replace('->', '\u5f71\u54cd').replace('--', ' ').strip()


def _entity_label(group: EntityEvidenceGroup) -> str:
    for item in group.instances:
        context = item.schema_context
        if context is None:
            continue
        if getattr(context, 'entity_zh', ''):
            return f'{group.entity}\uff08{context.entity_zh}\uff09'
    return group.entity


def _instance_business_view(business_keys: dict[str, Any], attributes: dict[str, Any]) -> dict[str, object]:
    result: dict[str, object] = {}

    for key, value in business_keys.items():
        result[str(key)] = _normalize_value(value)

    for key, value in attributes.items():
        key_text = str(key)
        if key_text in result:
            continue
        if key_text == 'id' or key_text.endswith('_id') or key_text.endswith('-id'):
            result[key_text] = _normalize_value(value)
            continue
        if key_text in {'name', 'room_name', 'position_name', 'status', 'position_status', 'room_status'}:
            result[key_text] = _normalize_value(value)

    return result


def _compact_instance_view(business_keys: dict[str, Any], attributes: dict[str, Any]) -> dict[str, object]:
    full = _instance_business_view(business_keys, attributes)
    if len(full) <= _MAX_INSTANCE_FIELDS:
        return full

    selected: dict[str, object] = {}
    for key in _ID_KEYS:
        if key in full:
            selected[key] = full[key]
            if len(selected) >= _MAX_INSTANCE_FIELDS:
                return selected

    for key in ('name', 'room_name', 'position_name', 'status', 'position_status', 'room_status'):
        if key in full and key not in selected:
            selected[key] = full[key]
            if len(selected) >= _MAX_INSTANCE_FIELDS:
                return selected

    for key, value in full.items():
        if key not in selected:
            selected[key] = value
            if len(selected) >= _MAX_INSTANCE_FIELDS:
                return selected

    return selected


def _summary(reasoning_result: dict[str, object]) -> dict[str, object]:
    summary = reasoning_result.get('summary') if isinstance(reasoning_result, dict) else {}
    return summary if isinstance(summary, dict) else {}


def _impact_summary(reasoning_result: dict[str, object]) -> dict[str, object]:
    impact_summary = reasoning_result.get('impact_summary') if isinstance(reasoning_result, dict) else {}
    return impact_summary if isinstance(impact_summary, dict) else {}


def _deadline_assessment(reasoning_result: dict[str, object]) -> dict[str, object]:
    assessment = reasoning_result.get('deadline_assessment') if isinstance(reasoning_result, dict) else {}
    return assessment if isinstance(assessment, dict) else {}


def _format_counts(counts: dict[str, object]) -> str:
    return '\u3001'.join(f'{entity} {int(value)}\u4e2a' for entity, value in counts.items() if int(value) > 0)


def _mode_label(mode: str) -> str:
    return _MODE_LABELS.get(mode, _readable(mode))


def _event_label(event_type: str) -> str:
    return _EVENT_LABELS.get(event_type, _readable(event_type))


def _goal_label(goal: str) -> str:
    return _GOAL_LABELS.get(goal, _readable(goal))


def _answer_type_label(answer_type: str) -> str:
    return _ANSWER_TYPE_LABELS.get(answer_type, _readable(answer_type))


def _risk_label(level: str) -> str:
    return _RISK_LABELS.get(level, _readable(level))


def _confidence_label(level: str) -> str:
    return _CONFIDENCE_LABELS.get(level, _readable(level))


def _yes_no(value: object) -> str:
    return '\u662f' if bool(value) else '\u5426'


def _readable(value: str) -> str:
    return str(value or '').strip().replace('_', ' ')


def _normalize_value(value: Any) -> object:
    if value is None:
        return ''
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
