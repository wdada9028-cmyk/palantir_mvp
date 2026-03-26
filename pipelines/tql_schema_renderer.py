from __future__ import annotations

from collections import defaultdict

from .tql_schema_models import TqlEntityTypeSpec, TqlSchemaSpec

_TYPE_PART_ALIASES = {
    'pod': 'PoD',
    'sla': 'SLA',
}
_ENTITY_ZH_OVERRIDES = {
    'project': '\u9879\u76ee',
    'building': '\u5927\u697c',
    'floor': '\u697c\u5c42',
    'room': '\u673a\u623f',
    'pod-position': 'PoD\u843d\u4f4d',
    'pod': 'PoD',
    'milestone': '\u91cc\u7a0b\u7891',
    'room-milestone': '\u673a\u623f\u91cc\u7a0b\u7891',
    'floor-milestone': '\u697c\u5c42\u91cc\u7a0b\u7891',
    'shipment': '\u53d1\u8d27\u5355',
    'arrival-event': '\u5230\u8d27\u4e8b\u4ef6',
    'arrival-plan': '\u5230\u8d27\u65b9\u6848',
    'activity-template': '\u6d3b\u52a8\u6a21\u677f',
    'activity-dependency-template': '\u6d3b\u52a8\u4f9d\u8d56\u6a21\u677f',
    'sla-standard': '\u6807\u51c6SLA',
    'activity-instance': '\u6d3b\u52a8\u5b9e\u4f8b',
    'pod-schedule': 'PoD\u6392\u671f',
    'crew': '\u65bd\u5de5\u961f',
    'work-assignment': '\u65bd\u5de5\u5206\u914d',
    'placement-plan': '\u843d\u4f4d\u5efa\u8bae\u65b9\u6848',
    'constraint-violation': '\u7ea6\u675f\u51b2\u7a81',
    'decision-recommendation': '\u51b3\u7b56\u5efa\u8bae',
}
_ATTRIBUTE_ZH_OVERRIDES = {
    'project-id': '\u6240\u5c5e\u9879\u76eeID',
    'project-name': '\u9879\u76ee\u540d\u79f0',
    'project-status': '\u9879\u76ee\u72b6\u6001',
    'product-type': '\u4ea7\u54c1\u7c7b\u578b',
    'cooling-mode': '\u5236\u51b7\u6a21\u5f0f',
    'project-scene': '\u9879\u76ee\u573a\u666f',
    'planned-start-date': '\u8ba1\u5212\u542f\u52a8\u65e5\u671f',
    'building-id': '\u6240\u5c5e\u5927\u697cID',
    'building-name': '\u5927\u697c\u540d\u79f0',
    'floor-id': '\u6240\u5c5e\u697c\u5c42ID',
    'floor-no': '\u697c\u5c42\u7f16\u53f7',
    'install-sequence': '\u5b89\u88c5\u987a\u5e8f',
    'room-id': '\u6240\u5c5e\u673a\u623fID',
    'room-type': '\u673a\u623f\u7c7b\u578b',
    'max-pod-capacity': '\u6700\u5927PoD\u5bb9\u91cf',
    'required-handover-pod-count': '\u8981\u6c42\u4ea4\u4ed8PoD\u6570\u91cf',
    'room-status': '\u673a\u623f\u72b6\u6001',
    'position-id': 'PoD\u843d\u4f4dID',
    'position-code': 'PoD\u843d\u4f4d\u7f16\u7801',
    'position-status': 'PoD\u843d\u4f4d\u72b6\u6001',
    'sequence-no': '\u987a\u5e8f\u53f7',
    'pod-id': 'PoD ID',
    'pod-code': 'PoD\u7f16\u7801',
    'pod-type': 'PoD\u7c7b\u578b',
    'pod-status': 'PoD\u72b6\u6001',
    'planned-arrival-time': '\u8ba1\u5212\u5230\u8d27\u65f6\u95f4',
    'actual-arrival-time': '\u5b9e\u9645\u5230\u8d27\u65f6\u95f4',
    'planned-install-start-time': '\u8ba1\u5212\u5b89\u88c5\u5f00\u59cb\u65f6\u95f4',
    'actual-install-start-time': '\u5b9e\u9645\u5b89\u88c5\u5f00\u59cb\u65f6\u95f4',
    'planned-handover-time': '\u8ba1\u5212\u4ea4\u4ed8\u65f6\u95f4',
    'actual-handover-time': '\u5b9e\u9645\u4ea4\u4ed8\u65f6\u95f4',
    'milestone-id': '\u91cc\u7a0b\u7891ID',
    'proposed-by': '\u63d0\u51fa\u65b9',
    'due-time': '\u5230\u671f\u65f6\u95f4',
    'priority': '\u4f18\u5148\u7ea7',
    'milestone-status': '\u91cc\u7a0b\u7891\u72b6\u6001',
    'target-pod-count': '\u76ee\u6807PoD\u6570\u91cf',
    'required-room-count': '\u8981\u6c42\u673a\u623f\u6570\u91cf',
    'completed-room-count': '\u5df2\u5b8c\u6210\u673a\u623f\u6570\u91cf',
    'completion-event-code': '\u5b8c\u6210\u4e8b\u4ef6\u7f16\u7801',
    'completion-event-name': '\u5b8c\u6210\u4e8b\u4ef6\u540d\u79f0',
    'shipment-id': '\u53d1\u8d27\u5355ID',
    'shipment-no': '\u53d1\u8d27\u5355\u53f7',
    'shipment-status': '\u53d1\u8d27\u5355\u72b6\u6001',
    'planned-ship-time': '\u8ba1\u5212\u53d1\u8d27\u65f6\u95f4',
    'arrival-event-id': '\u5230\u8d27\u4e8b\u4ef6ID',
    'arrival-status': '\u5230\u8d27\u72b6\u6001',
    'receiving-location': '\u6536\u8d27\u5730\u70b9',
    'confirmed-by': '\u786e\u8ba4\u4eba',
    'arrival-plan-id': '\u5230\u8d27\u65b9\u6848ID',
    'recommended-arrival-time': '\u5efa\u8bae\u5230\u8d27\u65f6\u95f4',
    'latest-safe-arrival-time': '\u6700\u665a\u5b89\u5168\u5230\u8d27\u65f6\u95f4',
    'earliest-useful-arrival-time': '\u6700\u65e9\u6709\u6548\u5230\u8d27\u65f6\u95f4',
    'backlog-risk-level': '\u79ef\u538b\u98ce\u9669\u7b49\u7ea7',
    'plan-status': '\u65b9\u6848\u72b6\u6001',
    'template-id': '\u6d3b\u52a8\u6a21\u677fID',
    'l1-code': '\u4e00\u7ea7\u7f16\u7801',
    'l1-name': '\u4e00\u7ea7\u540d\u79f0',
    'l2-code': '\u4e8c\u7ea7\u7f16\u7801',
    'l2-name': '\u4e8c\u7ea7\u540d\u79f0',
    'activity-category': '\u6d3b\u52a8\u7c7b\u522b',
    'completion-flag': '\u5b8c\u6210\u6807\u8bb0',
    'scenario-tag': '\u573a\u666f\u6807\u7b7e',
    'dependency-template-id': '\u6d3b\u52a8\u4f9d\u8d56\u6a21\u677fID',
    'dependency-type': '\u4f9d\u8d56\u7c7b\u578b',
    'sla-id': 'SLA ID',
    'standard-duration': '\u6807\u51c6\u65f6\u957f',
    'duration-unit': '\u65f6\u957f\u5355\u4f4d',
    'crew-capacity-assumption': '\u65bd\u5de5\u961f\u4ea7\u80fd\u5047\u8bbe',
    'activity-id': '\u6d3b\u52a8ID',
    'activity-status': '\u6d3b\u52a8\u72b6\u6001',
    'planned-start-time': '\u8ba1\u5212\u5f00\u59cb\u65f6\u95f4',
    'planned-finish-time': '\u8ba1\u5212\u5b8c\u6210\u65f6\u95f4',
    'latest-start-time': '\u6700\u665a\u5f00\u59cb\u65f6\u95f4',
    'latest-finish-time': '\u6700\u665a\u5b8c\u6210\u65f6\u95f4',
    'actual-start-time': '\u5b9e\u9645\u5f00\u59cb\u65f6\u95f4',
    'actual-finish-time': '\u5b9e\u9645\u5b8c\u6210\u65f6\u95f4',
    'is-milestone-anchor': '\u662f\u5426\u91cc\u7a0b\u7891\u951a\u70b9',
    'pod-schedule-id': 'PoD\u6392\u671fID',
    'schedule-type': '\u6392\u671f\u7c7b\u578b',
    'generated-at': '\u751f\u6210\u65f6\u95f4',
    'is-feasible': '\u662f\u5426\u53ef\u6267\u884c',
    'crew-id': '\u65bd\u5de5\u961fID',
    'crew-status': '\u65bd\u5de5\u961f\u72b6\u6001',
    'daily-pod-capacity': '\u6bcf\u65e5PoD\u4ea7\u80fd',
    'parallel-limit': '\u5e76\u884c\u4e0a\u9650',
    'assignment-id': '\u65bd\u5de5\u5206\u914dID',
    'assignment-date': '\u65bd\u5de5\u5206\u914d\u65e5\u671f',
    'start-time': '\u5f00\u59cb\u65f6\u95f4',
    'finish-time': '\u7ed3\u675f\u65f6\u95f4',
    'assignment-status': '\u65bd\u5de5\u5206\u914d\u72b6\u6001',
    'placement-plan-id': '\u843d\u4f4d\u5efa\u8bae\u65b9\u6848ID',
    'placement-score': '\u843d\u4f4d\u5efa\u8bae\u65b9\u6848\u8bc4\u5206',
    'violation-id': '\u51b2\u7a81ID',
    'violation-type': '\u51b2\u7a81\u7c7b\u578b',
    'severity': '\u4e25\u91cd\u7a0b\u5ea6',
    'message': '\u51b2\u7a81\u8bf4\u660e',
    'recommendation-id': '\u5efa\u8baeID',
    'recommendation-type': '\u5efa\u8bae\u7c7b\u578b',
    'recommendation-text': '\u5efa\u8bae\u5185\u5bb9',
    'confidence': '\u7f6e\u4fe1\u5ea6',
    'created-at': '\u521b\u5efa\u65f6\u95f4',
}
_RELATION_VERBS = {
    'project-building': 'HAS',
    'building-floor': 'HAS',
    'floor-room': 'HAS',
    'room-position': 'HAS',
    'project-pod': 'DELIVERS',
    'project-crew': 'HAS',
    'project-shipment': 'HAS',
    'project-room-milestone': 'HAS',
    'project-floor-milestone': 'HAS',
    'room-milestone-constraint': 'CONSTRAINS',
    'floor-milestone-constraint': 'CONSTRAINS',
    'floor-room-milestone-aggregation': 'AGGREGATES',
    'pod-building-assignment': 'ASSIGNED_TO',
    'pod-floor-assignment': 'ASSIGNED_TO',
    'pod-room-assignment': 'ASSIGNED_TO',
    'pod-position-assignment': 'ASSIGNED_TO',
    'shipment-pod': 'SHIPS',
    'pod-arrival-event': 'HAS',
    'arrival-plan-pod': 'APPLIES_TO',
    'pod-activity': 'HAS',
    'activity-template-instance': 'GENERATES',
    'activity-template-sla': 'USES',
    'activity-instance-dependency': 'DEPENDS_ON',
    'pod-schedule-pod': 'APPLIES_TO',
    'pod-schedule-activity': 'CONTAINS',
    'crew-work-assignment': 'EXECUTES',
    'work-assignment-pod': 'ASSIGNS',
    'work-assignment-room': 'OCCURS_IN',
    'work-assignment-position': 'OCCURS_AT',
    'placement-plan-pod': 'APPLIES_TO',
    'placement-plan-building': 'REFERENCES',
    'placement-plan-floor': 'REFERENCES',
    'placement-plan-room': 'REFERENCES',
    'placement-plan-position': 'REFERENCES',
    'violation-pod': 'REFERENCES',
    'violation-room-milestone': 'REFERENCES',
    'violation-floor-milestone': 'REFERENCES',
    'recommendation-arrival-plan': 'REFERENCES',
    'recommendation-placement-plan': 'REFERENCES',
    'recommendation-violation': 'REFERENCES',
}
_RELATION_ROLE_PAIRS = {}
_RELATION_FIXED_TRIPLES = {
    'template-dependency-link': [
        ('ActivityDependencyTemplate', 'DEFINES', 'ActivityInstance'),
        ('ActivityInstance', 'DEPENDS_ON', 'ActivityInstance'),
    ],
}
_RELATION_VERB_ZH = {
    'HAS': '\u5305\u542b',
    'DELIVERS': '\u4ea4\u4ed8',
    'CONSTRAINS': '\u7ea6\u675f',
    'AGGREGATES': '\u805a\u5408',
    'ASSIGNED_TO': '\u5206\u914d\u5230',
    'SHIPS': '\u53d1\u8fd0',
    'APPLIES_TO': '\u4f5c\u7528\u4e8e',
    'GENERATES': '\u751f\u6210',
    'USES': '\u4f7f\u7528',
    'DEPENDS_ON': '\u4f9d\u8d56',
    'CONTAINS': '\u5305\u542b',
    'EXECUTES': '\u6267\u884c',
    'ASSIGNS': '\u5206\u6d3e',
    'OCCURS_IN': '\u53d1\u751f\u5728',
    'OCCURS_AT': '\u53d1\u751f\u4e8e',
    'REFERENCES': '\u5f15\u7528',
    'REFERENCES_PREDECESSOR': '\u5f15\u7528\u524d\u5e8f\u6a21\u677f',
    'REFERENCES_SUCCESSOR': '\u5f15\u7528\u540e\u7eed\u6a21\u677f',
    'DEFINES': '\u5b9a\u4e49',
}
_RELATION_DIRECTION_ROLE_PAIRS = {
    'room-milestone-constraint': ('constraining-room-milestone', 'constrained-room'),
    'floor-milestone-constraint': ('constraining-floor-milestone', 'constrained-floor'),
    'floor-room-milestone-aggregation': ('owner-floor-milestone', 'member-room-milestone'),
}
_ROLE_DIRECTION_PREFIX_PAIRS = (
    ('owner-', 'owned-'),
    ('owning-', 'owned-'),
    ('constraining-', 'constrained-'),
    ('planning-', 'planned-'),
    ('predecessor-', 'successor-'),
    ('source-', 'generated-'),
    ('executing-', 'executed-'),
    ('shipping-', 'shipped-'),
)
_DESC_LABEL = '\u4e2d\u6587\u91ca\u4e49'
_SEMANTIC_LABEL = '\u8bed\u4e49\u5b9a\u4e49'
_KEY_PROPERTIES_LABEL = '\u5173\u952e\u5c5e\u6027'
_OBJECTS_HEADING = 'Object Types\uff08\u5b9e\u4f53\uff09'
_LINKS_HEADING = 'Link Types\uff08\u5173\u7cfb\uff09'
_FULLWIDTH_COLON = '\uff1a'


