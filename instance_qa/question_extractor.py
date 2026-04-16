from __future__ import annotations

import json

from .question_models import AnchorRef, ConstraintRef, DurationRef, GoalRef, IdentifierRef, QuestionDSL, ScenarioRef
from .schema_registry import SchemaRegistry

_ALLOWED_MODES = ('fact_lookup', 'impact_analysis', 'deadline_risk_check')
_ALLOWED_EVENT_TYPES = (
    'power_outage',
    'fire',
    'delay',
    'capacity_loss',
    'access_blocked',
    'generic_incident',
)
_ALLOWED_GOAL_TYPES = ('list_impacts', 'yes_no_risk', 'explain_risk', 'instance_lookup', 'count')


def parse_question_dsl_payload(payload: dict[str, object]) -> QuestionDSL:
    anchor_payload = payload.get('anchor') if isinstance(payload, dict) else None
    if not isinstance(anchor_payload, dict):
        raise ValueError('Question DSL payload is missing anchor.')
    identifier_payload = anchor_payload.get('identifier')
    identifier = None
    if isinstance(identifier_payload, dict):
        identifier = IdentifierRef(
            attribute=str(identifier_payload.get('attribute', '') or '').strip(),
            value=str(identifier_payload.get('value', '') or '').strip(),
        )

    scenario_payload = payload.get('scenario') if isinstance(payload, dict) else None
    scenario = None
    if isinstance(scenario_payload, dict):
        duration_payload = scenario_payload.get('duration')
        duration = None
        if isinstance(duration_payload, dict):
            duration = DurationRef(
                value=int(duration_payload.get('value', 0) or 0),
                unit=str(duration_payload.get('unit', '') or '').strip(),
            )
        scenario = ScenarioRef(
            event_type=str(scenario_payload.get('event_type', '') or '').strip(),
            duration=duration,
            start_time=_optional_text(scenario_payload.get('start_time')),
            severity=_optional_text(scenario_payload.get('severity')),
            raw_event=str(scenario_payload.get('raw_event', '') or '').strip(),
        )

    goal_payload = payload.get('goal') if isinstance(payload, dict) else None
    if not isinstance(goal_payload, dict):
        raise ValueError('Question DSL payload is missing goal.')

    constraints_payload = payload.get('constraints') if isinstance(payload, dict) else None
    statuses: list[str] = []
    time_window = None
    limit = 20
    if isinstance(constraints_payload, dict):
        raw_statuses = constraints_payload.get('statuses')
        if isinstance(raw_statuses, list):
            statuses = [str(item).strip() for item in raw_statuses if str(item).strip()]
        time_window = _optional_text(constraints_payload.get('time_window'))
        raw_limit = constraints_payload.get('limit', 20)
        limit = int(raw_limit or 20)

    return QuestionDSL(
        mode=str(payload.get('mode', '') or '').strip(),
        anchor=AnchorRef(
            entity=str(anchor_payload.get('entity', '') or '').strip(),
            identifier=identifier,
            surface=str(anchor_payload.get('surface', '') or '').strip(),
        ),
        scenario=scenario,
        goal=GoalRef(
            type=str(goal_payload.get('type', '') or '').strip(),
            target_entity=_optional_text(goal_payload.get('target_entity')),
            target_metric=_optional_text(goal_payload.get('target_metric')),
            deadline=_optional_text(goal_payload.get('deadline')),
        ),
        constraints=ConstraintRef(statuses=statuses, time_window=time_window, limit=limit),
    )


def build_question_extraction_prompt(schema_registry: SchemaRegistry, raw_query: str) -> str:
    payload = {
        'allowed_modes': list(_ALLOWED_MODES),
        'allowed_event_types': list(_ALLOWED_EVENT_TYPES),
        'allowed_goal_types': list(_ALLOWED_GOAL_TYPES),
        'allowed_entities': sorted(schema_registry.entities),
        'query': raw_query,
    }
    return (
        'Read the user question and return only JSON matching the controlled Question DSL. '
        'Do not invent entities, event types, or goal types outside the allowed lists.\n\n'
        f'{json.dumps(payload, ensure_ascii=False, indent=2)}'
    )


def _optional_text(value: object) -> str | None:
    text = str(value or '').strip()
    return text or None
