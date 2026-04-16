from __future__ import annotations

import os
import re
from pathlib import Path
from contextlib import nullcontext

from collections import defaultdict
from dataclasses import dataclass

from .anchor_search_index import build_anchor_search_index, search_anchor_candidates
from ..models.ontology import OntologyGraph
from ..qa.template_answering import TemplateAnswer, build_instance_template_answer
from ..search.ontology_query_engine import retrieve_ontology_evidence
from ..search.ontology_query_models import EvidenceItem, OntologyEvidenceBundle, RetrievalStep, SearchTrace
from ..search.query_parser import parse_query
from .anchor_candidate_context_builder import build_anchor_candidate_context
from .anchor_candidate_ranker import resolve_anchor_candidate_rank
from .anchor_candidate_resolver import resolve_anchor_candidates
from .anchor_locator_registry import build_anchor_locator_registry
from .anchor_resolution_policy import apply_anchor_resolution_policy
from .evidence_bundle_builder import build_evidence_bundle
from .evidence_models import EvidenceBundle
from .evidence_subgraph_builder import build_evidence_subgraph
from .fact_query_planner import build_fact_queries, build_propagation_queries
from .fact_query_validator import validate_fact_query_dsl
from .question_models import AnchorRef, ConstraintRef, GoalRef, IdentifierRef, QuestionDSL, ScenarioRef
from .question_router import (
    QuestionRoute,
    QuestionRouteResolution,
    load_schema_markdown,
    resolve_question_route,
    validate_question_route,
)
from .question_validator import validate_question_dsl
from .llm_answer_context_builder import LLMAnswerContext, build_llm_answer_context
from .reasoner import build_reasoning_result
from .schema_registry import SchemaEntity, SchemaRegistry, build_schema_registry
from .trace_summary_builder import build_trace_summary
from .typeql_builder import _type_label, build_typeql_query
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
    schema_retrieval_bundle: OntologyEvidenceBundle
    llm_answer_context: LLMAnswerContext
    reasoning: dict[str, object]
    trace_summary: dict[str, object]
    fallback_answer: TemplateAnswer
    router_diagnostics: dict[str, object]
    blocked_before_retrieval: bool


_POWER_OUTAGE_KEYWORDS = ('\u65ad\u7535', '\u505c\u7535', '\u6389\u7535')
_FIRE_KEYWORDS = ('\u706b\u707e', '\u5931\u706b', '\u7740\u706b')
_DELAY_KEYWORDS = ('\u5ef6\u671f', '\u5ef6\u8bef', '\u63a8\u8fdf', '\u6ede\u540e')
_CAPACITY_LOSS_KEYWORDS = ('\u4ea7\u80fd\u4e0b\u964d', '\u8d44\u6e90\u4e0d\u8db3', '\u4eba\u624b\u4e0d\u8db3', '\u4eba\u5458\u4e0d\u8db3', '\u7f3a\u4eba', '\u5bb9\u91cf\u4e0d\u8db3')
_ACCESS_BLOCKED_KEYWORDS = ('\u5c01\u9501', '\u5c01\u95ed', '\u65e0\u6cd5\u8fdb\u5165', '\u4e0d\u53ef\u8fdb\u5165', '\u8fdb\u4e0d\u53bb')
_DEADLINE_HINTS = ('\u4ea4\u4ed8', '\u622a\u6b62\u65e5\u671f', 'deadline')
_PROPAGATION_ROUNDS = 2
_ANCHOR_CANDIDATE_LIMIT = 1000
_IDENTIFIER_FALLBACK_KEYS = ('id', 'room_id', 'floor_id', 'milestone_id', 'position_id', 'assignment_id', 'pod_id', 'pod_code', 'activity_id', 'pod_schedule_id')


def run_instance_qa(question: str, graph: OntologyGraph) -> InstanceQAResult:
    schema_registry = build_schema_registry(graph)
    parsed = parse_query(question)
    router_schema_markdown = _load_router_schema_markdown(graph)
    typedb_config = load_typedb_config()

    if typedb_config is None:
        return _run_instance_qa_with_client(
            question,
            graph,
            schema_registry,
            parsed.normalized_query,
            router_schema_markdown,
            typedb_client=None,
        )

    with TypeDBClient(typedb_config) as typedb_client:
        return _run_instance_qa_with_client(
            question,
            graph,
            schema_registry,
            parsed.normalized_query,
            router_schema_markdown,
            typedb_client=typedb_client,
        )



