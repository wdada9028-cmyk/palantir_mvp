from __future__ import annotations

from pathlib import Path

from .fact_query_models import FactQueryDSL, FactQueryRoot, FactQueryTraversal
from .question_models import IdentifierRef, QuestionDSL
from .schema_registry import SchemaAdjacency, SchemaRegistry

_PROFILE_PATH = Path(__file__).resolve().with_name('event_profiles.yaml')
_DEFAULT_EVENT = 'generic_incident'


_FALLBACK_IMPACT_PROPAGATION = {
    'PoDPosition': [
        {'relation': 'ASSIGNED_TO', 'neighbor_entity': 'PoD'},
        {'relation': 'OCCURS_AT', 'neighbor_entity': 'WorkAssignment'},
    ],
    'WorkAssignment': [
        {'relation': 'ASSIGNS', 'neighbor_entity': 'PoD'},
    ],
    'PoD': [
        {'relation': 'HAS', 'neighbor_entity': 'ActivityInstance'},
        {'relation': 'APPLIES_TO', 'neighbor_entity': 'PoDSchedule'},
    ],
}

_FALLBACK_PROFILES: dict[str, dict[str, object]] = {
    'generic_incident': {'relation_priority': ['OCCURS_IN', 'ASSIGNS', 'ASSIGNED_TO', 'APPLIES_TO', 'HAS'], 'impact_propagation': {}},
    'power_outage': {'relation_priority': ['OCCURS_IN', 'ASSIGNS', 'APPLIES_TO', 'HAS', 'ASSIGNED_TO'], 'impact_propagation': _FALLBACK_IMPACT_PROPAGATION},
    'fire': {'relation_priority': ['OCCURS_IN', 'ASSIGNS', 'APPLIES_TO', 'HAS', 'ASSIGNED_TO'], 'impact_propagation': _FALLBACK_IMPACT_PROPAGATION},
    'delay': {'relation_priority': ['DEPENDS_ON', 'CONSTRAINS', 'APPLIES_TO', 'ASSIGNS', 'OCCURS_IN'], 'impact_propagation': {}},
    'capacity_loss': {'relation_priority': ['EXECUTES', 'ASSIGNS', 'OCCURS_IN', 'APPLIES_TO', 'HAS'], 'impact_propagation': {}},
    'access_blocked': {'relation_priority': ['OCCURS_IN', 'ASSIGNS', 'APPLIES_TO', 'HAS', 'ASSIGNED_TO'], 'impact_propagation': _FALLBACK_IMPACT_PROPAGATION},
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
        impact_propagation = _normalize_impact_propagation(value.get('impact_propagation'))
        normalized[str(key)] = {'relation_priority': relation_priority, 'impact_propagation': impact_propagation}

    if _DEFAULT_EVENT not in normalized:
        normalized[_DEFAULT_EVENT] = dict(_FALLBACK_PROFILES[_DEFAULT_EVENT])
    return normalized


def build_fact_queries(question: QuestionDSL, schema_registry: SchemaRegistry) -> list[FactQueryDSL]:
    anchor_entity = question.anchor.entity
    anchor_schema = schema_registry.entities.get(anchor_entity)
    if anchor_schema is None:
        return []

    profile = _event_profile(question)
    limit = max(int(question.constraints.limit), 1)

    queries: list[FactQueryDSL] = [
        FactQueryDSL(
            purpose='resolve_anchor',
            root=FactQueryRoot(entity=anchor_entity, identifier=question.anchor.identifier),
            projection={anchor_entity: list(anchor_schema.attributes)},
            limit=limit,
        )
    ]

    if question.reasoning_scope == 'anchor_only':
        return queries

    adjacency = list(schema_registry.adjacency.get(anchor_entity, []))
    if not adjacency:
        return queries

    ordered_adjacency = _order_adjacency(adjacency, profile)
    for item in ordered_adjacency:
        neighbor_schema = schema_registry.entities.get(item.neighbor_entity)
        if neighbor_schema is None:
            continue

        queries.append(
            FactQueryDSL(
                purpose='collect_neighbors',
                root=FactQueryRoot(entity=anchor_entity, identifier=question.anchor.identifier),
                traversals=[
                    FactQueryTraversal(
                        from_entity=item.entity,
                        relation=item.relation,
                        direction=item.direction,
                        to_entity=item.neighbor_entity,
                        typedb_relation=item.typedb_relation,
                        entity_role=item.entity_role,
                        neighbor_role=item.neighbor_role,
                        required=False,
                    )
                ],
                projection={
                    anchor_entity: list(anchor_schema.key_attributes or anchor_schema.attributes),
                    item.neighbor_entity: list(neighbor_schema.key_attributes or neighbor_schema.attributes),
                },
                limit=limit,
            )
        )

    return queries


def build_propagation_queries(
    question: QuestionDSL,
    schema_registry: SchemaRegistry,
    seed_identifiers: dict[str, set[str]],
) -> list[FactQueryDSL]:
    if question.reasoning_scope == 'anchor_only':
        return []

    profile = _event_profile(question)
    impact_propagation = profile.get('impact_propagation') if isinstance(profile, dict) else {}
    if not isinstance(impact_propagation, dict):
        return []

    limit = max(int(question.constraints.limit), 1)
    queries: list[FactQueryDSL] = []

    for source_entity, identifiers in seed_identifiers.items():
        if not identifiers:
            continue
        entity_schema = schema_registry.entities.get(source_entity)
        if entity_schema is None or not entity_schema.key_attributes:
            continue
        rules = impact_propagation.get(source_entity)
        if not isinstance(rules, list):
            continue

        adjacency = list(schema_registry.adjacency.get(source_entity, []))
        for identifier_value in sorted(identifiers):
            root = FactQueryRoot(
                entity=source_entity,
                identifier=IdentifierRef(attribute=entity_schema.key_attributes[0], value=identifier_value),
            )
            for rule in rules:
                if not isinstance(rule, dict):
                    continue
                relation = str(rule.get('relation') or '').strip()
                neighbor_entity = str(rule.get('neighbor_entity') or '').strip()
                item = _find_adjacency(adjacency, relation, neighbor_entity)
                if item is None:
                    continue
                neighbor_schema = schema_registry.entities.get(item.neighbor_entity)
                if neighbor_schema is None:
                    continue
                queries.append(
                    FactQueryDSL(
                        purpose='propagate_neighbors',
                        root=root,
                        traversals=[
                            FactQueryTraversal(
                                from_entity=item.entity,
                                relation=item.relation,
                                direction=item.direction,
                                to_entity=item.neighbor_entity,
                                typedb_relation=item.typedb_relation,
                                entity_role=item.entity_role,
                                neighbor_role=item.neighbor_role,
                                required=False,
                            )
                        ],
                        projection={
                            source_entity: list(entity_schema.key_attributes or entity_schema.attributes),
                            item.neighbor_entity: list(neighbor_schema.key_attributes or neighbor_schema.attributes),
                        },
                        limit=limit,
                    )
                )

    return _dedupe_queries(queries)


def _event_profile(question: QuestionDSL) -> dict[str, object]:
    profiles = load_event_profiles()
    event_type = question.scenario.event_type if question.scenario is not None else _DEFAULT_EVENT
    return profiles.get(event_type) or profiles.get(_DEFAULT_EVENT) or {'relation_priority': [], 'impact_propagation': {}}


def _normalize_impact_propagation(raw: object) -> dict[str, list[dict[str, str]]]:
    if not isinstance(raw, dict):
        return {}
    result: dict[str, list[dict[str, str]]] = {}
    for key, value in raw.items():
        if not isinstance(value, list):
            continue
        rules: list[dict[str, str]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            relation = str(item.get('relation') or '').strip()
            neighbor_entity = str(item.get('neighbor_entity') or '').strip()
            if relation and neighbor_entity:
                rules.append({'relation': relation, 'neighbor_entity': neighbor_entity})
        result[str(key)] = rules
    return result


def _find_adjacency(values: list[SchemaAdjacency], relation: str, neighbor_entity: str) -> SchemaAdjacency | None:
    for item in values:
        if item.relation == relation and item.neighbor_entity == neighbor_entity:
            return item
    return None


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


def _dedupe_queries(values: list[FactQueryDSL]) -> list[FactQueryDSL]:
    seen: set[tuple[str, str, str, str]] = set()
    result: list[FactQueryDSL] = []
    for item in values:
        traversal = item.traversals[0] if item.traversals else None
        key = (
            item.root.entity,
            item.root.identifier.value if item.root.identifier else '',
            traversal.relation if traversal else '',
            traversal.to_entity if traversal else '',
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
