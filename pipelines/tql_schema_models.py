from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TqlAttributeSpec:
    name: str
    value_type: str
    zh_label: str | None = None


@dataclass(slots=True)
class TqlRelationTypeSpec:
    name: str
    roles: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TqlEntityPlaySpec:
    relation_name: str
    role_name: str


@dataclass(slots=True)
class TqlEntityTypeSpec:
    name: str
    parent: str | None = None
    own_attributes: list[str] = field(default_factory=list)
    plays: list[TqlEntityPlaySpec] = field(default_factory=list)
    is_abstract: bool = False
    group_label: str | None = None
    zh_label: str | None = None
    semantic_definition: str | None = None


@dataclass(slots=True)
class TqlSchemaSpec:
    title: str
    attributes: dict[str, TqlAttributeSpec] = field(default_factory=dict)
    relations: dict[str, TqlRelationTypeSpec] = field(default_factory=dict)
    entities: list[TqlEntityTypeSpec] = field(default_factory=list)
