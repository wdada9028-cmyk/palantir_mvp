from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schema_registry import SchemaRegistry

_ALLOWED_INTENTS = ('attribute_lookup', 'impact_analysis', 'relation_query', 'instance_lookup')
_ALLOWED_MATCH_TYPES = ('key_attribute', 'attribute', 'name', 'alias', 'unknown')
_ALLOWED_SCOPES = ('anchor_only', 'expand_graph')
_DEFAULT_MODEL = 'qwen3.6-plus'
_DEFAULT_TIMEOUT_S = 120.0
_DEFAULT_MAX_RETRIES = 2


@dataclass(frozen=True, slots=True)
class AnchorLocator:
    match_type: str
    attribute: str | None
    value: str


@dataclass(frozen=True, slots=True)
class QuestionRoute:
    intent: str
    anchor_entity: str
    anchor_locator: AnchorLocator
    target_attributes: list[str] = field(default_factory=list)
    reasoning_scope: str = 'expand_graph'
    confidence: float = 0.0
    why: str = ''


@dataclass(frozen=True, slots=True)
class QuestionRouteResolution:
    status: str
    error_type: str
    error_message: str
    route: QuestionRoute | None


@dataclass(frozen=True, slots=True)
class _RouterConfig:
    api_base: str
    api_key: str
    model: str


def parse_question_route_payload(payload: dict[str, object]) -> QuestionRoute:
    locator_payload = payload.get('anchor_locator') if isinstance(payload, dict) else None
    if not isinstance(locator_payload, dict):
        raise ValueError('Question route payload is missing anchor_locator.')

    target_attributes = payload.get('target_attributes', []) if isinstance(payload, dict) else []
    if not isinstance(target_attributes, list):
        raise ValueError('Question route payload target_attributes must be a list.')

    confidence_raw = payload.get('confidence', 0.0) if isinstance(payload, dict) else 0.0
    try:
        confidence = float(confidence_raw)
    except Exception as exc:
        raise ValueError('Question route payload confidence must be numeric.') from exc

    return QuestionRoute(
        intent=str(payload.get('intent', '') or '').strip(),
        anchor_entity=str(payload.get('anchor_entity', '') or '').strip(),
        anchor_locator=AnchorLocator(
            match_type=str(locator_payload.get('match_type', '') or '').strip(),
            attribute=_optional_text(locator_payload.get('attribute')),
            value=str(locator_payload.get('value', '') or '').strip(),
        ),
        target_attributes=[str(item).strip() for item in target_attributes if str(item).strip()],
        reasoning_scope=str(payload.get('reasoning_scope', '') or '').strip(),
        confidence=confidence,
        why=str(payload.get('why', '') or '').strip(),
    )


def validate_question_route(route: QuestionRoute, schema_registry: SchemaRegistry) -> str | None:
    if route.intent not in _ALLOWED_INTENTS:
        return f'Unsupported route intent: {route.intent}'
    if route.reasoning_scope not in _ALLOWED_SCOPES:
        return f'Unsupported reasoning scope: {route.reasoning_scope}'
    if route.anchor_entity not in schema_registry.entities:
        return f'Unknown route anchor entity: {route.anchor_entity}'
    if route.anchor_locator.match_type not in _ALLOWED_MATCH_TYPES:
        return f'Unsupported anchor locator match type: {route.anchor_locator.match_type}'
    if not route.anchor_locator.value:
        return 'Route anchor locator value must not be empty.'

    entity = schema_registry.entities[route.anchor_entity]
    attribute = route.anchor_locator.attribute
    if route.anchor_locator.match_type == 'key_attribute':
        if not attribute or attribute not in entity.key_attributes:
            return f'Route anchor locator attribute {attribute!r} must be a key attribute for entity {route.anchor_entity}'
    elif route.anchor_locator.match_type == 'attribute':
        if not attribute or attribute not in entity.attributes:
            return f'Route anchor locator attribute {attribute!r} is not valid for entity {route.anchor_entity}'

    invalid_target_attributes = [item for item in route.target_attributes if item not in entity.attributes]
    if invalid_target_attributes:
        return f"Unknown target attributes for {route.anchor_entity}: {', '.join(invalid_target_attributes)}"

    if route.intent == 'attribute_lookup':
        if route.reasoning_scope != 'anchor_only':
            return 'attribute_lookup must use anchor_only reasoning scope.'
        if not route.target_attributes:
            return 'attribute_lookup must provide target_attributes.'

    return None


