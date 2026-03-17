from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Evidence:
    source_id: str
    quote: str
    start: int | None = None
    end: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'source_id': self.source_id,
            'quote': self.quote,
            'start': self.start,
            'end': self.end,
        }


@dataclass(slots=True)
class OntologyObject:
    id: str
    type: str
    name: str
    aliases: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)
    canonical_type: str | None = None
    raw_type: str | None = None
    type_aliases: list[str] = field(default_factory=list)

    def all_names(self) -> set[str]:
        return {self.name, *self.aliases}

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'aliases': list(self.aliases),
            'attributes': dict(self.attributes),
            'evidence': [item.to_dict() for item in self.evidence],
            'canonical_type': self.canonical_type,
            'raw_type': self.raw_type,
            'type_aliases': list(self.type_aliases),
        }


class Node(OntologyObject):
    pass


@dataclass(slots=True)
class OntologyRelation:
    source_id: str
    target_id: str
    relation: str
    evidence: list[Evidence] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    canonical_relation: str | None = None
    raw_relation: str | None = None
    relation_aliases: list[str] = field(default_factory=list)

    @property
    def source(self) -> str:
        return self.source_id

    @property
    def target(self) -> str:
        return self.target_id

    def to_dict(self) -> dict[str, Any]:
        return {
            'source': self.source_id,
            'target': self.target_id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation': self.relation,
            'evidence': [item.to_dict() for item in self.evidence],
            'attributes': dict(self.attributes),
            'canonical_relation': self.canonical_relation,
            'raw_relation': self.raw_relation,
            'relation_aliases': list(self.relation_aliases),
        }


class Edge(OntologyRelation):
    def __init__(
        self,
        source: str,
        target: str,
        relation: str,
        evidence: list[Evidence] | None = None,
        attributes: dict[str, Any] | None = None,
        canonical_relation: str | None = None,
        raw_relation: str | None = None,
        relation_aliases: list[str] | None = None,
    ) -> None:
        super().__init__(
            source_id=source,
            target_id=target,
            relation=relation,
            evidence=list(evidence or []),
            attributes=dict(attributes or {}),
            canonical_relation=canonical_relation,
            raw_relation=raw_relation,
            relation_aliases=list(relation_aliases or []),
        )


@dataclass(slots=True)
class OntologyGraph:
    objects: dict[str, OntologyObject] = field(default_factory=dict)
    relations: list[OntologyRelation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def nodes(self) -> dict[str, OntologyObject]:
        return self.objects

    @property
    def edges(self) -> list[OntologyRelation]:
        return self.relations

    def add_object(self, obj: OntologyObject) -> OntologyObject:
        self.objects[obj.id] = obj
        return obj

    def add_node(self, node: OntologyObject) -> OntologyObject:
        return self.add_object(node)

    def add_relation(self, relation: OntologyRelation) -> OntologyRelation:
        self.relations.append(relation)
        return relation

    def add_edge(self, edge: OntologyRelation) -> OntologyRelation:
        return self.add_relation(edge)

    def get_object(self, object_id: str) -> OntologyObject | None:
        return self.objects.get(object_id)

    def get_node(self, node_id: str) -> OntologyObject | None:
        return self.get_object(node_id)

    def get_relations(
        self,
        object_id: str,
        allowed_relations: set[str] | None = None,
        direction: str = 'out',
    ) -> list[OntologyRelation]:
        matches: list[OntologyRelation] = []
        for relation in self.relations:
            if allowed_relations and relation.relation not in allowed_relations:
                continue
            if direction == 'out' and relation.source_id == object_id:
                matches.append(relation)
            elif direction == 'in' and relation.target_id == object_id:
                matches.append(relation)
            elif direction == 'both' and (relation.source_id == object_id or relation.target_id == object_id):
                matches.append(relation)
        return matches

    def get_edges(
        self,
        node_id: str,
        allowed_relations: set[str] | None = None,
        direction: str = 'out',
    ) -> list[OntologyRelation]:
        return self.get_relations(node_id, allowed_relations=allowed_relations, direction=direction)

    def get_neighbors(
        self,
        object_id: str,
        allowed_relations: set[str] | None = None,
        direction: str = 'out',
    ) -> list[OntologyObject]:
        neighbors: list[OntologyObject] = []
        for relation in self.get_relations(object_id, allowed_relations=allowed_relations, direction=direction):
            other_id = relation.target_id if relation.source_id == object_id else relation.source_id
            obj = self.get_object(other_id)
            if obj is not None:
                neighbors.append(obj)
        return neighbors

    def to_dict(self) -> dict[str, Any]:
        objects = [obj.to_dict() for obj in self.objects.values()]
        relations = [relation.to_dict() for relation in self.relations]
        return {
            'metadata': dict(self.metadata),
            'objects': objects,
            'relations': relations,
            'nodes': objects,
            'edges': relations,
        }
