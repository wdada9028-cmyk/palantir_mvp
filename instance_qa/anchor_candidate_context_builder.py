from __future__ import annotations

import re
from typing import Iterable

from .anchor_candidate_resolver import AnchorCandidate, AnchorResolutionResult
from .schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry

_SUPPORTED_ENTITIES = {'PoD', 'Room', 'Project'}
_STATUS_HINTS = ('状态', '当前状态', 'status')
_LOCATION_HINTS = (
    '机房',
    '位置',
    '在哪',
    '在哪个',
    '在哪里',
    'location',
    'where',
    'floor',
    'building',
    'room',
)
_MODEL_NAME_HINTS = (
    '型号',
    '名称',
    '名字',
    '编码',
    '代码',
    '编号',
    'model',
    'name',
    'code',
)
_LOCATION_ENTITIES = {'Room', 'Floor', 'Building', 'PoDPosition'}
_MAX_CORE_ATTRIBUTES = 5
_MAX_BUSINESS_CONTEXT = 4


def build_anchor_candidate_context(
    *,
    question: str,
    schema_registry: SchemaRegistry,
    resolution: AnchorResolutionResult,
) -> dict[str, object]:
    normalized_question = str(question or '').strip()
    candidates_payload: list[dict[str, object]] = []

    for candidate in resolution.candidates:
        payload = _build_candidate_payload(
            candidate,
            candidate_index=len(candidates_payload) + 1,
            question=normalized_question,
            schema_registry=schema_registry,
            match_stage=resolution.match_stage,
        )
        if payload is not None:
            candidates_payload.append(payload)

    candidate_entity = ''
    if resolution.selected is not None and resolution.selected.entity in _SUPPORTED_ENTITIES:
        candidate_entity = resolution.selected.entity
    elif candidates_payload:
        candidate_entity = str(candidates_payload[0].get('entity') or '')

    return {
        'raw_anchor_text': resolution.raw_anchor_text,
        'question': normalized_question,
        'candidate_entity': candidate_entity,
        'candidates': candidates_payload,
    }


def _build_candidate_payload(
    candidate: AnchorCandidate,
    *,
    candidate_index: int,
    question: str,
    schema_registry: SchemaRegistry,
    match_stage: str,
) -> dict[str, object] | None:
    if candidate.entity not in _SUPPORTED_ENTITIES:
        return None

    entity_schema = schema_registry.entities.get(candidate.entity)
    if entity_schema is None:
        return None

    source_row = candidate.source_row if isinstance(candidate.source_row, dict) else {}
    return {
        'candidate_id': f'cand_{candidate_index}',
        'entity': candidate.entity,
        'locator': {
            'matched_attribute': candidate.attribute,
            'matched_value': candidate.value,
            'match_stage': str(match_stage or '').strip(),
        },
        'identity': _build_identity(candidate, entity_schema, source_row),
        'core_attributes': _build_core_attributes(question, entity_schema, source_row),
        'business_context': _build_business_context(question, candidate.entity, source_row, schema_registry),
    }


def _build_identity(candidate: AnchorCandidate, entity_schema: SchemaEntity, source_row: dict[str, object]) -> dict[str, object]:
    primary_id = _first_non_empty(source_row.get(attribute) for attribute in entity_schema.key_attributes)
    if not primary_id:
        primary_id = str(candidate.value or '').strip()

    aliases: list[str] = []
    for attribute in entity_schema.attributes:
        if attribute == 'iid':
            continue
        value = str(source_row.get(attribute) or '').strip()
        if not value or value == primary_id:
            continue
        if attribute.endswith('_code') or attribute.endswith('_name'):
            aliases.append(value)

    return {
        'primary_id': primary_id,
        'display_name': '',
        'aliases': _dedupe_preserve_order(aliases),
    }


