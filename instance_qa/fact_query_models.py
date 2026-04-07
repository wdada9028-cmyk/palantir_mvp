from __future__ import annotations

from dataclasses import dataclass, field

from .question_models import IdentifierRef


@dataclass(frozen=True, slots=True)
class FactQueryRoot:
    entity: str
    identifier: IdentifierRef | None = None


@dataclass(frozen=True, slots=True)
class FactQueryFilter:
    entity: str
    attribute: str
    op: str
    value: object


@dataclass(frozen=True, slots=True)
class FactQueryTraversal:
    from_entity: str
    relation: str
    direction: str
    to_entity: str
    typedb_relation: str | None = None
    entity_role: str | None = None
    neighbor_role: str | None = None
    required: bool = True


@dataclass(frozen=True, slots=True)
class FactQuerySort:
    entity: str
    attribute: str
    direction: str = 'asc'


@dataclass(frozen=True, slots=True)
class FactQueryDSL:
    purpose: str
    root: FactQueryRoot
    filters: list[FactQueryFilter] = field(default_factory=list)
    traversals: list[FactQueryTraversal] = field(default_factory=list)
    projection: dict[str, list[str]] = field(default_factory=dict)
    aggregate: str | None = None
    sort: list[FactQuerySort] = field(default_factory=list)
    limit: int = 20
