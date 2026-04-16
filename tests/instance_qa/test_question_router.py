from cloud_delivery_ontology_palantir.instance_qa.question_router import (
    _load_config,
    build_question_router_prompt,
    get_openai_client,
    parse_question_route_payload,
    validate_question_route,
)
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry


def _schema_registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            'Room': SchemaEntity(name='Room', object_id='object_type:Room', attributes=['room_id', 'room_status'], key_attributes=['room_id']),
            'PoD': SchemaEntity(name='PoD', object_id='object_type:PoD', attributes=['pod_id', 'pod_status'], key_attributes=['pod_id']),
        },
        relations=[],
        adjacency={
            'Room': [SchemaAdjacency(entity='Room', relation='OCCURS_IN', direction='in', neighbor_entity='WorkAssignment')],
            'PoD': [],
        },
    )


def test_parse_question_route_payload_supports_anchor_locator_and_reasoning_scope():
    payload = {
        'intent': 'attribute_lookup',
        'anchor_entity': 'PoD',
        'anchor_locator': {
            'match_type': 'key_attribute',
            'attribute': 'pod_id',
            'value': 'POD-001',
        },
        'target_attributes': ['pod_status'],
        'reasoning_scope': 'anchor_only',
        'confidence': 0.97,
    }

    result = parse_question_route_payload(payload)

    assert result.intent == 'attribute_lookup'
    assert result.anchor_entity == 'PoD'
    assert result.anchor_locator.attribute == 'pod_id'
    assert result.anchor_locator.value == 'POD-001'
    assert result.target_attributes == ['pod_status']
    assert result.reasoning_scope == 'anchor_only'
    assert result.confidence == 0.97


def test_build_question_router_prompt_embeds_schema_markdown_verbatim():
    schema_markdown = """# typedb_schema_v4

## Object Types????

### `PoD`

?????PoD
?????
- `pod_id`?PoD ID
- `pod_status`?PoD??
"""

    prompt = build_question_router_prompt(_schema_registry(), 'POD-001???????', schema_markdown=schema_markdown)

    assert 'Schema \u8bf4\u660e\uff1a' in prompt
    assert '## Object Types????' in prompt
    assert '?????PoD' in prompt
    assert '- `pod_status`?PoD??' in prompt


def test_build_question_router_prompt_mentions_anchor_only_and_expand_graph():
    prompt = build_question_router_prompt(_schema_registry(), 'POD-001的状态是什么？')

    assert 'attribute_lookup' in prompt
    assert 'impact_analysis' in prompt
    assert 'anchor_only' in prompt
    assert 'expand_graph' in prompt
    assert 'POD-001的状态是什么？' in prompt
    assert 'pod_status' in prompt
    assert 'room_status' in prompt


def test_validate_question_route_rejects_unknown_target_attribute():
    route = parse_question_route_payload({
        'intent': 'attribute_lookup',
        'anchor_entity': 'PoD',
        'anchor_locator': {
            'match_type': 'key_attribute',
            'attribute': 'pod_id',
            'value': 'POD-001',
        },
        'target_attributes': ['room_status'],
        'reasoning_scope': 'anchor_only',
        'confidence': 0.91,
    })

    error = validate_question_route(route, _schema_registry())

    assert 'room_status' in error


def test_question_router_defaults_to_qwen36_plus(monkeypatch):
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.delenv('QWEN_MODEL', raising=False)
    monkeypatch.delenv('QWEN_ROUTER_MODEL', raising=False)

    config = _load_config()

    assert config is not None
    assert config.model == 'qwen3.6-plus'



def test_get_openai_client_uses_router_timeout_and_retries(monkeypatch):
    import sys
    from types import SimpleNamespace

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    captured = {}

    class FakeOpenAI:
        def __init__(self, *, api_key, base_url, max_retries, timeout):
            captured['api_key'] = api_key
            captured['base_url'] = base_url
            captured['max_retries'] = max_retries
            captured['timeout'] = timeout

    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(OpenAI=FakeOpenAI))

    client = get_openai_client(timeout_s=120.0)

    assert client is not None
    assert captured == {
        'api_key': 'test-key',
        'base_url': 'https://example.com/v1',
        'max_retries': 2,
        'timeout': 120.0,
    }


