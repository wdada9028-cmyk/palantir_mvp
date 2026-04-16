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
_ROUTER_PROMPT_VERSION = 'v1'
_ROUTER_PROMPT_PREFIX_CACHE: dict[str, str] = {}
_SYSTEM_ROUTER_INSTRUCTION = '????????????????? JSON?'
_EXPLICIT_CACHE_SUPPORTED_MODELS = frozenset({
    'qwen3-max',
    'qwen3.6-plus',
    'qwen3.5-plus',
    'qwen-plus',
    'qwen3.5-flash',
    'qwen-flash',
    'qwen3-coder-plus',
    'qwen3-coder-flash',
    'qwen3-vl-plus',
    'qwen3-vl-flash',
    'deepseek-v3.2',
    'kimi-k2.5',
    'glm-5.1',
})


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


def build_question_router_prompt_prefix(
    schema_registry: SchemaRegistry,
    *,
    schema_markdown: str = '',
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
            'question': 'POD-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f',
            'output': {
                'intent': 'attribute_lookup',
                'anchor_entity': 'PoD',
                'anchor_locator': {'match_type': 'key_attribute', 'attribute': 'pod_id', 'value': 'POD-001'},
                'target_attributes': ['pod_status'],
                'reasoning_scope': 'anchor_only',
                'confidence': 0.97,
                'why': '\u7528\u6237\u5728\u8be2\u95ee\u67d0\u4e2a\u5177\u4f53\u5b9e\u4f8b\u7684\u5355\u4e00\u5c5e\u6027\u3002',
            },
        },
        {
            'question': 'L1-A\u673a\u623f\u65ad\u7535\u4e00\u5468\uff0c\u4f1a\u6709\u54ea\u4e9b\u5f71\u54cd\uff1f',
            'output': {
                'intent': 'impact_analysis',
                'anchor_entity': 'Room',
                'anchor_locator': {'match_type': 'key_attribute', 'attribute': 'room_id', 'value': 'L1-A'},
                'target_attributes': [],
                'reasoning_scope': 'expand_graph',
                'confidence': 0.96,
                'why': '\u7528\u6237\u5728\u8be2\u95ee\u4e0b\u6e38\u5f71\u54cd\u5206\u6790\uff0c\u800c\u4e0d\u662f\u5355\u4e00\u5b57\u6bb5\u503c\u3002',
            },
        },
    ]
    payload = {
        'allowed_intents': list(_ALLOWED_INTENTS),
        'allowed_match_types': list(_ALLOWED_MATCH_TYPES),
        'allowed_reasoning_scopes': list(_ALLOWED_SCOPES),
        'schema_entities': schema_payload,
        'examples': examples,
    }
    sections = [
        '\u4f60\u662f\u4e00\u4e2a\u9762\u5411\u672c\u4f53\u9a71\u52a8\u5b9e\u4f8b\u95ee\u7b54\u7cfb\u7edf\u7684\u95ee\u9898\u8def\u7531\u5668\u3002',
        '\u53ea\u80fd\u8fd4\u56de JSON\u3002',
        'anchor_entity \u548c target_attributes \u53ea\u80fd\u4ece\u63d0\u4f9b\u7684 schema \u4e2d\u9009\u62e9\u3002',
        '\u5f53\u7528\u6237\u8be2\u95ee\u67d0\u4e2a\u5177\u4f53\u5b9e\u4f8b\u7684\u5355\u4e00\u5c5e\u6027\u6216\u72b6\u6001\u65f6\uff0c\u4f7f\u7528 attribute_lookup + anchor_only\u3002',
        '\u5f53\u7528\u6237\u8be2\u95ee\u5f71\u54cd\u3001\u4f9d\u8d56\u3001\u5173\u7cfb\u6216\u591a\u8df3\u4e0a\u4e0b\u6587\u65f6\uff0c\u4f7f\u7528 impact_analysis / relation_query / instance_lookup + expand_graph\u3002',
        '\u53d7\u63a7\u8f93\u5165\uff1a',
        json.dumps(payload, ensure_ascii=False, indent=2),
    ]
    if schema_markdown.strip():
        sections.extend(['Schema \u8bf4\u660e\uff1a', schema_markdown.strip()])
    return '\n\n'.join(sections)