def _run_instance_qa_with_client(
    question: str,
    graph: OntologyGraph,
    schema_registry: SchemaRegistry,
    normalized_query: str,
    router_schema_markdown: str,
    *,
    typedb_client: TypeDBClient | None,
) -> InstanceQAResult:
    anchor_resolution_payload = _resolve_anchor_resolution_payload(
        question,
        schema_registry,
        schema_markdown=router_schema_markdown,
        typedb_client=typedb_client,
    )
    route_resolution = _normalize_question_route_resolution(
        resolve_question_route(
            question,
            schema_registry,
            schema_markdown=router_schema_markdown,
            anchor_resolution_payload=anchor_resolution_payload,
        )
    )
    router_failed = route_resolution.status != 'ok' or route_resolution.route is None
    router_diagnostics = {
        'status': route_resolution.status,
        'error_type': route_resolution.error_type,
        'error_message': route_resolution.error_message,
        'used_fallback': router_failed,
    }

    if router_failed:
        question_dsl = _build_router_failed_question_dsl(
            question,
            normalized_query,
            schema_registry,
            anchor_resolution_payload=anchor_resolution_payload,
        )
    else:
        question_dsl = _build_question_dsl(
            question,
            normalized_query,
            schema_registry,
            route=route_resolution.route,
        )

    if question_dsl.reasoning_scope == 'anchor_only':
        schema_retrieval_bundle = _build_anchor_only_schema_bundle(graph, question_dsl, question)
    else:
        schema_retrieval_bundle = retrieve_ontology_evidence(graph, question)

    question_validation_error = validate_question_dsl(question_dsl, schema_registry)
    if router_failed:
        failure_code = route_resolution.error_type or 'router_unknown_error'
        question_validation_error = f'router_failed:{failure_code}'

    fact_query_records: list[dict[str, object]] = []
    all_rows: list[dict[str, object]] = []

    if (not router_failed) and question_validation_error is None:
        initial_queries = build_fact_queries(question_dsl, schema_registry)
        initial_rows = _execute_fact_queries(initial_queries, schema_registry, fact_query_records, typedb_client)
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

            propagation_rows = _execute_fact_queries(propagation_queries, schema_registry, fact_query_records, typedb_client)
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
            'reasoning_scope': question_dsl.reasoning_scope,
            'target_attributes': list(question_dsl.target_attributes),
            'router_diagnostics': dict(router_diagnostics),
            'blocked_before_retrieval': router_failed,
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
        understanding=_build_evidence_understanding(
            question_dsl,
            normalized_query,
            router_diagnostics=router_diagnostics,
            blocked_before_retrieval=router_failed,
        ),
    )
    llm_answer_context = build_llm_answer_context(evidence_bundle)

    if router_failed:
        reasoning = {
            'summary': {'answer_type': 'router_failure', 'risk_level': 'unknown', 'confidence': 'low'},
            'affected_entities': [],
            'impact_summary': {'direct_counts': {}, 'propagated_counts': {}},
            'deadline_assessment': {'deadline': None, 'at_risk': False, 'reason_codes': [], 'supporting_facts': []},
            'evidence_chains': [],
            'router_diagnostics': dict(router_diagnostics),
        }
    else:
        reasoning = build_reasoning_result(
            fact_pack,
            mode=question_dsl.mode,
            deadline=question_dsl.goal.deadline,
        )

    trace_summary = build_trace_summary(
        question_dsl=question_dsl,
        fact_pack=fact_pack,
        evidence_bundle=evidence_bundle,
        reasoning_result=reasoning,
    )
    fallback_answer = build_instance_template_answer(question, fact_pack, reasoning)

    return InstanceQAResult(
        question=question,
        normalized_query=normalized_query,
        question_dsl=question_dsl,
        question_validation_error=question_validation_error,
        fact_queries=fact_query_records,
        fact_pack=fact_pack,
        evidence_bundle=evidence_bundle,
        schema_retrieval_bundle=schema_retrieval_bundle,
        llm_answer_context=llm_answer_context,
        reasoning=reasoning,
        trace_summary=trace_summary,
        fallback_answer=fallback_answer,
        router_diagnostics=router_diagnostics,
        blocked_before_retrieval=router_failed,
    )



