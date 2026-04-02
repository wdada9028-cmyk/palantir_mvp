from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, AsyncIterator

from .template_answering import TemplateAnswer, _dedupe_trace_steps, _relation_name, _summary_name
from ..search.ontology_query_models import OntologyEvidenceBundle

_DEFAULT_MODEL = 'qwen2.5-32b-instruct'


@dataclass(slots=True)
class GeneratorConfig:
    api_base: str
    api_key: str
    model: str = _DEFAULT_MODEL


@dataclass(slots=True)
class GeneratorChunk:
    delta: str
    answer_text_so_far: str


@dataclass(slots=True)
class GeneratorResult:
    answer_text: str
    used_fallback: bool


async def iter_generated_answer(
    question: str,
    bundle: OntologyEvidenceBundle,
    fallback_answer: TemplateAnswer,
) -> AsyncIterator[GeneratorChunk | GeneratorResult]:
    config = _load_config()
    fact_lines = _build_fact_lines(bundle)
    if config is None or not fact_lines:
        yield GeneratorResult(answer_text=fallback_answer.answer, used_fallback=True)
        return

    answer_parts: list[str] = []
    try:
        client = get_openai_client()
        stream = await client.chat.completions.create(
            model=config.model,
            temperature=0.1,
            stream=True,
            messages=_build_messages(question, fact_lines),
        )
        async for chunk in stream:
            delta = _extract_delta_text(chunk)
            if not delta:
                continue
            answer_parts.append(delta)
            yield GeneratorChunk(delta=delta, answer_text_so_far=''.join(answer_parts))
    except Exception:
        yield GeneratorResult(answer_text=fallback_answer.answer, used_fallback=True)
        return

    answer_text = ''.join(answer_parts).strip()
    if not answer_text:
        yield GeneratorResult(answer_text=fallback_answer.answer, used_fallback=True)
        return
    yield GeneratorResult(answer_text=answer_text, used_fallback=False)


def get_openai_client() -> Any:
    from openai import AsyncOpenAI

    config = _load_config()
    if config is None:
        raise RuntimeError('Missing QWEN_API_BASE or QWEN_API_KEY.')
    return AsyncOpenAI(
        api_key=config.api_key,
        base_url=config.api_base.rstrip('/'),
    )


def _load_config() -> GeneratorConfig | None:
    api_base = os.getenv('QWEN_API_BASE', '').strip()
    api_key = os.getenv('QWEN_API_KEY', '').strip()
    if not api_base or not api_key:
        return None
    return GeneratorConfig(
        api_base=api_base,
        api_key=api_key,
        model=os.getenv('QWEN_MODEL', _DEFAULT_MODEL).strip() or _DEFAULT_MODEL,
    )


def _build_fact_lines(bundle: OntologyEvidenceBundle) -> list[str]:
    fact_lines = [
        f'{_summary_name(bundle, step.from_node_id)} {_relation_name(bundle, step.relation)} {_summary_name(bundle, step.to_node_id)}'
        for step in _dedupe_trace_steps(bundle.search_trace.expansion_steps)
    ]
    if fact_lines:
        return _dedupe_preserve_order(fact_lines)

    fallback_lines: list[str] = []
    for item in bundle.evidence_chain:
        if item.kind != 'relation' or len(item.node_ids) < 2:
            continue
        fallback_lines.append(
            f'{_summary_name(bundle, item.node_ids[0])} [\u5173\u8054] {_summary_name(bundle, item.node_ids[1])}'
        )
    return _dedupe_preserve_order(fallback_lines)