def render_tql_schema_as_definition_markdown(schema: TqlSchemaSpec) -> str:
    entity_by_name = {entity.name: entity for entity in schema.entities}
    relation_players = _build_relation_players(schema)
    entities = [entity for entity in schema.entities if not entity.is_abstract]
    object_zh_labels = {_type_name(entity.name): (entity.zh_label or _entity_zh_label(entity.name)) for entity in entities}

    lines: list[str] = [f'# {schema.title}', '', f'## {_OBJECTS_HEADING}', '']
    lines.extend(_render_object_type_lines(entities, schema, entity_by_name))
    lines.extend([f'## {_LINKS_HEADING}', ''])

    emitted: set[tuple[str, str, str]] = set()
    for relation_name, relation_spec in schema.relations.items():
        for source_name, verb, target_name, description in _render_relation_entries(relation_name, relation_spec.roles, relation_players, object_zh_labels):
            triple = (source_name, verb, target_name)
            if triple in emitted:
                continue
            emitted.add(triple)
            lines.append(f'- `{source_name} {verb} {target_name}`{_FULLWIDTH_COLON}{description}')

    lines.append('')
    return '\n'.join(lines)


def _render_object_type_lines(entities: list[TqlEntityTypeSpec], schema: TqlSchemaSpec, entity_by_name: dict[str, TqlEntityTypeSpec]) -> list[str]:
    lines: list[str] = []
    grouped: dict[str, list[TqlEntityTypeSpec]] = defaultdict(list)
    ungrouped: list[TqlEntityTypeSpec] = []
    has_group = any(entity.group_label for entity in entities)

    for entity in entities:
        if has_group and entity.group_label:
            grouped[entity.group_label].append(entity)
        else:
            ungrouped.append(entity)

    for entity in ungrouped:
        lines.extend(_render_entity_block(entity, schema, entity_by_name, heading_level=3))

    for group_label, group_entities in grouped.items():
        lines.append(f'### {group_label}')
        lines.append('')
        for entity in group_entities:
            lines.extend(_render_entity_block(entity, schema, entity_by_name, heading_level=4))

    return lines


