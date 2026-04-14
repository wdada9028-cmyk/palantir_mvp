from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

_DEFAULT_MODEL = 'Qwen3.5-35B-A3B'
_DEFAULT_TIMEOUT_S = 60.0
_DEFAULT_MAX_RETRIES = 2
_ALLOWED_DECISIONS = {'select', 'ambiguous', 'reject'}


@dataclass(frozen=True, slots=True)
class AnchorRankDecision:
    decision: str
    selected_candidate_id: str
    confidence: float
    reason: str


@dataclass(frozen=True, slots=True)
class _RankerConfig:
    api_base: str
    api_key: str
    model: str


def build_anchor_candidate_ranker_prompt(
    *,
    question: str,
    schema_markdown: str,
    candidate_context: dict[str, object],
    max_candidates: int = 5,
) -> str:
    normalized_question = str(question or '').strip()
    context_payload = _clip_candidate_context(candidate_context, max_candidates=max_candidates)
    sections = [
        'You are an anchor candidate ranker for ontology-backed instance QA.',
        'Return JSON only.',
        'Allowed decisions: select, ambiguous, reject.',
        'Output fields: decision, selected_candidate_id, confidence, reason.',
        f'Question: {normalized_question}',
        'Schema markdown:',
        str(schema_markdown or '').strip(),
        'Candidate context:',
        json.dumps(context_payload, ensure_ascii=False, indent=2),
    ]
    return "\n\n".join(sections)


def parse_anchor_rank_payload(payload: dict[str, object]) -> AnchorRankDecision:
    decision = str(payload.get('decision', '') or '').strip().lower()
    if decision not in _ALLOWED_DECISIONS:
        raise ValueError(f'Unsupported rank decision: {decision}')

    selected_candidate_id = str(payload.get('selected_candidate_id', '') or '').strip()
    if decision == 'select' and not selected_candidate_id:
        raise ValueError('selected_candidate_id is required when decision=select')

    confidence_raw = payload.get('confidence', 0.0)
    try:
        confidence = float(confidence_raw)
    except Exception as exc:
        raise ValueError('confidence must be numeric') from exc

    reason = str(payload.get('reason', '') or '').strip()

    return AnchorRankDecision(
        decision=decision,
        selected_candidate_id=selected_candidate_id,
        confidence=confidence,
        reason=reason,
    )


def resolve_anchor_candidate_rank(
    *,
    question: str,
    schema_markdown: str,
    candidate_context: dict[str, object],
    max_candidates: int = 5,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
) -> AnchorRankDecision | None:
    config = _load_config()
    if config is None:
        return None

    try:
        response = get_openai_client(timeout_s=timeout_s).chat.completions.create(
            model=config.model,
            temperature=0.0,
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a controlled anchor-candidate ranker. Return JSON only.',
                },
                {
                    'role': 'user',
                    'content': build_anchor_candidate_ranker_prompt(
                        question=question,
                        schema_markdown=schema_markdown,
                        candidate_context=candidate_context,
                        max_candidates=max_candidates,
                    ),
                },
            ],
            timeout=timeout_s,
        )
        content = _extract_message_content(response)
        payload = _parse_json_object(content)
        return parse_anchor_rank_payload(payload)
    except Exception:
        return None


def get_openai_client(timeout_s: float = _DEFAULT_TIMEOUT_S) -> Any:
    from openai import OpenAI

    config = _load_config()
    if config is None:
        raise RuntimeError('Missing QWEN_API_BASE or QWEN_API_KEY.')

    return OpenAI(
        api_key=config.api_key,
        base_url=config.api_base.rstrip('/'),
        max_retries=_DEFAULT_MAX_RETRIES,
        timeout=timeout_s,
    )


def _load_config() -> _RankerConfig | None:
    api_base = os.getenv('QWEN_API_BASE', '').strip()
    api_key = os.getenv('QWEN_API_KEY', '').strip()
    if not api_base or not api_key:
        return None

    model = os.getenv('QWEN_ANCHOR_RANKER_MODEL', '').strip() or _DEFAULT_MODEL
    return _RankerConfig(api_base=api_base, api_key=api_key, model=model)


def _clip_candidate_context(candidate_context: dict[str, object], *, max_candidates: int) -> dict[str, object]:
    payload = dict(candidate_context or {})
    candidates = payload.get('candidates')
    if not isinstance(candidates, list):
        payload['candidates'] = []
        return payload

    limit = max(0, int(max_candidates))
    payload['candidates'] = [item for item in candidates[:limit] if isinstance(item, dict)]
    return payload


def _extract_message_content(payload: Any) -> str:
    if isinstance(payload, dict):
        choices = payload.get('choices')
    else:
        choices = getattr(payload, 'choices', None)
    if not isinstance(choices, list) or not choices:
        raise ValueError('Invalid response payload: missing choices.')

    first_choice = choices[0]
    if isinstance(first_choice, dict):
        message = first_choice.get('message')
    else:
        message = getattr(first_choice, 'message', None)
    if message is None:
        raise ValueError('Invalid response payload: missing message.')

    if isinstance(message, dict):
        content = message.get('content', '')
    else:
        content = getattr(message, 'content', '')

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text = str(item.get('text', '') or '').strip()
                else:
                    text = ''
            else:
                item_type = getattr(item, 'type', None)
                text = str(getattr(item, 'text', '') or '').strip() if item_type == 'text' else ''
            if text:
                parts.append(text)
        content = ''.join(parts)

    if not isinstance(content, str) or not content.strip():
        raise ValueError('Invalid response payload: missing message content.')
    return content.strip()


def _parse_json_object(content: str) -> dict[str, object]:
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError('Ranker output must be a JSON object.')
    return parsed