def _build_messages(question: str, fact_lines: list[str]) -> list[dict[str, str]]:
    facts_block = '\n'.join(f'- {line}' for line in fact_lines)
    return [
        {
            'role': 'system',
            'content': (
                '\u4f60\u662f\u4e91\u4ea4\u4ed8\u672c\u4f53\u95ee\u7b54\u52a9\u624b\u3002'
                '\u53ea\u80fd\u6839\u636e\u63d0\u4f9b\u7684\u672c\u4f53\u4e8b\u5b9e\u751f\u6210\u9762\u5411\u7528\u6237\u7684\u7b54\u6848\u6458\u8981\uff0c\u4e0d\u5f97\u7f16\u9020\u5173\u7cfb\u3002'
                '\u4e0d\u8981\u590d\u8ff0\u68c0\u7d22\u8def\u5f84\uff0c\u4e0d\u8981\u63cf\u8ff0\u4ece\u54ea\u4e2a\u8282\u70b9\u6269\u5c55\u5230\u54ea\u4e2a\u8282\u70b9\u3002'
                '\u91cd\u70b9\u603b\u7ed3\u54ea\u4e9b\u5bf9\u8c61\u53d7\u5f71\u54cd\u3001\u4e3a\u4ec0\u4e48\u53d7\u5f71\u54cd\u3001\u5f71\u54cd\u8868\u73b0\u5728\u54ea\u91cc\u3002'
                '\u8f93\u51fa\u901a\u987a\u81ea\u7136\u7684\u4e2d\u6587\uff0c\u53ef\u4ee5\u5408\u5e76\u591a\u6761\u5173\u7cfb\u5f62\u6210\u66f4\u9ad8\u5c42\u7ed3\u8bba\u3002'
                '\u4e0d\u8981\u8f93\u51fa\u82f1\u6587\u5b9e\u4f53\u540d\uff0c\u4e0d\u8981\u8f93\u51fa\u8bc1\u636e\u7f16\u53f7\u3002'
                '\u5982\u679c\u4e8b\u5b9e\u4e0d\u8db3\uff0c\u8bf7\u660e\u786e\u8bf4\u660e\u8bc1\u636e\u4e0d\u8db3\u3002'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'\u7528\u6237\u95ee\u9898\uff1a{question}\n\n'
                '\u4ec5\u53ef\u4f7f\u7528\u4ee5\u4e0b\u672c\u4f53\u4e8b\u5b9e\uff1a\n'
                f'{facts_block}\n\n'
                '\u8bf7\u57fa\u4e8e\u8fd9\u4e9b\u4e8b\u5b9e\u751f\u6210\u7b54\u6848\u6458\u8981\u3002'
            ),
        },
    ]


def _extract_delta_text(chunk: Any) -> str:
    choices = getattr(chunk, 'choices', None)
    if not choices:
        return ''
    delta = getattr(choices[0], 'delta', None)
    if delta is None:
        return ''
    content = getattr(delta, 'content', '')
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = getattr(item, 'text', None)
            if text:
                parts.append(str(text))
        content = ''.join(parts)
    return str(content or '')


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result



async def iter_generated_instance_answer(
    question: str,
    *,
    schema_summary: dict[str, object],
    fact_pack: dict[str, object],
    reasoning_result: dict[str, object],
    fallback_answer: TemplateAnswer,
) -> AsyncIterator[GeneratorChunk | GeneratorResult]:
    config = _load_config()
    if config is None:
        yield GeneratorResult(answer_text=fallback_answer.answer, used_fallback=True)
        return

    fact_summary = _build_instance_fact_summary(fact_pack, reasoning_result)
    if not fact_summary:
        yield GeneratorResult(answer_text=fallback_answer.answer, used_fallback=True)
        return

    answer_parts: list[str] = []
    try:
        client = get_openai_client()
        stream = await client.chat.completions.create(
            model=config.model,
            temperature=0.1,
            stream=True,
            messages=[
                {
                    'role': 'system',
                    'content': '???????????????? schema ????????????????????',
                },
                {
                    'role': 'user',
                    'content': f'?????{question}\n\nSchema ???{schema_summary}\n\n????????\n{fact_summary}\n\n????????',
                },
            ],
        )
        async for chunk in stream:
            delta = _extract_delta_text(chunk)
            if not delta:
                continue
            answer_parts.append(delta)
            yield GeneratorChunk(delta=delta, answer_text_so_far=''.join(answer_parts))
    except Exception:
        yield GeneratorResult(answer_text=fallback_answer.answer, used_fallback=True)
        return

    answer_text = ''.join(answer_parts).strip()
    if not answer_text:
        yield GeneratorResult(answer_text=fallback_answer.answer, used_fallback=True)
        return
    yield GeneratorResult(answer_text=answer_text, used_fallback=False)


def _build_instance_fact_summary(fact_pack: dict[str, object], reasoning_result: dict[str, object]) -> str:
    instances = fact_pack.get('instances') if isinstance(fact_pack, dict) else {}
    counts = fact_pack.get('counts') if isinstance(fact_pack, dict) else {}
    lines: list[str] = []
    if isinstance(counts, dict) and counts:
        for entity, count in counts.items():
            lines.append(f'- {entity}: {count} ?')
    if isinstance(instances, dict):
        for entity, items in instances.items():
            if not isinstance(items, list) or not items:
                continue
            lines.append(f'- {entity} ??: {items[0]}')

    summary = reasoning_result.get('summary') if isinstance(reasoning_result, dict) else None
    deadline = reasoning_result.get('deadline_assessment') if isinstance(reasoning_result, dict) else None
    if summary:
        lines.append(f'- ????: {summary}')
    if deadline:
        lines.append(f'- ????: {deadline}')

    return '\n'.join(lines)