def _render_entity_block(entity: TqlEntityTypeSpec, schema: TqlSchemaSpec, entity_by_name: dict[str, TqlEntityTypeSpec], *, heading_level: int) -> list[str]:
    object_name = _type_name(entity.name)
    heading_prefix = '#' * heading_level
    lines = [f'{heading_prefix} `{object_name}`', '']
    lines.append(f'{_DESC_LABEL}{_FULLWIDTH_COLON}{entity.zh_label or _entity_zh_label(entity.name)}')
    if entity.semantic_definition:
        lines.append(f'{_SEMANTIC_LABEL}{_FULLWIDTH_COLON}{entity.semantic_definition}')
    lines.append(f'{_KEY_PROPERTIES_LABEL}{_FULLWIDTH_COLON}')
    resolved_attributes = _resolve_attributes(entity.name, entity_by_name)
    for attribute_name in resolved_attributes:
        attribute = schema.attributes.get(attribute_name)
        zh_label = attribute.zh_label if attribute is not None and attribute.zh_label else _attribute_zh_label(attribute_name)
        lines.append(f'- `{_property_name(attribute_name)}`{_FULLWIDTH_COLON}{zh_label}')
    lines.append('')
    return lines


def _build_relation_players(schema: TqlSchemaSpec) -> dict[str, dict[str, list[str]]]:
    relation_players: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for entity in schema.entities:
        for play in entity.plays:
            relation_players[play.relation_name][play.role_name].append(entity.name)
    return relation_players


