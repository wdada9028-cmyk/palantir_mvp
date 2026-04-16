from __future__ import annotations

import json
from collections.abc import AsyncIterator
from uuid import uuid4

from ..instance_qa.orchestrator import InstanceQAResult
from ..qa.generator import GeneratorChunk, GeneratorResult, iter_generated_instance_answer


def sse_event(name: str, payload: dict[str, object]) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def iter_qa_events(result: InstanceQAResult) -> AsyncIterator[str]:
    session_id = uuid4().hex
    step = 0

    step += 1
    yield sse_event('question_parsed', {
        'session_id': session_id,
        'step': step,
        'question': result.question,
        'normalized_query': result.normalized_query,
    })

    step += 1
    yield sse_event('question_dsl', {
        'session_id': session_id,
        'step': step,
        'question_dsl': _question_to_dict(result.question_dsl),
        'validation_error': result.question_validation_error,
        'router_diagnostics': result.router_diagnostics,
        'blocked_before_retrieval': result.blocked_before_retrieval,
    })

    schema_trace_events, step = _build_schema_trace_events(result, session_id=session_id, start_step=step)
    for event_text in schema_trace_events:
        yield event_text

    step += 1
    yield sse_event('fact_query_planned', {
        'session_id': session_id,
        'step': step,
        'fact_queries': result.fact_queries,
    })

    for item in result.fact_queries:
        step += 1
        yield sse_event('typedb_query', {
            'session_id': session_id,
            'step': step,
            'purpose': item.get('purpose'),
            'typeql': item.get('typeql', ''),
            'error': item.get('error'),
        })

    step += 1
    yield sse_event('typedb_result', {
        'session_id': session_id,
        'step': step,
        'fact_pack': result.fact_pack,
    })

    step += 1
    yield sse_event('evidence_bundle_ready', {
        'session_id': session_id,
        'step': step,
        'evidence_bundle': result.evidence_bundle.to_dict(),
    })

    step += 1
    yield sse_event('llm_answer_context_ready', {
        'session_id': session_id,
        'step': step,
        'llm_answer_context': _llm_context_to_dict(result),
    })

    step += 1
    yield sse_event('reasoning_done', {
        'session_id': session_id,
        'step': step,
        'reasoning': result.reasoning,
    })

    step += 1
    yield sse_event('trace_summary_ready', {
        'session_id': session_id,
        'step': step,
        'trace_summary': result.trace_summary,
    })

    final_result: GeneratorResult | None = None
    if result.question_validation_error is None:
        async for chunk in iter_generated_instance_answer(
            result.question,
            schema_summary={'entities': list(result.fact_pack.get('instances', {}).keys())},
            fact_pack=result.fact_pack,
            reasoning_result=result.reasoning,
            llm_answer_context=result.llm_answer_context,
            fallback_answer=result.fallback_answer,
        ):
            if isinstance(chunk, GeneratorChunk):
                step += 1
                yield sse_event('answer_delta', {
                    'session_id': session_id,
                    'step': step,
                    'delta': chunk.delta,
                    'answer_text_so_far': chunk.answer_text_so_far,
                })
            else:
                final_result = chunk

    if final_result is None:
        final_result = GeneratorResult(answer_text=result.fallback_answer.answer, used_fallback=True)

    step += 1
    yield sse_event('answer_done', {
        'session_id': session_id,
        'step': step,
        'answer': result.fallback_answer.answer,
        'answer_text': final_result.answer_text,
        'used_fallback': final_result.used_fallback,
        'reasoning': result.reasoning,
        'fact_pack': result.fact_pack,
        'trace_summary': result.trace_summary,
        'router_diagnostics': result.router_diagnostics,
        'blocked_before_retrieval': result.blocked_before_retrieval,
    })


def _llm_context_to_dict(result: InstanceQAResult) -> dict[str, object]:
    context = result.llm_answer_context
    return {
        'system_prompt': context.system_prompt,
        'task_prompt': context.task_prompt,
        'evidence_contract_prompt': context.evidence_contract_prompt,
        'style_prompt': context.style_prompt,
        'user_payload': context.user_payload,
    }



