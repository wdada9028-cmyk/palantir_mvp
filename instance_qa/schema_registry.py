from __future__ import annotations

from dataclasses import dataclass, field

from ..models.ontology import OntologyGraph


@dataclass(frozen=True, slots=True)
class SchemaEntity:
    name: str
    object_id: str
    attributes: list[str] = field(default_factory=list)
    key_attributes: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SchemaRelation:
    relation: str
    source_entity: str
    target_entity: str


@dataclass(frozen=True, slots=True)
class SchemaAdjacency:
    entity: str
    relation: str
    direction: str
    neighbor_entity: str


@dataclass(frozen=True, slots=True)
class SchemaRegistry:
    entities: dict[str, SchemaEntity]
    relations: list[SchemaRelation]
    adjacency: dict[str, list[SchemaAdjacency]]


def build_schema_registry(graph: OntologyGraph) -> SchemaRegistry:
    entities: dict[str, SchemaEntity] = {}
    adjacency: dict[str, list[SchemaAdjacency]] = {}

    for obj in graph.objects.values():
        if obj.type != 'ObjectType':
            continue
        entity_name = obj.name
        key_attributes = _extract_key_attributes(obj.attributes.get('key_properties'))
        attributes = _extract_attributes(obj.attributes.get('key_properties'))
        entities[entity_name] = SchemaEntity(
            name=entity_name,
            object_id=obj.id,
            attributes=attributes,
            key_attributes=key_attributes,
        )
        adjacency.setdefault(entity_name, [])

    relations: list[SchemaRelation] = []
    for relation in graph.relations:
        source_entity = _entity_name_from_object_id(relation.source_id)
        target_entity = _entity_name_from_object_id(relation.target_id)
        if source_entity not in entities or target_entity not in entities:
            continue

        relations.append(
            SchemaRelation(
                relation=relation.relation,
                source_entity=source_entity,
                target_entity=target_entity,
            )
        )

        adjacency[source_entity].append(
            SchemaAdjacency(
                entity=source_entity,
                relation=relation.relation,
                direction='out',
                neighbor_entity=target_entity,
            )
        )
        adjacency[target_entity].append(
            SchemaAdjacency(
                entity=target_entity,
                relation=relation.relation,
                direction='in',
                neighbor_entity=source_entity,
            )
        )

    for entity_name in adjacency:
        adjacency[entity_name] = _dedupe_adjacency(adjacency[entity_name])

    return SchemaRegistry(entities=entities, relations=relations, adjacency=adjacency)


def _extract_attributes(raw_key_properties: object) -> list[str]:
    if not isinstance(raw_key_properties, list):
        return []
    names: list[str] = []
    for item in raw_key_properties:
        if not isinstance(item, dict):
            continue
        name = str(item.get('name', '') or '').strip()
        if not name:
            continue
        names.append(name)
    return _dedupe_preserve_order(names)


def _extract_key_attributes(raw_key_properties: object) -> list[str]:
    return _extract_attributes(raw_key_properties)


def _entity_name_from_object_id(object_id: str) -> str:
    return object_id.split(':', 1)[-1]


def _dedupe_adjacency(values: list[SchemaAdjacency]) -> list[SchemaAdjacency]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[SchemaAdjacency] = []
    for item in values:
        key = (item.entity, item.relation, item.direction, item.neighbor_entity)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
