from __future__ import annotations

from pathlib import Path

from .fact_query_models import FactQueryDSL, FactQueryRoot, FactQueryTraversal
from .question_models import QuestionDSL
from .schema_registry import SchemaAdjacency, SchemaRegistry

_PROFILE_PATH = Path(__file__).resolve().with_name('event_profiles.yaml')
_DEFAULT_EVENT = 'generic_incident'


_FALLBACK_PROFILES: dict[str, dict[str, object]] = {
    'generic_incident': {'relation_priority': ['OCCURS_IN', 'ASSIGNS', 'ASSIGNED_TO', 'APPLIES_TO', 'HAS']},
    'power_outage': {'relation_priority': ['OCCURS_IN', 'ASSIGNS', 'APPLIES_TO', 'HAS', 'ASSIGNED_TO']},
    'fire': {'relation_priority': ['OCCURS_IN', 'ASSIGNS', 'APPLIES_TO', 'HAS', 'ASSIGNED_TO']},
    'delay': {'relation_priority': ['DEPENDS_ON', 'CONSTRAINS', 'APPLIES_TO', 'ASSIGNS', 'OCCURS_IN']},
    'capacity_loss': {'relation_priority': ['EXECUTES', 'ASSIGNS', 'OCCURS_IN', 'APPLIES_TO', 'HAS']},
    'access_blocked': {'relation_priority': ['OCCURS_IN', 'ASSIGNS', 'APPLIES_TO', 'HAS', 'ASSIGNED_TO']},
}


def load_event_profiles(path: str | Path = _PROFILE_PATH) -> dict[str, dict[str, object]]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return dict(_FALLBACK_PROFILES)

    payload = yaml.safe_load(Path(path).read_text(encoding='utf-8')) or {}
    events = payload.get('events')
    if not isinstance(events, dict):
        return dict(_FALLBACK_PROFILES)

    normalized: dict[str, dict[str, object]] = {}
    for key, value in events.items():
        if not isinstance(value, dict):
            continue
        relation_priority = value.get('relation_priority')
        if isinstance(relation_priority, list):
            relation_priority = [str(item).strip() for item in relation_priority if str(item).strip()]
        else:
            relation_priority = []
        normalized[str(key)] = {'relation_priority': relation_priority}

    if _DEFAULT_EVENT not in normalized:
        normalized[_DEFAULT_EVENT] = dict(_FALLBACK_PROFILES[_DEFAULT_EVENT])
    return normalized


def build_fact_queries(question: QuestionDSL, schema_registry: SchemaRegistry) -> list[FactQueryDSL]:
    anchor_entity = question.anchor.entity
    anchor_schema = schema_registry.entities.get(anchor_entity)
    if anchor_schema is None:
        return []

    profiles = load_event_profiles()
    event_type = question.scenario.event_type if question.scenario is not None else _DEFAULT_EVENT
    profile = profiles.get(event_type) or profiles.get(_DEFAULT_EVENT) or {'relation_priority': []}

    limit = max(int(question.constraints.limit), 1)

    anchor_query = FactQueryDSL(
        purpose='resolve_anchor',
        root=FactQueryRoot(entity=anchor_entity, identifier=question.anchor.identifier),
        projection={anchor_entity: list(anchor_schema.attributes)},
        limit=limit,
    )

    queries = [anchor_query]

    adjacency = list(schema_registry.adjacency.get(anchor_entity, []))
    if not adjacency:
        return queries

    ordered_adjacency = _order_adjacency(adjacency, profile)
    traversals = [
        FactQueryTraversal(
            from_entity=item.entity,
            relation=item.relation,
            direction=item.direction,
            to_entity=item.neighbor_entity,
            required=False,
        )
        for item in ordered_adjacency
    ]

    projection: dict[str, list[str]] = {anchor_entity: list(anchor_schema.key_attributes or anchor_schema.attributes)}
    for item in ordered_adjacency:
        entity = schema_registry.entities.get(item.neighbor_entity)
        if entity is None:
            continue
        projection[item.neighbor_entity] = list(entity.key_attributes or entity.attributes)

    queries.append(
        FactQueryDSL(
            purpose='collect_neighbors',
            root=FactQueryRoot(entity=anchor_entity, identifier=question.anchor.identifier),
            traversals=traversals,
            projection=projection,
            limit=limit,
        )
    )
    return queries


def _order_adjacency(values: list[SchemaAdjacency], profile: dict[str, object]) -> list[SchemaAdjacency]:
    relation_priority = profile.get('relation_priority')
    if not isinstance(relation_priority, list):
        relation_priority = []
    rank = {name: index for index, name in enumerate(relation_priority)}

    deduped: list[SchemaAdjacency] = []
    seen: set[tuple[str, str, str, str]] = set()
    for item in values:
        key = (item.entity, item.relation, item.direction, item.neighbor_entity)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    deduped.sort(
        key=lambda item: (
            rank.get(item.relation, 10_000),
            item.relation,
            item.direction,
            item.neighbor_entity,
        )
    )
    return deduped