def build_question_router_prompt(
    schema_registry: SchemaRegistry,
    raw_query: str,
    *,
    schema_markdown: str = '',
    anchor_resolution_payload: dict[str, object] | None = None,
) -> str:
    schema_payload = {
        entity_name: {
            'key_attributes': list(entity.key_attributes),
            'attributes': list(entity.attributes),
            'zh_label': entity.zh_label,
        }
        for entity_name, entity in sorted(schema_registry.entities.items())
    }
    examples = [
        {
            'question': 'POD-001???????',
            'output': {
                'intent': 'attribute_lookup',
                'anchor_entity': 'PoD',
                'anchor_locator': {'match_type': 'key_attribute', 'attribute': 'pod_id', 'value': 'POD-001'},
                'target_attributes': ['pod_status'],
                'reasoning_scope': 'anchor_only',
                'confidence': 0.97,
                'why': '?????????????????',
            },
        },
        {
            'question': 'L1-A??????????????',
            'output': {
                'intent': 'impact_analysis',
                'anchor_entity': 'Room',
                'anchor_locator': {'match_type': 'key_attribute', 'attribute': 'room_id', 'value': 'L1-A'},
                'target_attributes': [],
                'reasoning_scope': 'expand_graph',
                'confidence': 0.96,
                'why': '?????????????????????',
            },
        },
    ]
    payload = {
        'allowed_intents': list(_ALLOWED_INTENTS),
        'allowed_match_types': list(_ALLOWED_MATCH_TYPES),
        'allowed_reasoning_scopes': list(_ALLOWED_SCOPES),
        'schema_entities': schema_payload,
        'examples': examples,
        'query': raw_query,
    }
    sections = [
        '???????????????????????',
        '???? JSON?',
        'anchor_entity ? target_attributes ?????? schema ????',
        '??????????????????????? attribute_lookup + anchor_only?',
        '??????????????????????? impact_analysis / relation_query / instance_lookup + expand_graph?',
        '?????',
        json.dumps(payload, ensure_ascii=False, indent=2),
    ]
    if anchor_resolution_payload:
        sections.extend([
            '?????????',
            json.dumps(anchor_resolution_payload, ensure_ascii=False, indent=2),
            '?? anchor_resolution_payload.selection.decision ? "select"?? confidence_tier ? "high"????? anchor_resolution_payload.selected ?? anchor_locator?',
            '?? anchor_resolution_payload.selection.decision ? "ambiguous"???????????????????',
            '?? anchor_resolution_payload.selection ??????? schema + ???????',
        ])
    if schema_markdown.strip():
        sections.extend(['Schema ???', schema_markdown.strip()])
    return '\\n\\n'.join(sections)



def resolve_question_route(
    raw_query: str,
    schema_registry: SchemaRegistry,
    *,
    schema_markdown: str = '',
    anchor_resolution_payload: dict[str, object] | None = None,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
) -> QuestionRouteResolution:
    config = _load_config()
    if config is None:
        return _failed_route_resolution('router_not_configured', 'Missing QWEN_API_BASE or QWEN_API_KEY.')

    try:
        response = get_openai_client(timeout_s=timeout_s).chat.completions.create(
            model=config.model,
            temperature=0.0,
            response_format={'type': 'json_object'},
            messages=[
                {
                    'role': 'system',
                    'content': '????????????????? JSON?',
                },
                {
                    'role': 'user',
                    'content': build_question_router_prompt(
                        schema_registry,
                        raw_query,
                        schema_markdown=schema_markdown,
                        anchor_resolution_payload=anchor_resolution_payload,
                    ),
                },
            ],
            timeout=timeout_s,
        )
        content = _extract_message_content(response)
        parsed = _parse_json_object(content)
        route = parse_question_route_payload(parsed)
    except json.JSONDecodeError as exc:
        return _failed_route_resolution('router_invalid_json', f'Router output is not valid JSON: {exc}')
    except ValueError as exc:
        return _failed_route_resolution('router_invalid_payload', str(exc))
    except Exception as exc:
        if _looks_like_timeout_error(exc):
            return _failed_route_resolution('router_timeout', str(exc) or 'Router request timed out.')
        if _looks_like_connect_error(exc):
            return _failed_route_resolution('router_connect_error', str(exc) or 'Router connection failed.')
        return _failed_route_resolution('router_unknown_error', str(exc) or type(exc).__name__)

    validation_error = validate_question_route(route, schema_registry)
    if validation_error is not None:
        return _failed_route_resolution('router_validation_failed', validation_error)
    return QuestionRouteResolution(status='ok', error_type='', error_message='', route=route)



def _failed_route_resolution(error_type: str, error_message: str) -> QuestionRouteResolution:
    return QuestionRouteResolution(status='failed', error_type=error_type, error_message=error_message, route=None)


def _looks_like_timeout_error(exc: Exception) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    return 'timeout' in name or 'timed out' in message or 'timeout' in message


def _looks_like_connect_error(exc: Exception) -> bool:
    if isinstance(exc, ConnectionError):
        return True
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    return 'connect' in name or 'connection' in message

def load_schema_markdown(path: str | Path | None) -> str:
    if path is None:
        return ''
    candidate = Path(path)
    if not candidate.exists() or candidate.suffix.lower() != '.md':
        return ''
    try:
        return candidate.read_text(encoding='utf-8')
    except Exception:
        return ''


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


def _load_config() -> _RouterConfig | None:
    api_base = os.getenv('QWEN_API_BASE', '').strip()
    api_key = os.getenv('QWEN_API_KEY', '').strip()
    if not api_base or not api_key:
        return None
    return _RouterConfig(
        api_base=api_base,
        api_key=api_key,
        model=_get_env('QWEN_ROUTER_MODEL', 'QWEN_MODEL') or _DEFAULT_MODEL,
    )


def _get_env(primary: str, fallback: str) -> str:
    value = os.getenv(primary, '').strip()
    if value:
        return value
    return os.getenv(fallback, '').strip()


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
        raise ValueError('Router output must be a JSON object.')
    return parsed


def _optional_text(value: object) -> str | None:
    text = str(value or '').strip()
    return text or None
