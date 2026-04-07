from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from ..models.ontology import OntologyGraph
from ..qa.template_answering import TemplateAnswer, build_instance_template_answer
from ..search.query_parser import parse_query
from .evidence_bundle_builder import build_evidence_bundle
from .evidence_models import EvidenceBundle
from .evidence_subgraph_builder import build_evidence_subgraph
from .fact_query_planner import build_fact_queries, build_propagation_queries
from .fact_query_validator import validate_fact_query_dsl
from .question_models import AnchorRef, ConstraintRef, GoalRef, IdentifierRef, QuestionDSL, ScenarioRef
from .question_validator import validate_question_dsl
from .llm_answer_context_builder import LLMAnswerContext, build_llm_answer_context
from .reasoner import build_reasoning_result
from .schema_registry import SchemaEntity, SchemaRegistry, build_schema_registry
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
    evidence_bundle: EvidenceBundle
    llm_answer_context: LLMAnswerContext
    reasoning: dict[str, object]
    fallback_answer: TemplateAnswer


_POWER_OUTAGE_KEYWORDS = ('\u65ad\u7535', '\u505c\u7535', '\u6389\u7535')
_FIRE_KEYWORDS = ('\u706b\u707e', '\u5931\u706b', '\u7740\u706b')
_DELAY_KEYWORDS = ('\u5ef6\u671f', '\u5ef6\u8bef', '\u63a8\u8fdf', '\u6ede\u540e')
_CAPACITY_LOSS_KEYWORDS = ('\u4ea7\u80fd\u4e0b\u964d', '\u8d44\u6e90\u4e0d\u8db3', '\u4eba\u624b\u4e0d\u8db3', '\u4eba\u5458\u4e0d\u8db3', '\u7f3a\u4eba', '\u5bb9\u91cf\u4e0d\u8db3')
_ACCESS_BLOCKED_KEYWORDS = ('\u5c01\u9501', '\u5c01\u95ed', '\u65e0\u6cd5\u8fdb\u5165', '\u4e0d\u53ef\u8fdb\u5165', '\u8fdb\u4e0d\u53bb')
_DEADLINE_HINTS = ('\u4ea4\u4ed8', '\u622a\u6b62\u65e5\u671f', 'deadline')
_PROPAGATION_ROUNDS = 2
_IDENTIFIER_FALLBACK_KEYS = ('id', 'room_id', 'floor_id', 'milestone_id', 'position_id', 'assignment_id', 'pod_id', 'pod_code', 'activity_id', 'pod_schedule_id')


def run_instance_qa(question: str, graph: OntologyGraph) -> InstanceQAResult:
    schema_registry = build_schema_registry(graph)
    parsed = parse_query(question)
    question_dsl = _build_question_dsl(question, parsed.normalized_query, schema_registry)
    question_validation_error = validate_question_dsl(question_dsl, schema_registry)

    fact_query_records: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []

    if question_validation_error is None:
        initial_queries = build_fact_queries(question_dsl, schema_registry)
        initial_rows = _execute_fact_queries(initial_queries, schema_registry, fact_query_records)
        all_rows.extend(initial_rows)

        current_seed_identifiers = _collect_seed_identifiers(initial_rows, schema_registry)
        seen_seed_identifiers: dict[str, set[str]] = defaultdict(set)

        for _ in range(_PROPAGATION_ROUNDS):
            pending_seed_identifiers = {
                entity: values - seen_seed_identifiers.get(entity, set())
                for entity, values in current_seed_identifiers.items()
                if values - seen_seed_identifiers.get(entity, set())
            }
            if not pending_seed_identifiers:
                break

            for entity, values in pending_seed_identifiers.items():
                seen_seed_identifiers[entity].update(values)

            propagation_queries = build_propagation_queries(question_dsl, schema_registry, pending_seed_identifiers)
            if not propagation_queries:
                break

            propagation_rows = _execute_fact_queries(propagation_queries, schema_registry, fact_query_records)
            if not propagation_rows:
                break

            all_rows.extend(propagation_rows)
            current_seed_identifiers = _collect_seed_identifiers(propagation_rows, schema_registry)

    fact_pack = map_typedb_rows_to_fact_pack(all_rows, purpose='instance_qa')
    fact_pack['metadata'].update(
        {
            'fact_query_count': len(fact_query_records),
            'question_validation_error': question_validation_error,
            'anchor': _build_anchor_metadata(question_dsl.anchor),
        }
    )

    evidence_bundle = build_evidence_bundle(
        question=question,
        schema_entities=_collect_schema_entities(question_dsl, fact_pack, schema_registry),
        positive_entities=set((fact_pack.get('instances') or {}).keys()) if isinstance(fact_pack, dict) else set(),
        empty_entities={},
        unrelated_entities={},
        omitted_entities={},
        subgraph=build_evidence_subgraph(fact_pack),
        registry=schema_registry,
        understanding=_build_evidence_understanding(question_dsl, parsed.normalized_query),
    )
    llm_answer_context = build_llm_answer_context(evidence_bundle)

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
        evidence_bundle=evidence_bundle,
        llm_answer_context=llm_answer_context,
        reasoning=reasoning,
        fallback_answer=fallback_answer,
    )


