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
            f'{_summary_name(bundle, item.node_ids[0])} [关联] {_summary_name(bundle, item.node_ids[1])}'
        )
    return _dedupe_preserve_order(fallback_lines)


def _build_messages(question: str, fact_lines: list[str]) -> list[dict[str, str]]:
    facts_block = '\n'.join(f'- {line}' for line in fact_lines)
    return [
        {
            'role': 'system',
            'content': (
                '你是云交付本体问答助手。'
                '只能根据提供的本体事实生成面向用户的答案摘要，不得编造关系。'
                '不要复述检索路径，不要描述从哪个节点扩展到哪个节点。'
                '重点总结哪些对象受影响、为什么受影响、影响表现在哪里。'
                '输出通顺自然的中文，可以合并多条关系形成更高层结论。'
                '不要输出英文实体名，不要输出证据编号。'
                '如果事实不足，请明确说明证据不足。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'用户问题：{question}\n\n'
                '仅可使用以下本体事实：\n'
                f'{facts_block}\n\n'
                '请基于这些事实生成答案摘要。'
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
                    'content': (
                        '你是云交付实例问答助手。'
                        '请结合 schema 摘要与事实包，用中文给出准确、简洁、可执行的结论。'
                        '不得虚构事实，证据不足时要明确说明。'
                    ),
                },
                {
                    'role': 'user',
                    'content': (
                        f'用户问题：{question}\n\n'
                        f'Schema 摘要：{schema_summary}\n\n'
                        f'事实与推理：\n{fact_summary}\n\n'
                        '请输出最终回答。'
                    ),
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
            lines.append(f'- {entity}：{count} 条')
    if isinstance(instances, dict):
        for entity, items in instances.items():
            if not isinstance(items, list) or not items:
                continue
            lines.append(f'- {entity} 示例：{items[0]}')

    summary = reasoning_result.get('summary') if isinstance(reasoning_result, dict) else None
    deadline = reasoning_result.get('deadline_assessment') if isinstance(reasoning_result, dict) else None
    if summary:
        lines.append(f'- 推理摘要：{summary}')
    if deadline:
        lines.append(f'- 截止评估：{deadline}')

    return '\n'.join(lines)
