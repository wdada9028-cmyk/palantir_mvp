from __future__ import annotations

from collections.abc import Iterable

from .evidence_models import SchemaContext
from .schema_registry import SchemaRegistry


def align_schema_context(
    *,
    entity: str,
    registry: SchemaRegistry,
    relevant_relations: Iterable[str] | None = None,
) -> SchemaContext:
    schema_entity = registry.entities.get(entity)
    if schema_entity is None:
        return SchemaContext(entity_name=entity, entity_zh='', key_attributes=[], relevant_relations=[])

    adjacency = registry.adjacency.get(entity, [])
    relation_names = {item.relation for item in adjacency if item.relation}
    relation_names.update(item.typedb_relation for item in adjacency if item.typedb_relation)

    filtered_relations = _filter_relevant_relations(relevant_relations, relation_names, adjacency)
    return SchemaContext(
        entity_name=schema_entity.name,
        entity_zh=schema_entity.zh_label or '',
        key_attributes=list(schema_entity.key_attributes),
        relevant_relations=filtered_relations,
    )


def _filter_relevant_relations(
    requested: Iterable[str] | None,
    available_names: set[str],
    adjacency,
) -> list[str]:
    if requested is not None:
        result: list[str] = []
        seen: set[str] = set()
        for item in requested:
            name = str(item or '').strip()
            if not name or name in seen or name not in available_names:
                continue
            seen.add(name)
            result.append(name)
        return result

    result: list[str] = []
    seen: set[str] = set()
    for edge in adjacency:
        name = str(edge.relation or '').strip()
        if not name or name in seen:
            continue
        seen.add(name)
        result.append(name)
    return result