def _resolve_attributes(entity_name: str, entity_by_name: dict[str, TqlEntityTypeSpec]) -> list[str]:
    resolved: list[str] = []
    current = entity_by_name.get(entity_name)
    lineage: list[TqlEntityTypeSpec] = []
    while current is not None:
        lineage.append(current)
        current = entity_by_name.get(current.parent) if current.parent else None
    for entity in reversed(lineage):
        for attribute_name in entity.own_attributes:
            if attribute_name not in resolved:
                resolved.append(attribute_name)
    return resolved


def _render_relation_entries(
    relation_name: str,
    declared_roles: list[str],
    relation_players: dict[str, dict[str, list[str]]],
    object_zh_labels: dict[str, str],
) -> list[tuple[str, str, str, str]]:
    role_players = relation_players.get(relation_name, {})
    entries: list[tuple[str, str, str, str]] = []

    if relation_name in _RELATION_FIXED_TRIPLES:
        for source_name, verb, target_name in _RELATION_FIXED_TRIPLES[relation_name]:
            entries.append((source_name, verb, target_name, _relation_business_description(source_name, verb, target_name, object_zh_labels)))
        return entries

    if relation_name in _RELATION_ROLE_PAIRS:
        for source_role, target_role, verb in _RELATION_ROLE_PAIRS[relation_name]:
            for source_entity in role_players.get(source_role, []):
                for target_entity in role_players.get(target_role, []):
                    source_name = _type_name(source_entity)
                    target_name = _type_name(target_entity)
                    entries.append((source_name, verb, target_name, _relation_business_description(source_name, verb, target_name, object_zh_labels)))
        return entries

    ordered_roles = _resolve_directional_roles(relation_name, declared_roles, role_players)
    if ordered_roles is None:
        return entries

    source_role, target_role = ordered_roles
    verb = _RELATION_VERBS.get(relation_name, 'RELATES_TO')
    for source_entity in role_players.get(source_role, []):
        for target_entity in role_players.get(target_role, []):
            source_name = _type_name(source_entity)
            target_name = _type_name(target_entity)
            entries.append((source_name, verb, target_name, _relation_business_description(source_name, verb, target_name, object_zh_labels)))
    return entries