def _build_schema_trace_events(result: InstanceQAResult, *, session_id: str, start_step: int) -> tuple[list[str], int]:
    if result.blocked_before_retrieval:
        return [], start_step

    evidence_trace = _build_instance_evidence_trace_events(result, session_id=session_id, start_step=start_step)
    if evidence_trace is not None:
        return evidence_trace

    return _build_legacy_schema_trace_events(result, session_id=session_id, start_step=start_step)



def _build_instance_evidence_trace_events(result: InstanceQAResult, *, session_id: str, start_step: int) -> tuple[list[str], int] | None:
    question_dsl = getattr(result, 'question_dsl', None)
    if question_dsl is None or str(getattr(question_dsl, 'reasoning_scope', '') or '').strip() != 'expand_graph':
        return None

    fact_pack = result.fact_pack if isinstance(result.fact_pack, dict) else {}
    instances = fact_pack.get('instances') if isinstance(fact_pack, dict) else {}
    if not isinstance(instances, dict) or not instances:
        return None

    anchor = getattr(question_dsl, 'anchor', None)
    anchor_entity = str(getattr(anchor, 'entity', '') or '').strip()
    anchor_node_id = _entity_node_id(anchor_entity) if anchor_entity else ''
    if not anchor_node_id:
        return None

    direct_entities, propagated_entities = _build_impact_playback_groups(result, anchor_entity)
    label_for = lambda entity: _entity_label(result, entity)

    events: list[str] = []
    evidence_chain: list[dict[str, object]] = []
    step = start_step
    snapshot_node_ids: list[str] = [anchor_node_id]
    evidence_index = 1

    anchor_message = f'\u5df2\u5b9a\u4f4d\u8d77\u70b9\u5b9e\u4f53\uff1a{label_for(anchor_entity)}'
    step += 1
    events.append(sse_event('trace_anchor', {
        'session_id': session_id,
        'step': step,
        'message': anchor_message,
        'node_ids': [anchor_node_id],
        'edge_ids': [],
        'snapshot_node_ids': list(snapshot_node_ids),
        'snapshot_edge_ids': [],
        'delay_ms': 600,
    }))
    evidence_chain.append({
        'evidence_id': f'E{evidence_index}',
        'kind': 'seed',
        'label': label_for(anchor_entity),
        'message': anchor_message,
        'node_ids': [anchor_node_id],
        'edge_ids': [],
        'why_matched': ['\u6700\u7ec8\u5b9e\u4f8b\u8bc1\u636e\u7684\u8d77\u70b9\u5b9e\u4f53'],
    })
    evidence_index += 1

    if direct_entities:
        step, evidence_index = _append_entity_group_events(
            events,
            evidence_chain,
            session_id=session_id,
            step=step,
            evidence_index=evidence_index,
            snapshot_node_ids=snapshot_node_ids,
            group_message='\u6b63\u5728\u5c55\u5f00\u76f4\u63a5\u5f71\u54cd\u5b9e\u4f53',
            item_prefix='\u76f4\u63a5\u5f71\u54cd\u5b9e\u4f53\uff1a',
            entities=direct_entities,
            label_for=label_for,
        )
    if propagated_entities:
        step, evidence_index = _append_entity_group_events(
            events,
            evidence_chain,
            session_id=session_id,
            step=step,
            evidence_index=evidence_index,
            snapshot_node_ids=snapshot_node_ids,
            group_message='\u6b63\u5728\u5c55\u5f00\u4f20\u64ad\u5f71\u54cd\u5b9e\u4f53',
            item_prefix='\u4f20\u64ad\u5f71\u54cd\u5b9e\u4f53\uff1a',
            entities=propagated_entities,
            label_for=label_for,
        )

    if len(snapshot_node_ids) <= 1:
        return None

    step += 1
    events.append(sse_event('evidence_final', {
        'session_id': session_id,
        'step': step,
        'message': '\u5df2\u5b8c\u6210\u5f71\u54cd\u8303\u56f4\u5b9a\u4f4d',
        'evidence_chain': evidence_chain,
        'search_trace': {
            'seed_node_ids': [anchor_node_id],
            'seed_resolution_source': 'instance_evidence',
            'seed_resolution_reasoning': 'final_instance_evidence_playback',
            'seed_resolution_error': '',
            'expansion_steps': [],
        },
    }))

    return events, step