def test_resolve_question_route_uses_openai_client_and_router_timeout_120_seconds(monkeypatch):
    from types import SimpleNamespace
    from cloud_delivery_ontology_palantir.instance_qa.question_router import resolve_question_route

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"intent": "attribute_lookup", "anchor_entity": "PoD", "anchor_locator": {"match_type": "key_attribute", "attribute": "pod_id", "value": "POD-001"}, "target_attributes": ["pod_status"], "reasoning_scope": "anchor_only", "confidence": 0.97}'
                        )
                    )
                ]
            )

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=FakeCompletions()
        )
    )

    monkeypatch.setattr('cloud_delivery_ontology_palantir.instance_qa.question_router.get_openai_client', lambda timeout_s=120.0: fake_client)

    resolution = resolve_question_route('POD-001???????', _schema_registry(), schema_markdown='# schema')

    assert resolution.status == 'ok'
    assert resolution.error_type == ''
    assert resolution.error_message == ''
    assert resolution.route is not None
    assert captured['model'] == 'qwen3.6-plus'
    assert captured['temperature'] == 0.0
    assert captured['response_format'] == {'type': 'json_object'}
    assert captured['timeout'] == 120.0



def test_resolve_question_route_uses_explicit_prompt_cache_for_supported_model(monkeypatch):
    from types import SimpleNamespace
    from cloud_delivery_ontology_palantir.instance_qa.question_router import resolve_question_route

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.setenv('QWEN_ROUTER_MODEL', 'qwen3.6-plus')
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"intent": "attribute_lookup", "anchor_entity": "PoD", "anchor_locator": {"match_type": "key_attribute", "attribute": "pod_id", "value": "POD-001"}, "target_attributes": ["pod_status"], "reasoning_scope": "anchor_only", "confidence": 0.97}'
                        )
                    )
                ]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr('cloud_delivery_ontology_palantir.instance_qa.question_router.get_openai_client', lambda timeout_s=120.0: fake_client)

    resolution = resolve_question_route('POD-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f', _schema_registry(), schema_markdown='# schema markdown')

    assert resolution.status == 'ok'
    user_content = captured['messages'][1]['content']
    assert isinstance(user_content, list)
    assert user_content[0]['type'] == 'text'
    assert user_content[0]['cache_control'] == {'type': 'ephemeral'}
    assert '\u53d7\u63a7\u8f93\u5165\uff1a' in user_content[0]['text']
    assert user_content[1]['type'] == 'text'
    assert '\u5f53\u524d\u7528\u6237\u95ee\u9898\uff1aPOD-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f' in user_content[1]['text']



def test_resolve_question_route_skips_explicit_prompt_cache_for_unsupported_model(monkeypatch):
    from types import SimpleNamespace
    from cloud_delivery_ontology_palantir.instance_qa.question_router import resolve_question_route

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.setenv('QWEN_ROUTER_MODEL', 'custom-router-model')
    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"intent": "attribute_lookup", "anchor_entity": "PoD", "anchor_locator": {"match_type": "key_attribute", "attribute": "pod_id", "value": "POD-001"}, "target_attributes": ["pod_status"], "reasoning_scope": "anchor_only", "confidence": 0.97}'
                        )
                    )
                ]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr('cloud_delivery_ontology_palantir.instance_qa.question_router.get_openai_client', lambda timeout_s=120.0: fake_client)

    resolution = resolve_question_route('POD-001???????', _schema_registry(), schema_markdown='# schema markdown')

    assert resolution.status == 'ok'
    assert isinstance(captured['messages'][1]['content'], str)

def test_build_question_router_prompt_embeds_anchor_resolution_payload_when_present():
    prompt = build_question_router_prompt(
        _schema_registry(),
        'pod-001???????',
        anchor_resolution_payload={
            'raw_anchor_text': 'pod-001',
            'match_stage': 'light',
            'selected': {
                'entity': 'PoD',
                'attribute': 'pod_id',
                'value': 'POD-001',
            },
            'candidates': [
                {
                    'entity': 'PoD',
                    'attribute': 'pod_id',
                    'value': 'POD-001',
                }
            ],
        },
    )

    assert '\u951a\u70b9\u5019\u9009\u89e3\u6790\u7ed3\u679c\uff1a' in prompt
    assert '"raw_anchor_text": "pod-001"' in prompt
    assert '"match_stage": "light"' in prompt
    assert '"value": "POD-001"' in prompt


