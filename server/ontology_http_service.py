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
    })

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

    final_result: GeneratorResult | None = None
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




def _question_to_dict(question) -> dict[str, object]:
    return {
        'mode': question.mode,
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