def _append_entity_group_events(
    events: list[str],
    evidence_chain: list[dict[str, object]],
    *,
    session_id: str,
    step: int,
    evidence_index: int,
    snapshot_node_ids: list[str],
    group_message: str,
    item_prefix: str,
    entities: list[str],
    label_for,
) -> tuple[int, int]:
    step += 1
    events.append(sse_event('trace_expand', {
        'session_id': session_id,
        'step': step,
        'message': group_message,
        'node_ids': list(snapshot_node_ids),
        'edge_ids': [],
        'snapshot_node_ids': list(snapshot_node_ids),
        'snapshot_edge_ids': [],
        'delay_ms': 600,
    }))
    evidence_chain.append({
        'evidence_id': f'E{evidence_index}',
        'kind': 'group',
        'label': group_message,
        'message': group_message,
        'node_ids': [],
        'edge_ids': [],
        'why_matched': [],
    })
    evidence_index += 1

    for entity in entities:
        node_id = _entity_node_id(entity)
        if not node_id:
            continue
        if node_id not in snapshot_node_ids:
            snapshot_node_ids.append(node_id)
        message = f'{item_prefix}{label_for(entity)}'
        step += 1
        events.append(sse_event('trace_expand', {
            'session_id': session_id,
            'step': step,
            'message': message,
            'node_ids': [node_id],
            'edge_ids': [],
            'snapshot_node_ids': list(snapshot_node_ids),
            'snapshot_edge_ids': [],
            'delay_ms': 600,
        }))
        evidence_chain.append({
            'evidence_id': f'E{evidence_index}',
            'kind': 'entity',
            'label': label_for(entity),
            'message': message,
            'node_ids': [node_id],
            'edge_ids': [],
            'why_matched': ['????????'],
        })
        evidence_index += 1

    return step, evidence_index



def _build_impact_playback_groups(result: InstanceQAResult, anchor_entity: str) -> tuple[list[str], list[str]]:
    reasoning = result.reasoning if isinstance(result.reasoning, dict) else {}
    impact_summary = reasoning.get('impact_summary') if isinstance(reasoning.get('impact_summary'), dict) else {}
    affected_entities = reasoning.get('affected_entities') if isinstance(reasoning.get('affected_entities'), list) else []
    fact_pack = result.fact_pack if isinstance(result.fact_pack, dict) else {}
    instances = fact_pack.get('instances') if isinstance(fact_pack.get('instances'), dict) else {}

    direct_entities: list[str] = []
    propagated_entities: list[str] = []
    seen_direct: set[str] = set()
    seen_propagated: set[str] = set()

    def push(target: list[str], seen: set[str], entity: str):
        text = str(entity or '').strip()
        if not text or text == anchor_entity or text in seen:
            return
        seen.add(text)
        target.append(text)

    if isinstance(impact_summary, dict):
        for entity in (impact_summary.get('direct_counts') or {}).keys():
            push(direct_entities, seen_direct, entity)
        for entity in (impact_summary.get('propagated_counts') or {}).keys():
            push(propagated_entities, seen_propagated, entity)

    for item in affected_entities:
        if not isinstance(item, dict):
            continue
        entity = str(item.get('entity') or '').strip()
        depth = int(item.get('depth') or 1)
        if depth <= 1:
            push(direct_entities, seen_direct, entity)
        else:
            push(propagated_entities, seen_propagated, entity)

    if isinstance(instances, dict):
        for entity in instances.keys():
            text = str(entity or '').strip()
            if not text or text == anchor_entity or text in seen_direct or text in seen_propagated:
                continue
            push(direct_entities, seen_direct, text)

    return direct_entities, propagated_entities



def _entity_node_id(entity: str) -> str:
    text = str(entity or '').strip()
    return f'object_type:{text}' if text else ''



