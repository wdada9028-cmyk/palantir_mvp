from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..models.ontology import OntologyGraph, OntologyObject

_DEFAULT_MODEL = 'qwen2.5-32b-instruct'
_HTTP_CLIENT: httpx.Client | None = None


@dataclass(slots=True)
class IntentResolution:
    seeds: list[str] = field(default_factory=list)
    reasoning: str = ''
    source: str = 'fallback'
    error: str = ''


@dataclass(slots=True)
class _IntentResolverConfig:
    api_base: str
    api_key: str
    model: str


def resolve_intent(
    graph: OntologyGraph,
    query: str,
    *,
    candidate_ids: list[str] | None = None,
    timeout_s: float = 3.0,
) -> IntentResolution:
    config = _load_config()
    if config is None:
        return IntentResolution(
            seeds=[],
            reasoning='',
            source='disabled',
            error='Missing QWEN_API_BASE or QWEN_API_KEY.',
        )

    if candidate_ids is None:
        object_ids = {obj.id for obj in _iter_prompt_objects(graph)}
        success_source = 'llm'
    else:
        candidate_id_set = {str(item) for item in candidate_ids if isinstance(item, str)}
        object_ids = {obj.id for obj in _iter_prompt_objects(graph) if obj.id in candidate_id_set}
        success_source = 'llm_candidate_select'
    if not object_ids:
        return IntentResolution(
            seeds=[],
            reasoning='',
            source='fallback',
            error='No ontology object types available for intent resolution.',
        )

    payload = {
        'model': config.model,
        'temperature': 0.1,
        'response_format': {'type': 'json_object'},
        'messages': [
            {
                'role': 'system',
                'content': (
                    'You map user questions to ontology entity IDs. '
                    'Return strict JSON with keys "seeds" and "reasoning". '
                    'If nothing matches the provided ontology list, return {"seeds": [], "reasoning": ""}. '
                    'Do not invent IDs.'
                ),
            },
            {
                'role': 'user',
                'content': _build_prompt(graph, query, object_ids=object_ids),
            },
        ],
    }

    try:
        response = get_http_client().post(
            f'{config.api_base.rstrip("/")}/chat/completions',
            headers={'Authorization': f'Bearer {config.api_key}'},
            json=payload,
            timeout=timeout_s,
        )
        response.raise_for_status()
        content = _extract_message_content(response.json())
        parsed = _parse_response_content(content)
        reasoning = str(parsed.get('reasoning', '') or '').strip()
        raw_seeds = parsed.get('seeds', [])
        if not isinstance(raw_seeds, list):
            return IntentResolution(
                seeds=[],
                reasoning=reasoning,
                source='fallback',
                error='Invalid JSON: seeds must be a list.',
            )
        filtered = _dedupe_preserve_order(
            seed for seed in raw_seeds if isinstance(seed, str) and seed in object_ids
        )
        if not filtered:
            return IntentResolution(
                seeds=[],
                reasoning=reasoning,
                source='fallback',
                error='Resolver returned no valid ontology seed IDs.',
            )
        return IntentResolution(seeds=filtered, reasoning=reasoning, source=success_source, error='')
    except Exception as exc:
        return IntentResolution(seeds=[], reasoning='', source='fallback', error=_format_error(exc))


def get_http_client() -> httpx.Client:
    global _HTTP_CLIENT
    if _HTTP_CLIENT is None:
        _HTTP_CLIENT = httpx.Client(
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=2, keepalive_expiry=30.0),
        )
    return _HTTP_CLIENT


def _load_config() -> _IntentResolverConfig | None:
    api_base = os.getenv('QWEN_API_BASE', '').strip()
    api_key = os.getenv('QWEN_API_KEY', '').strip()
    if not api_base or not api_key:
        return None
    return _IntentResolverConfig(
        api_base=api_base,
        api_key=api_key,
        model=os.getenv('QWEN_MODEL', _DEFAULT_MODEL).strip() or _DEFAULT_MODEL,
    )


def _build_prompt(graph: OntologyGraph, query: str, *, object_ids: set[str] | None = None) -> str:
    ontology_text = _build_schema_summary(graph, object_ids=object_ids)
    return (
        f'User question: {query}\n\n'
        'Ontology entities:\n'
        f'{ontology_text}\n\n'
        'Return JSON only, in the form {"seeds": ["object_type:Example"], "reasoning": "short reason"}.\n'
        'Only use IDs from the ontology entities list. If there is no match, return an empty seeds list.'
    )


def _build_schema_summary(graph: OntologyGraph, *, object_ids: set[str] | None = None) -> str:
    lines: list[str] = []
    for obj in _iter_prompt_objects(graph):
        if object_ids is not None and obj.id not in object_ids:
            continue
        description = str(obj.attributes.get('chinese_description', '') or '').strip()
        if not description:
            description = str(obj.name or obj.id.split(':', 1)[-1]).strip() or obj.id
        lines.append(f'id={obj.id}; chinese_description={description}')
    return '\n'.join(_dedupe_preserve_order(lines))


def _iter_prompt_objects(graph: OntologyGraph) -> list[OntologyObject]:
    return sorted(
        (obj for obj in graph.objects.values() if obj.type == 'ObjectType'),
        key=lambda obj: obj.id,
    )


def _extract_message_content(payload: dict[str, Any]) -> str:
    choices = payload.get('choices')
    if not isinstance(choices, list) or not choices:
        raise ValueError('Invalid response payload: missing choices.')
    message = choices[0].get('message')
    if not isinstance(message, dict):
        raise ValueError('Invalid response payload: missing message.')
    content = message.get('content', '')
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                text = str(item.get('text', '') or '').strip()
                if text:
                    parts.append(text)
        content = ''.join(parts)
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Invalid response payload: missing message content.')
    return content.strip()


def _parse_response_content(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid JSON: {exc.msg}') from exc
    if not isinstance(parsed, dict):
        raise ValueError('Invalid JSON: top-level object must be a dictionary.')
    return parsed


def _format_error(exc: Exception) -> str:
    if isinstance(exc, ValueError):
        return str(exc)
    return f'{type(exc).__name__}: {exc}'


def _dedupe_preserve_order(values: list[str] | Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
