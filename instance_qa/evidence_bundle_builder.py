from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .evidence_models import (
    EmptyEntityEvidence,
    EvidenceBundle,
    OmittedEntityEvidence,
    UnrelatedEntityEvidence,
    EntityEvidenceGroup,
    InstanceEvidence,
)
from .evidence_subgraph_builder import EvidenceSubgraph
from .schema_instance_aligner import align_schema_context
from .schema_registry import SchemaRegistry

_DEFAULT_EMPTY_REASON = 'schema matched but no instances'
_DEFAULT_UNRELATED_REASON = 'instances exist but unrelated to current evidence graph'
_DEFAULT_OMITTED_REASON = 'exceeds entity instance cap'


def build_evidence_bundle(
    *,
    question: str,
    schema_entities: list[str] | set[str],
    positive_entities: set[str] | None,
    empty_entities: dict[str, str] | None,
    unrelated_entities: dict[str, str] | None,
    omitted_entities: dict[str, Any] | None,
    subgraph: EvidenceSubgraph,
    registry: SchemaRegistry,
    understanding: dict[str, Any] | None = None,
    max_instances_per_entity: int = 20,
) -> EvidenceBundle:
    entity_cap = max(int(max_instances_per_entity), 1)
    schema_entity_set = {str(item) for item in schema_entities}

    empty_map = {str(k): str(v) for k, v in (empty_entities or {}).items()}
    unrelated_map = {str(k): str(v) for k, v in (unrelated_entities or {}).items()}
    omitted_map = _normalize_omitted_entities(omitted_entities or {})

    all_node_entities = list(subgraph.nodes.keys())
    positive_order = all_node_entities
    allow: set[str] | None = None
    if positive_entities is not None:
        allow = {str(item) for item in positive_entities}
        positive_order = [entity for entity in all_node_entities if entity in allow]
        for entity in all_node_entities:
            if entity in allow:
                continue
            unrelated_map.setdefault(entity, 'excluded by positive_entities filter')

    positive_groups: list[EntityEvidenceGroup] = []
    for entity in positive_order:
        rows = list(subgraph.nodes.get(entity, []))
        if not rows:
            continue

        relevant_relations = _relations_for_entity(entity, subgraph)
        schema_context = align_schema_context(
            entity=entity,
            registry=registry,
            relevant_relations=relevant_relations,
        )

        kept_rows: list[InstanceEvidence] = []
        for row in rows[:entity_cap]:
            kept_rows.append(
                InstanceEvidence(
                    entity=row.entity,
                    iid=row.iid,
                    business_keys=dict(row.business_keys),
                    attributes=dict(row.attributes),
                    schema_context=schema_context,
                    paths=_paths_for_instance(entity, row, subgraph.paths),
                )
            )

        overflow = max(len(rows) - len(kept_rows), 0)
        if overflow > 0:
            current = omitted_map.get(entity)
            if current is None:
                omitted_map[entity] = {'omitted_count': overflow, 'reason': _DEFAULT_OMITTED_REASON}
            else:
                current['omitted_count'] = int(current.get('omitted_count', 0)) + overflow

        positive_groups.append(EntityEvidenceGroup(entity=entity, instances=kept_rows))

    for entity in schema_entity_set:
        if entity in {group.entity for group in positive_groups}:
            continue
        if entity in unrelated_map:
            continue
        if entity in empty_map:
            continue
        if entity in subgraph.nodes and subgraph.nodes[entity]:
            continue
        empty_map[entity] = _DEFAULT_EMPTY_REASON

    empty_records = [
        EmptyEntityEvidence(entity=entity, reason=reason or _DEFAULT_EMPTY_REASON)
        for entity, reason in empty_map.items()
    ]
    unrelated_records = [
        UnrelatedEntityEvidence(entity=entity, reason=reason or _DEFAULT_UNRELATED_REASON)
        for entity, reason in unrelated_map.items()
    ]
    omitted_records = [
        OmittedEntityEvidence(
            entity=entity,
            omitted_count=int(info.get('omitted_count', 0)),
            reason=str(info.get('reason') or _DEFAULT_OMITTED_REASON),
        )
        for entity, info in omitted_map.items()
        if int(info.get('omitted_count', 0)) > 0
    ]

    return EvidenceBundle(
        question=question,
        understanding=dict(understanding or {}),
        positive_evidence=positive_groups,
        edges=list(subgraph.edges),
        paths=list(subgraph.paths),
        empty_entities=empty_records,
        unrelated_entities=unrelated_records,
        omitted_entities=omitted_records,
    )


def _normalize_omitted_entities(raw: dict[str, Any]) -> 'OrderedDict[str, dict[str, Any]]':
    result: 'OrderedDict[str, dict[str, Any]]' = OrderedDict()
    for entity, value in raw.items():
        name = str(entity)
        if isinstance(value, dict):
            result[name] = {
                'omitted_count': int(value.get('omitted_count', 0) or 0),
                'reason': str(value.get('reason') or _DEFAULT_OMITTED_REASON),
            }
            continue
        try:
            count = int(value)
        except Exception:
            count = 0
        result[name] = {'omitted_count': count, 'reason': _DEFAULT_OMITTED_REASON}
    return result


def _relations_for_entity(entity: str, subgraph: EvidenceSubgraph) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for edge in subgraph.edges:
        if edge.source_entity != entity and edge.target_entity != entity:
            continue
        relation = str(edge.relation or '').strip()
        if not relation or relation in seen:
            continue
        seen.add(relation)
        result.append(relation)
    return result


def _paths_for_instance(entity: str, row: InstanceEvidence, paths: list[str]) -> list[str]:
    tokens = _instance_path_tokens(entity, row)
    if not tokens:
        return []
    result: list[str] = []
    for path in paths:
        for token in tokens:
            if token in path:
                result.append(path)
                break
    return result


def _instance_path_tokens(entity: str, row: InstanceEvidence) -> list[str]:
    ids: list[str] = []
    if row.iid:
        ids.append(str(row.iid).strip())
    for value in row.business_keys.values():
        if value is None:
            continue
        token = str(value).strip()
        if token:
            ids.append(token)
    for key, value in row.attributes.items():
        key_text = str(key).strip().lower()
        if value is None:
            continue
        if key_text == 'id' or key_text.endswith('_id') or key_text.endswith('-id'):
            token = str(value).strip()
            if token:
                ids.append(token)

    deduped_ids: list[str] = []
    seen: set[str] = set()
    for item in ids:
        if item in seen:
            continue
        seen.add(item)
        deduped_ids.append(item)

    return [f'{entity}({item})' for item in deduped_ids]