def _entity_label(result: InstanceQAResult, entity: str) -> str:
    target = str(entity or '').strip()
    if not target:
        return ''

    bundle = getattr(result, 'evidence_bundle', None)
    positive = getattr(bundle, 'positive_evidence', []) if bundle is not None else []
    for group in positive if isinstance(positive, list) else []:
        if getattr(group, 'entity', '') != target:
            continue
        instances = getattr(group, 'instances', [])
        for item in instances if isinstance(instances, list) else []:
            schema_context = getattr(item, 'schema_context', None)
            entity_zh = str(getattr(schema_context, 'entity_zh', '') or '').strip()
            if entity_zh:
                return entity_zh

    display_name_map = getattr(result.schema_retrieval_bundle, 'display_name_map', {})
    raw = str(display_name_map.get(_entity_node_id(target), '') or '').strip()
    if raw:
        suffix = f'({target})'
        if raw.endswith(suffix):
            raw = raw[:-len(suffix)].strip()
        if raw:
            return raw
    return target



def _build_legacy_schema_trace_events(result: InstanceQAResult, *, session_id: str, start_step: int) -> tuple[list[str], int]:
    bundle = result.schema_retrieval_bundle
    search_trace = bundle.search_trace
    events: list[str] = []
    step = start_step

    seed_node_ids = list(search_trace.seed_node_ids or bundle.seed_node_ids)
    if seed_node_ids:
        step += 1
        events.append(sse_event('trace_anchor', {
            'session_id': session_id,
            'step': step,
            'message': '\u5df2\u8bc6\u522b\u951a\u70b9\u5b9e\u4f53',
            'node_ids': seed_node_ids,
            'edge_ids': [],
            'snapshot_node_ids': seed_node_ids,
            'snapshot_edge_ids': [],
            'delay_ms': 420,
        }))

    for item in search_trace.expansion_steps:
        step += 1
        events.append(sse_event('trace_expand', {
            'session_id': session_id,
            'step': step,
            'message': f'\u6cbf {item.relation} \u6269\u5c55\u5230\u76f8\u5173\u5b9e\u4f53',
            'node_ids': [item.to_node_id],
            'edge_ids': [item.edge_id],
            'snapshot_node_ids': list(item.snapshot_node_ids),
            'snapshot_edge_ids': list(item.snapshot_edge_ids),
            'delay_ms': 600,
        }))

    if seed_node_ids or search_trace.expansion_steps:
        step += 1
        events.append(sse_event('evidence_final', {
            'session_id': session_id,
            'step': step,
            'message': '\u5df2\u5b8c\u6210\u672c\u4f53\u68c0\u7d22\u5b9a\u4f4d',
            'evidence_chain': [item.to_dict() for item in bundle.evidence_chain],
            'search_trace': bundle.search_trace.to_dict(),
        }))

    return events, step



def _question_to_dict(question) -> dict[str, object]:
    return {
        'mode': question.mode,
        'reasoning_scope': question.reasoning_scope,
        'target_attributes': list(question.target_attributes),
        'anchor': {
            'entity': question.anchor.entity,
            'identifier': (
                {'attribute': question.anchor.identifier.attribute, 'value': question.anchor.identifier.value}
                if question.anchor.identifier
                else None
            ),
            'surface': question.anchor.surface,
        },
        'scenario': (
            {
                'event_type': question.scenario.event_type,
                'duration': (
                    {'value': question.scenario.duration.value, 'unit': question.scenario.duration.unit}
                    if question.scenario and question.scenario.duration
                    else None
                ),
                'start_time': question.scenario.start_time if question.scenario else None,
                'severity': question.scenario.severity if question.scenario else None,
                'raw_event': question.scenario.raw_event if question.scenario else '',
            }
            if question.scenario
            else None
        ),
        'goal': {
            'type': question.goal.type,
            'target_entity': question.goal.target_entity,
            'target_metric': question.goal.target_metric,
            'deadline': question.goal.deadline,
        },
        'constraints': {
            'statuses': list(question.constraints.statuses),
            'time_window': question.constraints.time_window,
            'limit': question.constraints.limit,
        },
    }