def _resolve_directional_roles(relation_name: str, declared_roles: list[str], role_players: dict[str, list[str]]) -> tuple[str, str] | None:
    available_roles = [role for role in declared_roles if role in role_players]
    if relation_name in _RELATION_DIRECTION_ROLE_PAIRS:
        source_role, target_role = _RELATION_DIRECTION_ROLE_PAIRS[relation_name]
        if source_role in role_players and target_role in role_players:
            return source_role, target_role

    for source_prefix, target_prefix in _ROLE_DIRECTION_PREFIX_PAIRS:
        source_role = next((role for role in available_roles if role.startswith(source_prefix)), None)
        target_role = next((role for role in available_roles if role.startswith(target_prefix)), None)
        if source_role and target_role:
            return source_role, target_role

    if len(available_roles) >= 2:
        return available_roles[0], available_roles[1]
    fallback_roles = list(role_players)
    if len(fallback_roles) >= 2:
        return fallback_roles[0], fallback_roles[1]
    return None


def _relation_business_description(source_name: str, verb: str, target_name: str, object_zh_labels: dict[str, str]) -> str:
    source_zh = object_zh_labels.get(source_name, source_name)
    target_zh = object_zh_labels.get(target_name, target_name)
    if verb == 'REFERENCES':
        ref_verb = '\u5173\u8054' if source_name in {'PlacementPlan', 'DecisionRecommendation', 'ConstraintViolation'} else '\u5f15\u7528'
        return f'{source_zh}{ref_verb}{target_zh}'
    verb_zh = _RELATION_VERB_ZH.get(verb, verb)
    return f'{source_zh}{verb_zh}{target_zh}'