def test_build_question_router_prompt_adds_selection_decision_guidance_when_selection_present():
    prompt = build_question_router_prompt(
        _schema_registry(),
        'pod-001???????',
        anchor_resolution_payload={
            'raw_anchor_text': 'pod-001',
            'match_stage': 'loose',
            'selection': {
                'decision': 'select',
                'confidence': 0.93,
                'confidence_tier': 'high',
                'reason': 'best match',
            },
            'selected': {
                'entity': 'PoD',
                'attribute': 'pod_id',
                'value': 'POD-001',
            },
            'candidates': [
                {'entity': 'PoD', 'attribute': 'pod_id', 'value': 'POD-001'},
                {'entity': 'PoD', 'attribute': 'pod_id', 'value': 'POD-002'},
            ],
        },
    )

    assert '\u5982\u679c anchor_resolution_payload.selection.decision \u662f "select"' in prompt
    assert 'confidence_tier \u662f "high"' in prompt
    assert '\u4f18\u5148\u91c7\u7528 anchor_resolution_payload.selected' in prompt
    assert '\u5982\u679c anchor_resolution_payload.selection.decision \u662f "ambiguous"' in prompt
    assert '\u9000\u56de\u5230 schema + \u95ee\u9898\u8bed\u4e49\u7406\u89e3' in prompt


def test_resolve_question_route_returns_not_configured_when_env_missing(monkeypatch):
    from cloud_delivery_ontology_palantir.instance_qa.question_router import resolve_question_route

    monkeypatch.delenv('QWEN_API_BASE', raising=False)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)

    resolution = resolve_question_route('POD-001???????', _schema_registry(), schema_markdown='# schema')

    assert resolution.status == 'failed'
    assert resolution.error_type == 'router_not_configured'
    assert resolution.route is None


def test_resolve_question_route_maps_invalid_json(monkeypatch):
    from types import SimpleNamespace
    from cloud_delivery_ontology_palantir.instance_qa.question_router import resolve_question_route

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content='not-json'))]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr('cloud_delivery_ontology_palantir.instance_qa.question_router.get_openai_client', lambda timeout_s=120.0: fake_client)

    resolution = resolve_question_route('POD-001???????', _schema_registry(), schema_markdown='# schema')

    assert resolution.status == 'failed'
    assert resolution.error_type == 'router_invalid_json'
    assert resolution.route is None


def test_resolve_question_route_maps_invalid_payload(monkeypatch):
    from types import SimpleNamespace
    from cloud_delivery_ontology_palantir.instance_qa.question_router import resolve_question_route

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"intent": "attribute_lookup", "anchor_entity": "PoD", "target_attributes": ["pod_status"], "reasoning_scope": "anchor_only", "confidence": 0.97}'
                        )
                    )
                ]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr('cloud_delivery_ontology_palantir.instance_qa.question_router.get_openai_client', lambda timeout_s=120.0: fake_client)

    resolution = resolve_question_route('POD-001???????', _schema_registry(), schema_markdown='# schema')

    assert resolution.status == 'failed'
    assert resolution.error_type == 'router_invalid_payload'
    assert resolution.route is None


def test_resolve_question_route_maps_validation_failed(monkeypatch):
    from types import SimpleNamespace
    from cloud_delivery_ontology_palantir.instance_qa.question_router import resolve_question_route

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"intent": "attribute_lookup", "anchor_entity": "PoD", "anchor_locator": {"match_type": "key_attribute", "attribute": "pod_id", "value": "POD-001"}, "target_attributes": ["room_status"], "reasoning_scope": "anchor_only", "confidence": 0.97}'
                        )
                    )
                ]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr('cloud_delivery_ontology_palantir.instance_qa.question_router.get_openai_client', lambda timeout_s=120.0: fake_client)

    resolution = resolve_question_route('POD-001???????', _schema_registry(), schema_markdown='# schema')

    assert resolution.status == 'failed'
    assert resolution.error_type == 'router_validation_failed'
    assert resolution.route is None