def _execute_fact_queries(
    queries,
    schema_registry: SchemaRegistry,
    fact_query_records: list[dict[str, object]],
    typedb_client: TypeDBClient | None,
) -> list[dict[str, object]]:
    collected_rows: list[dict[str, object]] = []
    for query in queries:
        validation_error = validate_fact_query_dsl(query, schema_registry)
        if validation_error is not None:
            fact_query_records.append({'purpose': query.purpose, 'validation_error': validation_error})
            continue

        typeql = build_typeql_query(query)
        rows, query_error = _call_readonly_query(typeql, typedb_client)
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


def _build_anchor_only_schema_bundle(graph: OntologyGraph, question_dsl: QuestionDSL, question: str) -> OntologyEvidenceBundle:
    object_id = f"object_type:{question_dsl.anchor.entity}"
    obj = graph.get_object(object_id)
    seed_node_ids = [object_id] if obj is not None else []
    display_name_map = {}
    if obj is not None:
        english_name = str(obj.name or question_dsl.anchor.entity).strip() or question_dsl.anchor.entity
        chinese_name = str(obj.attributes.get('chinese_description', '') or '').strip()
        display_name_map[object_id] = f'{chinese_name}({english_name})' if chinese_name and chinese_name != english_name else english_name
    evidence_chain = []
    if seed_node_ids:
        evidence_chain.append(
            EvidenceItem(
                evidence_id='E1',
                kind='seed',
                label=question_dsl.anchor.entity,
                message=f'\u5df2\u8bc6\u522b\u951a\u70b9\u5b9e\u4f53 {question_dsl.anchor.entity}',
                node_ids=list(seed_node_ids),
                why_matched=['\u5c5e\u6027\u67e5\u8be2\u4ec5\u9501\u5b9a\u951a\u70b9\u5b9e\u4f53'],
            )
        )
    return OntologyEvidenceBundle(
        question=question,
        seed_node_ids=list(seed_node_ids),
        matched_node_ids=list(seed_node_ids),
        matched_edge_ids=[],
        highlight_steps=(
            [RetrievalStep(action='anchor_node', message='\u5df2\u8bc6\u522b\u951a\u70b9\u5b9e\u4f53', node_ids=list(seed_node_ids), edge_ids=[], evidence_ids=['E1'])]
            if seed_node_ids
            else []
        ),
        evidence_chain=evidence_chain,
        insufficient_evidence=not bool(seed_node_ids),
        search_trace=SearchTrace(
            seed_node_ids=list(seed_node_ids),
            seed_resolution_source='question_router',
            seed_resolution_reasoning='attribute_lookup -> anchor_only',
            seed_resolution_error='',
            expansion_steps=[],
        ),
        display_name_map=display_name_map,
        relation_name_map={},
    )




def _load_router_schema_markdown(graph: OntologyGraph) -> str:
    source_file = str(graph.metadata.get('source_file') or '').strip()
    if source_file:
        schema_markdown = load_schema_markdown(source_file)
        if schema_markdown:
            return schema_markdown

    typedb_input_file = str(graph.metadata.get('typedb_schema_input_file') or '').strip()
    if typedb_input_file:
        from ..pipelines.input_file_resolver import resolve_input_to_markdown

        try:
            resolved = resolve_input_to_markdown(typedb_input_file)
        except Exception:
            return ''
        return load_schema_markdown(resolved)
    return ''


