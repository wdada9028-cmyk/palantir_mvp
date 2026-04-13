from __future__ import annotations

from dataclasses import dataclass

from .schema_registry import SchemaRegistry

_ENTITY_LOOKUP_OVERRIDES = {
    'PoD': ('pod_id', 'pod_code', 'pod_name', 'pod_model'),
    'Project': ('project_id', 'project_name', 'project_code', 'name'),
    'Room': ('room_id', 'room_name', 'name'),
}


@dataclass(frozen=True, slots=True)
class AnchorLocatorConfig:
    entity: str
    lookup_attributes: tuple[str, ...]


def build_anchor_locator_registry(schema_registry: SchemaRegistry) -> dict[str, AnchorLocatorConfig]:
    registry: dict[str, AnchorLocatorConfig] = {}
    for entity_name, entity in schema_registry.entities.items():
        preferred = _ENTITY_LOOKUP_OVERRIDES.get(entity_name, ())
        available = set(entity.attributes) | set(entity.key_attributes)
        lookup_attributes = _dedupe_preserve_order([
            *[attribute for attribute in entity.key_attributes if attribute in available],
            *[attribute for attribute in preferred if attribute in available],
        ])
        if not lookup_attributes:
            continue
        registry[entity_name] = AnchorLocatorConfig(
            entity=entity_name,
            lookup_attributes=tuple(lookup_attributes),
        )
    return registry


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