def _build_core_attributes(question: str, entity_schema: SchemaEntity, source_row: dict[str, object]) -> dict[str, object]:
    question_lower = question.lower()
    entity_attributes = [attribute for attribute in entity_schema.attributes if attribute in source_row and attribute != 'iid']
    attribute_values = {
        attribute: source_row.get(attribute)
        for attribute in entity_attributes
        if source_row.get(attribute) not in (None, '')
    }

    has_status_hint = _contains_any(question_lower, _STATUS_HINTS)
    has_model_token = _contains_model_token(question)
    has_model_name_hint = _contains_any(question_lower, _MODEL_NAME_HINTS) or has_model_token

    if has_model_name_hint and (not has_status_hint or has_model_token):
        picked = [attribute for attribute in entity_attributes if attribute.endswith('_model') or attribute.endswith('_name') or attribute.endswith('_code')]
        model_name_values = _pick_attributes(attribute_values, picked)
        if model_name_values:
            return model_name_values

    if has_status_hint:
        picked = [attribute for attribute in entity_attributes if attribute.endswith('_status') or attribute == 'status']
        status_values = _pick_attributes(attribute_values, picked)
        if status_values:
            return status_values

    if _contains_any(question_lower, _LOCATION_HINTS):
        picked = [attribute for attribute in entity_attributes if attribute.endswith('_status') or attribute == 'status']
        location_values = _pick_attributes(attribute_values, picked)
        if location_values:
            return location_values

    default_order = [
        *[attribute for attribute in entity_attributes if attribute.endswith('_status')],
        *[attribute for attribute in entity_attributes if attribute.endswith('_model')],
        *[attribute for attribute in entity_attributes if attribute.endswith('_name')],
        *[attribute for attribute in entity_attributes if attribute.endswith('_code')],
    ]
    return _pick_attributes(attribute_values, default_order)


def _build_business_context(
    question: str,
    entity_name: str,
    source_row: dict[str, object],
    schema_registry: SchemaRegistry,
) -> list[dict[str, object]]:
    foreign_key_map = _build_foreign_key_entity_map(schema_registry, entity_name)
    contexts: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    for attribute, target_entity in foreign_key_map.items():
        value = str(source_row.get(attribute) or '').strip()
        if not value:
            continue
        dedupe_key = (target_entity, value)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        contexts.append(
            {
                'relation': _resolve_relation(entity_name, target_entity, schema_registry),
                'entity': target_entity,
                'id': value,
                'summary': _build_context_summary(target_entity, value),
            }
        )

    contexts = _sort_context_by_question(question, contexts)
    return contexts[:_MAX_BUSINESS_CONTEXT]


def _build_foreign_key_entity_map(schema_registry: SchemaRegistry, source_entity: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for entity_name, entity in schema_registry.entities.items():
        if entity_name == source_entity or entity_name not in _SUPPORTED_ENTITIES:
            continue
        for key_attribute in entity.key_attributes:
            result[key_attribute] = entity_name
    return result


def _resolve_relation(source_entity: str, target_entity: str, schema_registry: SchemaRegistry) -> str:
    for adjacency in schema_registry.adjacency.get(source_entity, []):
        if isinstance(adjacency, SchemaAdjacency) and adjacency.neighbor_entity == target_entity:
            return adjacency.relation
    for adjacency in schema_registry.adjacency.get(target_entity, []):
        if isinstance(adjacency, SchemaAdjacency) and adjacency.neighbor_entity == source_entity:
            return adjacency.relation
    return 'RELATED_TO'


def _build_context_summary(target_entity: str, target_id: str) -> str:
    if target_entity == 'Room':
        return f'位于机房 {target_id}'
    if target_entity == 'Project':
        return f'关联项目 {target_id}'
    return f'关联{target_entity} {target_id}'


def _sort_context_by_question(question: str, contexts: list[dict[str, object]]) -> list[dict[str, object]]:
    if not _contains_any(question.lower(), _LOCATION_HINTS):
        return contexts

    def _score(item: dict[str, object]) -> tuple[int, str]:
        entity = str(item.get('entity') or '')
        return (0 if entity in _LOCATION_ENTITIES else 1, entity)

    return sorted(contexts, key=_score)


def _pick_attributes(attribute_values: dict[str, object], ordered_candidates: list[str]) -> dict[str, object]:
    result: dict[str, object] = {}
    for attribute in ordered_candidates:
        if attribute in result or attribute not in attribute_values:
            continue
        if attribute == 'iid':
            continue
        result[attribute] = attribute_values[attribute]
        if len(result) >= _MAX_CORE_ATTRIBUTES:
            break
    return result


def _contains_model_token(text: str) -> bool:
    return re.search(r'[A-Za-z]{1,6}\d{2,}', text) is not None


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in text for keyword in keywords)


def _first_non_empty(values: Iterable[object]) -> str:
    for item in values:
        value = str(item or '').strip()
        if value:
            return value
    return ''


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