def _resolve_anchor_resolution_payload(
    question: str,
    schema_registry: SchemaRegistry,
    *,
    schema_markdown: str = '',
    typedb_client: TypeDBClient | None = None,
) -> dict[str, object] | None:
    locator_registry = build_anchor_locator_registry(schema_registry)
    if not locator_registry:
        return None

    surface_candidates = _extract_anchor_surface_candidates(question)
    if not surface_candidates:
        return None

    index_path = _build_or_load_anchor_search_index(locator_registry, typedb_client=typedb_client)
    if index_path is None:
        return None

    fallback_payload: dict[str, object] | None = None
    attempted_refresh = False
    while True:
        had_any_hit = False
        for raw_anchor_text in surface_candidates:
            search_hits = search_anchor_candidates(index_path, raw_anchor_text, top_k=20)
            candidate_rows_by_entity = _group_anchor_search_hits(search_hits)
            if not any(candidate_rows_by_entity.values()):
                continue

            had_any_hit = True
            deterministic_result = resolve_anchor_candidates(
                raw_anchor_text=raw_anchor_text,
                locator_registry=locator_registry,
                candidate_rows_by_entity=candidate_rows_by_entity,
            )
            if not deterministic_result.candidates:
                continue

            candidate_context = build_anchor_candidate_context(
                question=question,
                schema_registry=schema_registry,
                resolution=deterministic_result,
            )

            rank_decision = None
            if not (
                deterministic_result.selected is not None
                and deterministic_result.match_stage in {'exact', 'light'}
            ):
                rank_decision = resolve_anchor_candidate_rank(
                    question=question,
                    schema_markdown=schema_markdown,
                    candidate_context=candidate_context,
                )

            payload = apply_anchor_resolution_policy(
                deterministic_result=deterministic_result,
                candidate_context=candidate_context,
                rank_decision=rank_decision,
            )
            if payload is None:
                continue

            selection = payload.get('selection') if isinstance(payload, dict) else None
            decision = str(selection.get('decision') or '').strip() if isinstance(selection, dict) else ''
            if decision == 'select':
                return payload
            if fallback_payload is None:
                fallback_payload = payload

        if had_any_hit or attempted_refresh:
            return fallback_payload

        refreshed_index_path = _build_or_load_anchor_search_index(locator_registry, typedb_client=typedb_client, force_rebuild=True)
        if refreshed_index_path is None or refreshed_index_path == index_path and attempted_refresh:
            return fallback_payload
        index_path = refreshed_index_path
        attempted_refresh = True



def _normalize_question_route_resolution(result: object) -> QuestionRouteResolution:
    if isinstance(result, QuestionRouteResolution):
        return result
    if isinstance(result, QuestionRoute):
        return QuestionRouteResolution(status='ok', error_type='', error_message='', route=result)
    return QuestionRouteResolution(status='failed', error_type='router_unknown_error', error_message='Router resolution unavailable.', route=None)


def _build_router_failed_question_dsl(
    question: str,
    normalized_query: str,
    schema_registry: SchemaRegistry,
    *,
    anchor_resolution_payload: dict[str, object] | None,
) -> QuestionDSL:
    anchor_entity = _safe_anchor_entity_for_router_failure(schema_registry, anchor_resolution_payload)
    identifier = _anchor_identifier_from_resolution_payload(anchor_resolution_payload, anchor_entity)
    deadline = _extract_deadline(normalized_query)
    event_type = _detect_event_type(normalized_query)
    mode = _detect_mode(normalized_query, deadline, event_type)
    goal_type = 'yes_no_risk' if mode == 'deadline_risk_check' else ('list_impacts' if mode == 'impact_analysis' else 'instance_lookup')
    target_attributes = _infer_target_attributes_for_router_failure(question, schema_registry, anchor_entity)
    reasoning_scope = 'anchor_only' if identifier is not None and target_attributes else 'expand_graph'

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
        reasoning_scope=reasoning_scope,
        target_attributes=target_attributes,
    )


def _safe_anchor_entity_for_router_failure(
    schema_registry: SchemaRegistry,
    anchor_resolution_payload: dict[str, object] | None,
) -> str:
    if isinstance(anchor_resolution_payload, dict):
        selected = anchor_resolution_payload.get('selected')
        if isinstance(selected, dict):
            selected_entity = str(selected.get('entity') or '').strip()
            if selected_entity in schema_registry.entities:
                return selected_entity
        candidates = anchor_resolution_payload.get('candidates')
        if isinstance(candidates, list):
            for item in candidates:
                if not isinstance(item, dict):
                    continue
                entity = str(item.get('entity') or '').strip()
                if entity in schema_registry.entities:
                    return entity

    for preferred in ('PoD', 'Room'):
        if preferred in schema_registry.entities:
            return preferred
    return next(iter(schema_registry.entities), 'Room')


def _anchor_identifier_from_resolution_payload(
    anchor_resolution_payload: dict[str, object] | None,
    anchor_entity: str,
) -> IdentifierRef | None:
    if not isinstance(anchor_resolution_payload, dict):
        return None

    selected = anchor_resolution_payload.get('selected')
    if isinstance(selected, dict):
        entity = str(selected.get('entity') or '').strip()
        attribute = str(selected.get('attribute') or '').strip()
        value = str(selected.get('value') or '').strip()
        if entity == anchor_entity and attribute and value:
            return IdentifierRef(attribute=attribute, value=value)

    candidates = anchor_resolution_payload.get('candidates')
    if isinstance(candidates, list):
        for item in candidates:
            if not isinstance(item, dict):
                continue
            entity = str(item.get('entity') or '').strip()
            attribute = str(item.get('attribute') or '').strip()
            value = str(item.get('value') or '').strip()
            if entity == anchor_entity and attribute and value:
                return IdentifierRef(attribute=attribute, value=value)

    return None