def _entity_zh_label(entity_name: str) -> str:
    return _ENTITY_ZH_OVERRIDES.get(entity_name, _translate_hyphen_name(entity_name))


def _attribute_zh_label(attribute_name: str) -> str:
    return _ATTRIBUTE_ZH_OVERRIDES.get(attribute_name, _translate_hyphen_name(attribute_name))


def _translate_hyphen_name(raw_name: str) -> str:
    parts = raw_name.replace('_', '-').split('-')
    translated = []
    token_map = {
        'project': '\u9879\u76ee', 'building': '\u5927\u697c', 'floor': '\u697c\u5c42', 'room': '\u673a\u623f', 'pod': 'PoD', 'position': 'PoD\u843d\u4f4d',
        'milestone': '\u91cc\u7a0b\u7891', 'shipment': '\u53d1\u8d27\u5355', 'arrival': '\u5230\u8d27', 'event': '\u4e8b\u4ef6', 'plan': '\u65b9\u6848', 'activity': '\u6d3b\u52a8',
        'template': '\u6a21\u677f', 'dependency': '\u4f9d\u8d56', 'sla': 'SLA', 'standard': '\u6807\u51c6', 'crew': '\u65bd\u5de5\u961f', 'work': '\u4f5c\u4e1a',
        'assignment': '\u65bd\u5de5\u5206\u914d', 'placement': '\u843d\u4f4d\u5efa\u8bae', 'violation': '\u51b2\u7a81', 'recommendation': '\u5efa\u8bae', 'status': '\u72b6\u6001',
        'type': '\u7c7b\u578b', 'code': '\u7f16\u7801', 'name': '\u540d\u79f0', 'id': 'ID', 'scene': '\u573a\u666f', 'cooling': '\u5236\u51b7', 'mode': '\u6a21\u5f0f',
        'planned': '\u8ba1\u5212', 'actual': '\u5b9e\u9645', 'start': '\u5f00\u59cb', 'finish': '\u5b8c\u6210', 'handover': '\u4ea4\u4ed8', 'install': '\u5b89\u88c5',
        'required': '\u8981\u6c42', 'completed': '\u5df2\u5b8c\u6210', 'count': '\u6570\u91cf', 'target': '\u76ee\u6807', 'completion': '\u5b8c\u6210', 'proposed': '\u63d0\u51fa',
        'by': '\u65b9', 'due': '\u5230\u671f', 'priority': '\u4f18\u5148\u7ea7', 'receiving': '\u6536\u8d27', 'location': '\u5730\u70b9', 'confirmed': '\u786e\u8ba4',
        'recommended': '\u5efa\u8bae', 'latest': '\u6700\u665a', 'safe': '\u5b89\u5168', 'earliest': '\u6700\u65e9', 'useful': '\u6709\u6548', 'backlog': '\u79ef\u538b',
        'risk': '\u98ce\u9669', 'level': '\u7b49\u7ea7', 'duration': '\u65f6\u957f', 'unit': '\u5355\u4f4d', 'capacity': '\u4ea7\u80fd', 'assumption': '\u5047\u8bbe',
        'generated': '\u751f\u6210', 'at': '\u65f6\u95f4', 'daily': '\u6bcf\u65e5', 'parallel': '\u5e76\u884c', 'limit': '\u4e0a\u9650', 'message': '\u8bf4\u660e',
        'severity': '\u4e25\u91cd\u7a0b\u5ea6', 'text': '\u5185\u5bb9', 'confidence': '\u7f6e\u4fe1\u5ea6', 'created': '\u521b\u5efa', 'date': '\u65e5\u671f', 'no': '\u53f7',
        'flag': '\u6807\u8bb0', 'feasible': '\u53ef\u6267\u884c', 'is': '\u662f\u5426', 'product': '\u4ea7\u54c1', 'category': '\u7c7b\u522b', 'l1': '\u4e00\u7ea7', 'l2': '\u4e8c\u7ea7',
        'max': '\u6700\u5927', 'ship': '\u53d1\u8d27', 'score': '\u8bc4\u5206',
    }
    for part in parts:
        translated.append(token_map.get(part, part.upper() if part.isupper() else part.capitalize()))
    return ''.join(translated)


def _type_name(raw_name: str) -> str:
    return ''.join(_TYPE_PART_ALIASES.get(part, part.capitalize()) for part in raw_name.split('-'))


def _property_name(raw_name: str) -> str:
    return raw_name.replace('-', '_')