def _execute_fact_queries(
    queries,
    schema_registry: SchemaRegistry,
    fact_query_records: list[dict[str, object]],
) -> list[dict[str, object]]:
    collected_rows: list[dict[str, object]] = []
    for query in queries:
        validation_error = validate_fact_query_dsl(query, schema_registry)
        if validation_error is not None:
            fact_query_records.append({'purpose': query.purpose, 'validation_error': validation_error})
            continue

        typeql = build_typeql_query(query)
        rows, query_error = _run_typeql_readonly(typeql)
        if rows:
            collected_rows.extend(rows)
        fact_query_records.append(
            {
                'purpose': query.purpose,
                'typeql': typeql,
                'row_count': len(rows),
                'error': query_error,
            }
        )
    return collected_rows


def _collect_seed_identifiers(rows: list[dict[str, object]], schema_registry: SchemaRegistry) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if not isinstance(row, dict):
            continue
        entity = str(row.get('_entity') or row.get('entity') or '').strip()
        if not entity:
            continue
        entity_schema = schema_registry.entities.get(entity)
        identifier = _row_identifier(row, entity_schema)
        if identifier:
            result[entity].add(identifier)
    return result


def _row_identifier(row: dict[str, object], entity_schema: SchemaEntity | None) -> str | None:
    if entity_schema is not None:
        for attribute in entity_schema.key_attributes:
            value = row.get(attribute)
            if value is not None and str(value).strip():
                return str(value).strip()
    for key in _IDENTIFIER_FALLBACK_KEYS:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


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


def _build_question_dsl(question: str, normalized_query: str, schema_registry: SchemaRegistry) -> QuestionDSL:
    parsed = parse_query(normalized_query)
    anchor_entity = next(iter(schema_registry.entities), 'Room')
    for candidate in [*parsed.high_confidence_entities, *parsed.candidate_entities]:
        if candidate in schema_registry.entities:
            anchor_entity = candidate
            break

    entity_schema = schema_registry.entities.get(anchor_entity)
    identifier = None
    identifier_value = _extract_identifier_value(question)
    if entity_schema and entity_schema.key_attributes and identifier_value:
        identifier = IdentifierRef(attribute=entity_schema.key_attributes[0], value=identifier_value)

    deadline = _extract_deadline(normalized_query)
    event_type = _detect_event_type(normalized_query)
    mode = _detect_mode(normalized_query, deadline, event_type)
    goal_type = 'yes_no_risk' if mode == 'deadline_risk_check' else ('list_impacts' if mode == 'impact_analysis' else 'instance_lookup')

    return QuestionDSL(
        mode=mode,
        anchor=AnchorRef(entity=anchor_entity, identifier=identifier, surface=question),
        scenario=ScenarioRef(event_type=event_type, duration=None, start_time=None, severity=None, raw_event=''),
        goal=GoalRef(
            type=goal_type,
            target_entity=None,
            target_metric='delivery' if mode == 'deadline_risk_check' else None,
            deadline=deadline,
        ),
        constraints=ConstraintRef(statuses=[], time_window=None, limit=20),
    )