def _infer_target_attributes_for_router_failure(
    question: str,
    schema_registry: SchemaRegistry,
    anchor_entity: str,
) -> list[str]:
    entity_schema = schema_registry.entities.get(anchor_entity)
    if entity_schema is None:
        return []

    text = str(question or '')
    if '\u72b6\u6001' in text:
        for attribute in entity_schema.attributes:
            if attribute.endswith('_status') or attribute == 'status':
                return [attribute]
    return []


def _extract_anchor_surface_candidates(question: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for match in re.findall(r'[A-Za-z0-9][A-Za-z0-9_\-/]{1,}', question):
        value = str(match or '').strip().strip(',.!?;:??????')
        if len(value) < 2 or not any('A' <= ch.upper() <= 'Z' for ch in value):
            continue
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        values.append(value)
    values.sort(key=len, reverse=True)
    return values


def _build_or_load_anchor_search_index(
    locator_registry: dict[str, object],
    *,
    typedb_client: TypeDBClient | None,
    force_rebuild: bool = False,
) -> Path | None:
    config = load_typedb_config()
    db_path = _anchor_index_db_path(config)
    allow_cached_index = config is not None or bool(os.getenv('INSTANCE_QA_ANCHOR_INDEX_DIR'))
    if (not force_rebuild) and allow_cached_index and db_path.exists() and db_path.stat().st_size > 0:
        return db_path

    candidate_rows_by_entity = _call_load_anchor_candidate_rows(locator_registry, typedb_client)
    index_rows: list[dict[str, object]] = []
    for entity_name, rows in candidate_rows_by_entity.items():
        locator = locator_registry.get(entity_name)
        for row in rows:
            if not isinstance(row, dict):
                continue
            lookup_attributes = _resolve_lookup_attributes_for_anchor_index(locator, row)
            if not lookup_attributes:
                continue
            payload = dict(row)
            for attribute in lookup_attributes:
                raw_value = str(row.get(attribute) or '').strip()
                if not raw_value:
                    continue
                iid = _resolve_anchor_index_iid(row, entity_name, attribute, raw_value)
                index_rows.append(
                    {
                        'entity': entity_name,
                        'attribute': attribute,
                        'raw_value': raw_value,
                        'iid': iid,
                        'payload': payload,
                    }
                )
    if not index_rows:
        return None
    return build_anchor_search_index(index_rows, db_path=db_path)



def _resolve_lookup_attributes_for_anchor_index(locator: object, row: dict[str, object]) -> tuple[str, ...]:
    lookup_attributes = tuple(getattr(locator, 'lookup_attributes', ()) or ())
    if lookup_attributes:
        return lookup_attributes

    fallback_attributes: list[str] = []
    for key, value in row.items():
        if key.startswith('_'):
            continue
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        if key in _IDENTIFIER_FALLBACK_KEYS or key.endswith(('_id', '_code', '_name', '_model')):
            fallback_attributes.append(key)
    return tuple(fallback_attributes)



def _resolve_anchor_index_iid(row: dict[str, object], entity_name: str, attribute: str, raw_value: str) -> str:
    iid = str(row.get('_iid') or '').strip()
    if iid:
        return iid

    preferred = str(row.get(attribute) or '').strip()
    if preferred:
        return f'{entity_name}:{attribute}:{preferred}'
    return f'{entity_name}:{attribute}:{raw_value}'



def _anchor_index_db_path(config) -> Path:
    root = Path(os.getenv('INSTANCE_QA_ANCHOR_INDEX_DIR', '.cache/instance_qa'))
    root.mkdir(parents=True, exist_ok=True)
    database = str(getattr(config, 'database', '') or 'default').strip().replace('/', '_').replace('\\', '_')
    return root / f'anchor_index_{database}.sqlite3'



def _group_anchor_search_hits(search_hits: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for hit in search_hits:
        if not isinstance(hit, dict):
            continue
        entity = str(hit.get('entity') or '').strip()
        iid = str(hit.get('iid') or '').strip()
        payload = hit.get('payload')
        if not entity or not iid or not isinstance(payload, dict):
            continue
        key = (entity, iid)
        if key in seen:
            continue
        seen.add(key)
        row = dict(payload)
        row.setdefault('_entity', entity)
        row.setdefault('_iid', iid)
        result[entity].append(row)
    return result



def _load_anchor_candidate_rows(locator_registry: dict[str, object], *, typedb_client: TypeDBClient | None) -> dict[str, list[dict[str, object]]]:
    result: dict[str, list[dict[str, object]]] = {}
    for entity_name in locator_registry:
        typeql = _build_anchor_candidate_query(entity_name)
        rows, _ = _call_readonly_query(typeql, typedb_client)
        result[entity_name] = rows
    return result



def _call_load_anchor_candidate_rows(locator_registry: dict[str, object], typedb_client: TypeDBClient | None) -> dict[str, list[dict[str, object]]]:
    try:
        return _load_anchor_candidate_rows(locator_registry, typedb_client=typedb_client)
    except TypeError:
        return _load_anchor_candidate_rows(locator_registry)



def _call_readonly_query(typeql: str, typedb_client: TypeDBClient | None) -> tuple[list[dict[str, object]], str | None]:
    try:
        return _run_typeql_readonly(typeql, typedb_client)
    except TypeError:
        return _run_typeql_readonly(typeql)



def _build_anchor_candidate_query(entity_name: str) -> str:
    return '\n'.join(
        [
            'match',
            f'$root isa {_type_label(entity_name)};',
            'get $root;',
            f'limit {_ANCHOR_CANDIDATE_LIMIT};',
        ]
    )


def _run_typeql_readonly(typeql: str, typedb_client: TypeDBClient | None = None) -> tuple[list[dict[str, object]], str | None]:
    if typedb_client is not None:
        try:
            rows = typedb_client.execute_readonly(typeql)
            return rows, None
        except (TypeDBConnectionError, TypeDBQueryError) as exc:
            return [], f'{type(exc).__name__}: {exc}'

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


def _build_question_dsl(question: str, normalized_query: str, schema_registry: SchemaRegistry, *, route: QuestionRoute | None = None) -> QuestionDSL:
    parsed = parse_query(normalized_query)
    if route is not None and validate_question_route(route, schema_registry) is None:
        return _build_question_dsl_from_route(question, normalized_query, route)
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


def _build_question_dsl_from_route(question: str, normalized_query: str, route: QuestionRoute) -> QuestionDSL:
    deadline = _extract_deadline(normalized_query)
    event_type = _detect_event_type(normalized_query)
    if route.intent == 'impact_analysis':
        mode = 'impact_analysis'
        goal_type = 'list_impacts'
    elif route.intent == 'attribute_lookup':
        mode = 'fact_lookup'
        goal_type = 'instance_lookup'
    else:
        mode = _detect_mode(normalized_query, deadline, event_type)
        goal_type = 'yes_no_risk' if mode == 'deadline_risk_check' else ('list_impacts' if mode == 'impact_analysis' else 'instance_lookup')

    identifier = None
    if route.anchor_locator.attribute and route.anchor_locator.value:
        identifier = IdentifierRef(attribute=route.anchor_locator.attribute, value=route.anchor_locator.value)

    return QuestionDSL(
        mode=mode,
        anchor=AnchorRef(entity=route.anchor_entity, identifier=identifier, surface=question),
        scenario=ScenarioRef(event_type=event_type, duration=None, start_time=None, severity=None, raw_event=''),
        goal=GoalRef(
            type=goal_type,
            target_entity=None,
            target_metric='delivery' if mode == 'deadline_risk_check' else None,
            deadline=deadline,
        ),
        constraints=ConstraintRef(statuses=[], time_window=None, limit=20),
        reasoning_scope=route.reasoning_scope,
        target_attributes=list(route.target_attributes),
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


def _build_evidence_understanding(
    question: QuestionDSL,
    normalized_query: str,
    *,
    router_diagnostics: dict[str, object] | None = None,
    blocked_before_retrieval: bool = False,
) -> dict[str, object]:
    anchor = _build_anchor_metadata(question.anchor)
    return {
        'mode': question.mode,
        'reasoning_scope': question.reasoning_scope,
        'target_attributes': list(question.target_attributes),
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
        'router_diagnostics': dict(router_diagnostics or {}),
        'blocked_before_retrieval': bool(blocked_before_retrieval),
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
