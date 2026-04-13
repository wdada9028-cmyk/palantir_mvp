from __future__ import annotations

from .question_models import QuestionDSL
from .schema_registry import SchemaRegistry

_ALLOWED_MODES = {'fact_lookup', 'impact_analysis', 'deadline_risk_check'}
_ALLOWED_EVENT_TYPES = {
    'power_outage',
    'fire',
    'delay',
    'capacity_loss',
    'access_blocked',
    'generic_incident',
}
_ALLOWED_GOAL_TYPES = {'list_impacts', 'yes_no_risk', 'explain_risk', 'instance_lookup', 'count'}
_ALLOWED_REASONING_SCOPES = {'anchor_only', 'expand_graph'}


def validate_question_dsl(question: QuestionDSL, schema_registry: SchemaRegistry) -> str | None:
    if question.mode not in _ALLOWED_MODES:
        return f'Unsupported question mode: {question.mode}'

    if question.reasoning_scope not in _ALLOWED_REASONING_SCOPES:
        return f'Unsupported reasoning scope: {question.reasoning_scope}'

    anchor = question.anchor
    entity = schema_registry.entities.get(anchor.entity)
    if entity is None:
        return f'Unknown anchor entity: {anchor.entity}'

    if anchor.identifier is not None:
        if anchor.identifier.attribute not in entity.attributes:
            return f'Unknown anchor identifier attribute {anchor.identifier.attribute!r} for entity {anchor.entity}'
        if anchor.identifier.attribute not in entity.key_attributes:
            return f'Anchor identifier attribute {anchor.identifier.attribute!r} must be a key attribute for entity {anchor.entity}'

    invalid_target_attributes = [item for item in question.target_attributes if item not in entity.attributes]
    if invalid_target_attributes:
        return f'Unknown target attributes for {anchor.entity}: {", ".join(invalid_target_attributes)}'

    scenario = question.scenario
    if scenario is not None and scenario.event_type not in _ALLOWED_EVENT_TYPES:
        return f'Unsupported event type: {scenario.event_type}'

    goal = question.goal
    if goal.type not in _ALLOWED_GOAL_TYPES:
        return f'Unsupported goal type: {goal.type}'

    if goal.target_entity is not None and goal.target_entity not in schema_registry.entities:
        return f'Unknown target entity: {goal.target_entity}'

    if question.constraints.limit <= 0:
        return 'Question limit must be positive.'

    return None
