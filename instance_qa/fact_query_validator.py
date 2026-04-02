from __future__ import annotations

from .fact_query_models import FactQueryDSL
from .schema_registry import SchemaRegistry

_ALLOWED_PURPOSES = {'resolve_anchor', 'collect_neighbors'}
_ALLOWED_FILTER_OPS = {'eq', 'in', 'gt', 'gte', 'lt', 'lte'}
_ALLOWED_AGGREGATES = {None, 'count'}
_ALLOWED_SORT_DIRECTIONS = {'asc', 'desc'}
_MAX_LIMIT = 1000


def validate_fact_query_dsl(query: FactQueryDSL, schema_registry: SchemaRegistry) -> str | None:
    if query.purpose not in _ALLOWED_PURPOSES:
        return f'Unsupported fact query purpose: {query.purpose}'

    root_entity = schema_registry.entities.get(query.root.entity)
    if root_entity is None:
        return f'Unknown root entity: {query.root.entity}'

    identifier = query.root.identifier
    if identifier is not None:
        if identifier.attribute not in root_entity.attributes:
            return f'Unknown root identifier attribute {identifier.attribute!r} for entity {query.root.entity}'
        if identifier.attribute not in root_entity.key_attributes:
            return f'Root identifier attribute {identifier.attribute!r} must be a key attribute for entity {query.root.entity}'

    if query.aggregate not in _ALLOWED_AGGREGATES:
        return f'Unsupported aggregate: {query.aggregate}'

    if query.limit <= 0 or query.limit > _MAX_LIMIT:
        return f'Fact query limit must be between 1 and {_MAX_LIMIT}.'

    for item in query.filters:
        entity = schema_registry.entities.get(item.entity)
        if entity is None:
            return f'Unknown filter entity: {item.entity}'
        if item.attribute not in entity.attributes:
            return f'Unknown filter attribute {item.attribute!r} for entity {item.entity}'
        if item.op not in _ALLOWED_FILTER_OPS:
            return f'Unsupported filter op {item.op!r} for attribute {item.attribute!r}'

    for item in query.traversals:
        if item.direction not in {'in', 'out'}:
            return f'Unsupported traversal direction: {item.direction}'
        if item.from_entity not in schema_registry.entities:
            return f'Unknown traversal source entity: {item.from_entity}'
        if item.to_entity not in schema_registry.entities:
            return f'Unknown traversal target entity: {item.to_entity}'
        adjacency = schema_registry.adjacency.get(item.from_entity, [])
        if not any(
            edge.relation == item.relation and edge.direction == item.direction and edge.neighbor_entity == item.to_entity
            for edge in adjacency
        ):
            return (
                f'Unsupported traversal {item.from_entity} --{item.relation}/{item.direction}--> {item.to_entity} '
                'for current schema registry'
            )

    for entity_name, attributes in query.projection.items():
        entity = schema_registry.entities.get(entity_name)
        if entity is None:
            return f'Unknown projection entity: {entity_name}'
        for attribute in attributes:
            if attribute not in entity.attributes:
                return f'Unknown projection attribute {attribute!r} for entity {entity_name}'

    for item in query.sort:
        entity = schema_registry.entities.get(item.entity)
        if entity is None:
            return f'Unknown sort entity: {item.entity}'
        if item.attribute not in entity.attributes:
            return f'Unknown sort attribute {item.attribute!r} for entity {item.entity}'
        if item.direction not in _ALLOWED_SORT_DIRECTIONS:
            return f'Unsupported sort direction: {item.direction}'

    return None
