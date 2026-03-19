from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, AsyncIterator

from .template_answering import TemplateAnswer, _dedupe_trace_steps, _display_name, _relation_name
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
        f'{_display_name(bundle, step.from_node_id)} {_relation_name(bundle, step.relation)} {_display_name(bundle, step.to_node_id)}'
        for step in _dedupe_trace_steps(bundle.search_trace.expansion_steps)
    ]
    if fact_lines:
        return _dedupe_preserve_order(fact_lines)

    fallback_lines: list[str] = []
    for item in bundle.evidence_chain:
        if item.kind != 'relation' or len(item.node_ids) < 2:
            continue
        fallback_lines.append(
            f'{_display_name(bundle, item.node_ids[0])} [关联] {_display_name(bundle, item.node_ids[1])}'
        )
    return _dedupe_preserve_order(fallback_lines)


def _build_messages(question: str, fact_lines: list[str]) -> list[dict[str, str]]:
    facts_block = '\n'.join(f'- {line}' for line in fact_lines)
    return [
        {
            'role': 'system',
            'content': (
                '你是云交付本体问答助手。'
                '只能根据提供的本体事实回答，不得编造关系。'
                '输出尽量简洁，优先直接给出结论。'
                '必须严格保留实体字符串原样，不得改写中文名(ID)格式。'
                '如果事实不足，请明确说明证据不足。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'用户问题：{question}\n\n'
                '仅可使用以下本体事实：\n'
                f'{facts_block}\n\n'
                '请基于这些事实直接回答。'
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
