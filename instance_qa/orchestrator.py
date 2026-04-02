from __future__ import annotations

import re
from dataclasses import dataclass

from ..models.ontology import OntologyGraph
from ..qa.template_answering import TemplateAnswer, build_instance_template_answer
from ..search.query_parser import parse_query
from .fact_query_planner import build_fact_queries
from .fact_query_validator import validate_fact_query_dsl
from .question_models import AnchorRef, ConstraintRef, GoalRef, IdentifierRef, QuestionDSL, ScenarioRef
from .question_validator import validate_question_dsl
from .reasoner import build_reasoning_result
from .schema_registry import build_schema_registry
from .typeql_builder import build_typeql_query
from .typedb_client import TypeDBClient, TypeDBConnectionError, TypeDBQueryError, load_typedb_config
from .typedb_result_mapper import map_typedb_rows_to_fact_pack


@dataclass(slots=True)
class InstanceQAResult:
    question: str
    normalized_query: str
    question_dsl: QuestionDSL
    question_validation_error: str | None
    fact_queries: list[dict[str, object]]
    fact_pack: dict[str, object]
    reasoning: dict[str, object]
    fallback_answer: TemplateAnswer


def run_instance_qa(question: str, graph: OntologyGraph) -> InstanceQAResult:
    schema_registry = build_schema_registry(graph)
    parsed = parse_query(question)
    question_dsl = _build_question_dsl(question, parsed.normalized_query, schema_registry)
    question_validation_error = validate_question_dsl(question_dsl, schema_registry)

    fact_query_records: list[dict[str, object]] = []
    merged_instances: dict[str, list[dict[str, object]]] = {}

    if question_validation_error is None:
        for query in build_fact_queries(question_dsl, schema_registry):
            validation_error = validate_fact_query_dsl(query, schema_registry)
            if validation_error is not None:
                fact_query_records.append({'purpose': query.purpose, 'validation_error': validation_error})
                continue

            typeql = build_typeql_query(query)
            rows, query_error = _run_typeql_readonly(typeql)
            fact_pack = map_typedb_rows_to_fact_pack(rows, purpose=query.purpose)
            for entity, items in fact_pack.get('instances', {}).items():
                merged_instances.setdefault(entity, []).extend(items)
            fact_query_records.append(
                {
                    'purpose': query.purpose,
                    'typeql': typeql,
                    'row_count': len(rows),
                    'error': query_error,
                }
            )

    fact_pack = {
        'instances': merged_instances,
        'counts': {entity: len(items) for entity, items in merged_instances.items()},
        'metadata': {
            'fact_query_count': len(fact_query_records),
            'question_validation_error': question_validation_error,
        },
    }

    reasoning = build_reasoning_result(
        fact_pack,
        mode=question_dsl.mode,
        deadline=question_dsl.goal.deadline,
    )

    fallback_answer = build_instance_template_answer(question, fact_pack, reasoning)

    return InstanceQAResult(
        question=question,
        normalized_query=parsed.normalized_query,
        question_dsl=question_dsl,
        question_validation_error=question_validation_error,
        fact_queries=fact_query_records,
        fact_pack=fact_pack,
        reasoning=reasoning,
        fallback_answer=fallback_answer,
    )


def _run_typeql_readonly(typeql: str) -> tuple[list[dict[str, object]], str | None]:
    config = load_typedb_config()
    if config is None:
        return [], 'typedb_not_configured'

    client = TypeDBClient(config)
    try:
        client.connect()
        rows = client.execute_readonly(typeql)
        return rows, None
    except (TypeDBConnectionError, TypeDBQueryError) as exc:
        return [], f'{type(exc).__name__}: {exc}'
    finally:
        client.close()


def _build_question_dsl(question: str, normalized_query: str, schema_registry) -> QuestionDSL:
    anchor_entity = next(iter(schema_registry.entities), 'Room')
    parsed = parse_query(normalized_query)
    for candidate in [*parsed.high_confidence_entities, *parsed.candidate_entities]:
        if candidate in schema_registry.entities:
            anchor_entity = candidate
            break

    entity_schema = schema_registry.entities.get(anchor_entity)
    identifier = None
    if entity_schema and entity_schema.key_attributes:
        identifier = IdentifierRef(attribute=entity_schema.key_attributes[0], value=_extract_identifier_value(question) or 'unknown')

    event_type = _detect_event_type(normalized_query)
    mode = 'deadline_risk_check' if _extract_deadline(normalized_query) else ('impact_analysis' if '??' in normalized_query else 'fact_lookup')
    goal_type = 'yes_no_risk' if mode == 'deadline_risk_check' else ('list_impacts' if mode == 'impact_analysis' else 'instance_lookup')

    return QuestionDSL(
        mode=mode,
        anchor=AnchorRef(entity=anchor_entity, identifier=identifier, surface=question),
        scenario=ScenarioRef(event_type=event_type, duration=None, start_time=None, severity=None, raw_event=''),
        goal=GoalRef(type=goal_type, target_entity=None, target_metric='delivery' if mode == 'deadline_risk_check' else None, deadline=_extract_deadline(normalized_query)),
        constraints=ConstraintRef(statuses=[], time_window=None, limit=20),
    )


def _detect_event_type(normalized_query: str) -> str:
    if '??' in normalized_query:
        return 'power_outage'
    if '??' in normalized_query:
        return 'fire'
    if '??' in normalized_query or '??' in normalized_query:
        return 'delay'
    if '??' in normalized_query or '??' in normalized_query:
        return 'capacity_loss'
    if '??' in normalized_query or '????' in normalized_query:
        return 'access_blocked'
    return 'generic_incident'


def _extract_identifier_value(question: str) -> str | None:
    match = re.search(r'([0-9A-Za-z_-]{2,})', question)
    return match.group(1) if match else None


def _extract_deadline(normalized_query: str) -> str | None:
    match = re.search(r'(20\d{2})[-/](\d{1,2})[-/](\d{1,2})', normalized_query)
    if match:
        year, month, day = match.groups()
        return f'{int(year):04d}-{int(month):02d}-{int(day):02d}'
    match = re.search(r'(\d{1,2})[/?](\d{1,2})', normalized_query)
    if match:
        month, day = match.groups()
        return f'2026-{int(month):02d}-{int(day):02d}'
    return None
