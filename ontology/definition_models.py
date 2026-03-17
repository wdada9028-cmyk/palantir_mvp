from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PropertySpec:
    name: str
    description: str
    line_no: int


@dataclass(slots=True)
class NamedValueSpec:
    name: str
    description: str
    line_no: int


@dataclass(slots=True)
class ObjectTypeSpec:
    name: str
    group: str
    chinese_description: str = ''
    semantic_definition: str | None = None
    key_properties: list[PropertySpec] = field(default_factory=list)
    status_values: list[NamedValueSpec] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    suggested_violation_types: list[NamedValueSpec] = field(default_factory=list)
    source_start_line: int | None = None
    source_end_line: int | None = None


@dataclass(slots=True)
class RelationSpec:
    source_type: str
    relation: str
    target_type: str
    description: str
    group: str
    line_no: int


@dataclass(slots=True)
class DerivedMetricSpec:
    name: str
    description: str
    line_no: int


@dataclass(slots=True)
class OntologyDefinitionSpec:
    title: str = ''
    source_file: str | None = None
    boundaries: list[str] = field(default_factory=list)
    mainline: list[str] = field(default_factory=list)
    object_types: list[ObjectTypeSpec] = field(default_factory=list)
    relations: list[RelationSpec] = field(default_factory=list)
    derived_metrics: list[DerivedMetricSpec] = field(default_factory=list)
    optional_properties: list[PropertySpec] = field(default_factory=list)
    optional_property_notes: list[str] = field(default_factory=list)