def build_question_router_prompt_suffix(
    raw_query: str,
    *,
    anchor_resolution_payload: dict[str, object] | None = None,
) -> str:
    sections = [
        f'\u5f53\u524d\u7528\u6237\u95ee\u9898\uff1a{raw_query}',
    ]
    if anchor_resolution_payload:
        sections.extend([
            '\u951a\u70b9\u5019\u9009\u89e3\u6790\u7ed3\u679c\uff1a',
            json.dumps(anchor_resolution_payload, ensure_ascii=False, indent=2),
            '\u5982\u679c anchor_resolution_payload.selection.decision \u662f "select"\uff0c\u4e14 confidence_tier \u662f "high"\uff0c\u4f18\u5148\u91c7\u7528 anchor_resolution_payload.selected \u4f5c\u4e3a anchor_locator\u3002',
            '\u5982\u679c anchor_resolution_payload.selection.decision \u662f "ambiguous"\uff0c\u4e0d\u8981\u5f3a\u884c\u9009\u62e9\u67d0\u4e2a\u951a\u70b9\uff0c\u8fd4\u56de\u4fdd\u5b88\u8def\u7531\u3002',
            '\u5982\u679c anchor_resolution_payload.selection \u7f3a\u5931\uff0c\u5219\u9000\u56de\u5230 schema + \u95ee\u9898\u8bed\u4e49\u7406\u89e3\u3002',
        ])
    return '\n\n'.join(sections)



def _router_prompt_prefix_cache_key(schema_markdown: str) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(_ROUTER_PROMPT_VERSION.encode('utf-8'))
    digest.update(b'\n')
    digest.update(schema_markdown.encode('utf-8'))
    return digest.hexdigest()



def get_cached_question_router_prompt_prefix(
    schema_registry: SchemaRegistry,
    *,
    schema_markdown: str = '',
) -> str:
    cache_key = _router_prompt_prefix_cache_key(schema_markdown)
    cached = _ROUTER_PROMPT_PREFIX_CACHE.get(cache_key)
    if cached is not None:
        return cached
    prefix = build_question_router_prompt_prefix(schema_registry, schema_markdown=schema_markdown)
    _ROUTER_PROMPT_PREFIX_CACHE[cache_key] = prefix
    return prefix



def build_question_router_prompt(
    schema_registry: SchemaRegistry,
    raw_query: str,
    *,
    schema_markdown: str = '',
    anchor_resolution_payload: dict[str, object] | None = None,
) -> str:
    prefix = get_cached_question_router_prompt_prefix(schema_registry, schema_markdown=schema_markdown)
    suffix = build_question_router_prompt_suffix(
        raw_query,
        anchor_resolution_payload=anchor_resolution_payload,
    )
    return '\n\n'.join(part for part in (prefix, suffix) if part.strip())



def _supports_explicit_prompt_cache(model: str) -> bool:
    return model.strip().lower() in _EXPLICIT_CACHE_SUPPORTED_MODELS



def build_question_router_messages(
    schema_registry: SchemaRegistry,
    raw_query: str,
    *,
    model: str,
    schema_markdown: str = '',
    anchor_resolution_payload: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    prefix = get_cached_question_router_prompt_prefix(schema_registry, schema_markdown=schema_markdown)
    suffix = build_question_router_prompt_suffix(
        raw_query,
        anchor_resolution_payload=anchor_resolution_payload,
    )
    if _supports_explicit_prompt_cache(model):
        user_content: object = [
            {'type': 'text', 'text': prefix, 'cache_control': {'type': 'ephemeral'}},
            {'type': 'text', 'text': suffix},
        ]
    else:
        user_content = '\n\n'.join(part for part in (prefix, suffix) if part.strip())
    return [
        {'role': 'system', 'content': _SYSTEM_ROUTER_INSTRUCTION},
        {'role': 'user', 'content': user_content},
    ]



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
            messages=build_question_router_messages(
                schema_registry,
                raw_query,
                model=config.model,
                schema_markdown=schema_markdown,
                anchor_resolution_payload=anchor_resolution_payload,
            ),
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