def _detect_event_type(normalized_query: str) -> str:
    if any(keyword in normalized_query for keyword in _POWER_OUTAGE_KEYWORDS):
        return 'power_outage'
    if any(keyword in normalized_query for keyword in _FIRE_KEYWORDS):
        return 'fire'
    if any(keyword in normalized_query for keyword in _DELAY_KEYWORDS):
        return 'delay'
    if any(keyword in normalized_query for keyword in _CAPACITY_LOSS_KEYWORDS):
        return 'capacity_loss'
    if any(keyword in normalized_query for keyword in _ACCESS_BLOCKED_KEYWORDS):
        return 'access_blocked'
    return 'generic_incident'


def _detect_mode(normalized_query: str, deadline: str | None, event_type: str) -> str:
    if deadline is not None or any(keyword in normalized_query for keyword in _DEADLINE_HINTS):
        return 'deadline_risk_check'
    if event_type != 'generic_incident':
        return 'impact_analysis'
    return 'fact_lookup'


def _build_anchor_metadata(anchor: AnchorRef) -> dict[str, object]:
    identifier_value = anchor.identifier.value if anchor.identifier else ''
    return {
        'entity': anchor.entity,
        'id': identifier_value,
        'identifier': (
            {'attribute': anchor.identifier.attribute, 'value': anchor.identifier.value}
            if anchor.identifier is not None
            else None
        ),
        'surface': anchor.surface,
    }


def _collect_schema_entities(question: QuestionDSL, fact_pack: dict[str, object], schema_registry: SchemaRegistry) -> list[str]:
    entities: list[str] = []
    if question.anchor.entity in schema_registry.entities:
        entities.append(question.anchor.entity)

    instances = fact_pack.get('instances') if isinstance(fact_pack, dict) else {}
    if isinstance(instances, dict):
        for entity in instances:
            if entity in schema_registry.entities:
                entities.append(entity)

    target_entity = question.goal.target_entity if question.goal is not None else None
    if target_entity and target_entity in schema_registry.entities:
        entities.append(target_entity)

    seen: set[str] = set()
    deduped: list[str] = []
    for entity in entities:
        if entity in seen:
            continue
        seen.add(entity)
        deduped.append(entity)
    return deduped


def _build_evidence_understanding(question: QuestionDSL, normalized_query: str) -> dict[str, object]:
    anchor = _build_anchor_metadata(question.anchor)
    return {
        'mode': question.mode,
        'normalized_query': normalized_query,
        'anchor': {
            'entity': anchor.get('entity', ''),
            'id': anchor.get('id', ''),
            'identifier': anchor.get('identifier'),
            'surface': anchor.get('surface', ''),
        },
        'scenario': (
            {
                'event_type': question.scenario.event_type,
                'raw_event': question.scenario.raw_event,
            }
            if question.scenario is not None
            else None
        ),
    }


def _extract_identifier_value(question: str) -> str | None:
    match = re.search(r'([0-9A-Za-z_-]{2,})', question)
    return match.group(1) if match else None


def _extract_deadline(normalized_query: str) -> str | None:
    match = re.search(r'(20\d{2})[-/](\d{1,2})[-/](\d{1,2})', normalized_query)
    if match:
        year, month, day = match.groups()
        return f'{int(year):04d}-{int(month):02d}-{int(day):02d}'
    match = re.search(r'(\d{1,2})[/-](\d{1,2})', normalized_query)
    if match and any(keyword in normalized_query for keyword in _DEADLINE_HINTS):
        month, day = match.groups()
        return f'2026-{int(month):02d}-{int(day):02d}'
    return None