def test_resolve_question_route_maps_timeout_and_connect_errors(monkeypatch):
    from cloud_delivery_ontology_palantir.instance_qa.question_router import resolve_question_route

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    def _timeout_client(timeout_s=120.0):
        class _Completions:
            def create(self, **kwargs):
                raise TimeoutError('timeout')
        class _Client:
            chat = type('Chat', (), {'completions': _Completions()})()
        return _Client()

    monkeypatch.setattr('cloud_delivery_ontology_palantir.instance_qa.question_router.get_openai_client', _timeout_client)
    timeout_resolution = resolve_question_route('POD-001???????', _schema_registry(), schema_markdown='# schema')
    assert timeout_resolution.status == 'failed'
    assert timeout_resolution.error_type == 'router_timeout'

    def _connect_client(timeout_s=120.0):
        class _Completions:
            def create(self, **kwargs):
                raise ConnectionError('connect failed')
        class _Client:
            chat = type('Chat', (), {'completions': _Completions()})()
        return _Client()

    monkeypatch.setattr('cloud_delivery_ontology_palantir.instance_qa.question_router.get_openai_client', _connect_client)
    connect_resolution = resolve_question_route('POD-001???????', _schema_registry(), schema_markdown='# schema')
    assert connect_resolution.status == 'failed'
    assert connect_resolution.error_type == 'router_connect_error'


def test_cached_question_router_prompt_prefix_reuses_same_schema(monkeypatch):
    from cloud_delivery_ontology_palantir.instance_qa import question_router as qr

    monkeypatch.setattr(qr, '_ROUTER_PROMPT_PREFIX_CACHE', {})
    calls = {'count': 0}
    original = qr.build_question_router_prompt_prefix

    def wrapped(*args, **kwargs):
        calls['count'] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(qr, 'build_question_router_prompt_prefix', wrapped)

    schema_markdown = '# schema\n\n## Object Types\n\n### `PoD`\n'
    prefix1 = qr.get_cached_question_router_prompt_prefix(_schema_registry(), schema_markdown=schema_markdown)
    prefix2 = qr.get_cached_question_router_prompt_prefix(_schema_registry(), schema_markdown=schema_markdown)

    assert prefix1 == prefix2
    assert calls['count'] == 1



def test_cached_question_router_prompt_prefix_invalidates_when_schema_changes(monkeypatch):
    from cloud_delivery_ontology_palantir.instance_qa import question_router as qr

    monkeypatch.setattr(qr, '_ROUTER_PROMPT_PREFIX_CACHE', {})

    prefix1 = qr.get_cached_question_router_prompt_prefix(_schema_registry(), schema_markdown='# schema A')
    prefix2 = qr.get_cached_question_router_prompt_prefix(_schema_registry(), schema_markdown='# schema B')

    assert prefix1 != prefix2
    assert len(qr._ROUTER_PROMPT_PREFIX_CACHE) == 2



def test_question_router_prompt_suffix_contains_query_and_anchor_payload():
    from cloud_delivery_ontology_palantir.instance_qa.question_router import build_question_router_prompt_suffix

    suffix = build_question_router_prompt_suffix(
        'pod-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f',
        anchor_resolution_payload={
            'raw_anchor_text': 'pod-001',
            'selection': {'decision': 'select', 'confidence_tier': 'high'},
            'selected': {'entity': 'PoD', 'attribute': 'pod_id', 'value': 'POD-001'},
        },
    )

    assert '\u5f53\u524d\u7528\u6237\u95ee\u9898\uff1a' in suffix
    assert 'pod-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f' in suffix
    assert '\u951a\u70b9\u5019\u9009\u89e3\u6790\u7ed3\u679c\uff1a' in suffix
    assert '\u4f18\u5148\u91c7\u7528 anchor_resolution_payload.selected' in suffix



def test_build_question_router_prompt_uses_cached_prefix_and_dynamic_suffix(monkeypatch):
    from cloud_delivery_ontology_palantir.instance_qa import question_router as qr

    monkeypatch.setattr(qr, '_ROUTER_PROMPT_PREFIX_CACHE', {})
    prompt = qr.build_question_router_prompt(
        _schema_registry(),
        'POD-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f',
        schema_markdown='# schema markdown',
        anchor_resolution_payload={'raw_anchor_text': 'POD-001'},
    )

    assert '\u53d7\u63a7\u8f93\u5165\uff1a' in prompt
    assert 'Schema \u8bf4\u660e\uff1a' in prompt
    assert '\u5f53\u524d\u7528\u6237\u95ee\u9898\uff1a' in prompt
    assert 'POD-001\u7684\u72b6\u6001\u662f\u4ec0\u4e48\uff1f' in prompt
    assert '\u951a\u70b9\u5019\u9009\u89e3\u6790\u7ed3\u679c\uff1a' in prompt
