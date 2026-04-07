from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..models.ontology import OntologyGraph
from ..pipelines.tql_schema_extractor import extract_tql_schema


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
    typedb_relation: str | None = None
    source_role: str | None = None
    target_role: str | None = None


@dataclass(frozen=True, slots=True)
class SchemaAdjacency:
    entity: str
    relation: str
    direction: str
    neighbor_entity: str
    typedb_relation: str | None = None
    entity_role: str | None = None
    neighbor_role: str | None = None


@dataclass(frozen=True, slots=True)
class SchemaRegistry:
    entities: dict[str, SchemaEntity]
    relations: list[SchemaRelation]
    adjacency: dict[str, list[SchemaAdjacency]]


@dataclass(frozen=True, slots=True)
class _PhysicalPair:
    relation: str
    left_entity: str
    right_entity: str
    left_role: str
    right_role: str


_ENTITY_TOKEN_OVERRIDES = {'pod': 'PoD', 'sla': 'SLA'}


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

    physical_pair_index = _build_physical_pair_index(graph)
    has_physical_index = bool(physical_pair_index)

    relations: list[SchemaRelation] = []
    for relation in graph.relations:
        source_entity = _entity_name_from_object_id(relation.source_id)
        target_entity = _entity_name_from_object_id(relation.target_id)
        if source_entity not in entities or target_entity not in entities:
            continue

        physical_pair = _resolve_physical_pair(physical_pair_index, source_entity, target_entity)
        relations.append(
            SchemaRelation(
                relation=relation.relation,
                source_entity=source_entity,
                target_entity=target_entity,
                typedb_relation=physical_pair.relation if physical_pair else None,
                source_role=physical_pair.left_role if physical_pair else None,
                target_role=physical_pair.right_role if physical_pair else None,
            )
        )

        if physical_pair is None and has_physical_index:
            continue

        adjacency[source_entity].append(
            SchemaAdjacency(
                entity=source_entity,
                relation=relation.relation,
                direction='out',
                neighbor_entity=target_entity,
                typedb_relation=physical_pair.relation if physical_pair else None,
                entity_role=physical_pair.left_role if physical_pair else None,
                neighbor_role=physical_pair.right_role if physical_pair else None,
            )
        )
        adjacency[target_entity].append(
            SchemaAdjacency(
                entity=target_entity,
                relation=relation.relation,
                direction='in',
                neighbor_entity=source_entity,
                typedb_relation=physical_pair.relation if physical_pair else None,
                entity_role=physical_pair.right_role if physical_pair else None,
                neighbor_role=physical_pair.left_role if physical_pair else None,
            )
        )

    for entity_name in adjacency:
        adjacency[entity_name] = _dedupe_adjacency(adjacency[entity_name])

    return SchemaRegistry(entities=entities, relations=relations, adjacency=adjacency)


def _build_physical_pair_index(graph: OntologyGraph) -> dict[tuple[str, str], list[_PhysicalPair]]:
    raw_path = str(graph.metadata.get('typedb_schema_input_file') or '').strip()
    if not raw_path:
        return {}

    path = Path(raw_path)
    if path.suffix.lower() != '.tql' or not path.exists():
        return {}

    schema = extract_tql_schema(path.read_text(encoding='utf-8'), source_file=str(path))
    plays_by_relation: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for entity in schema.entities:
        entity_name = _normalize_entity_name(entity.name)
        for play in entity.plays:
            plays_by_relation[play.relation_name].append((entity_name, play.role_name))

    index: dict[tuple[str, str], list[_PhysicalPair]] = defaultdict(list)
    for relation_name, players in plays_by_relation.items():
        for left_index, (left_entity, left_role) in enumerate(players):
            for right_index, (right_entity, right_role) in enumerate(players):
                if left_index == right_index:
                    continue
                index[(left_entity, right_entity)].append(
                    _PhysicalPair(
                        relation=relation_name,
                        left_entity=left_entity,
                        right_entity=right_entity,
                        left_role=left_role,
                        right_role=right_role,
                    )
                )

    return {key: _dedupe_physical_pairs(values) for key, values in index.items()}


def _resolve_physical_pair(
    physical_pair_index: dict[tuple[str, str], list[_PhysicalPair]],
    source_entity: str,
    target_entity: str,
) -> _PhysicalPair | None:
    candidates = physical_pair_index.get((source_entity, target_entity), [])
    if len(candidates) == 1:
        return candidates[0]
    return None


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


def _normalize_entity_name(value: str) -> str:
    tokens = [part for part in str(value or '').replace('-', '_').split('_') if part]
    return ''.join(_ENTITY_TOKEN_OVERRIDES.get(token.lower(), token.capitalize()) for token in tokens)


def _dedupe_physical_pairs(values: list[_PhysicalPair]) -> list[_PhysicalPair]:
    seen: set[tuple[str, str, str, str, str]] = set()
    result: list[_PhysicalPair] = []
    for item in values:
        key = (item.relation, item.left_entity, item.right_entity, item.left_role, item.right_role)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _dedupe_adjacency(values: list[SchemaAdjacency]) -> list[SchemaAdjacency]:
    seen: set[tuple[str, str, str, str, str | None, str | None, str | None]] = set()
    result: list[SchemaAdjacency] = []
    for item in values:
        key = (
            item.entity,
            item.relation,
            item.direction,
            item.neighbor_entity,
            item.typedb_relation,
            item.entity_role,
            item.neighbor_role,
        )
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
