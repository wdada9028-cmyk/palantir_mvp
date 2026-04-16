from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject
from cloud_delivery_ontology_palantir.search.intent_resolver import _build_prompt, _load_config, resolve_intent


def _build_graph() -> OntologyGraph:
    graph = OntologyGraph()
    graph.add_object(
        OntologyObject(
            id='object_type:ArrivalPlan',
            type='ObjectType',
            name='ArrivalPlan',
            aliases=['arrival plan'],
            attributes={'chinese_description': '到货计划', 'group': '决策与解释层'},
        )
    )
    graph.add_object(
        OntologyObject(
            id='object_type:PoDPosition',
            type='ObjectType',
            name='PoDPosition',
            attributes={'chinese_description': '泊位', 'group': '空间层'},
        )
    )
    return graph


def test_resolve_intent_returns_llm_seeds_from_openai_compatible_payload(monkeypatch):
    graph = _build_graph()

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.setenv('QWEN_MODEL', 'qwen2.5-32b-instruct')

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"seeds": ["object_type:ArrivalPlan"], "reasoning": "问题指向到货计划"}'
                        }
                    }
                ]
            }

    class FakeClient:
        def post(self, url, headers=None, json=None, timeout=None):
            assert url == 'https://example.com/v1/chat/completions'
            assert headers == {'Authorization': 'Bearer test-key'}
            assert json['model'] == 'qwen2.5-32b-instruct'
            return FakeResponse()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.intent_resolver.get_http_client',
        lambda: FakeClient(),
    )

    result = resolve_intent(graph, '到货计划是什么')

    assert result.seeds == ['object_type:ArrivalPlan']
    assert result.source == 'llm'
    assert result.reasoning == '问题指向到货计划'
    assert result.error == ''




def test_resolve_intent_ignores_intent_specific_base_key_and_uses_shared_base_key_with_intent_model(monkeypatch):
    graph = _build_graph()

    monkeypatch.setenv('QWEN_API_BASE', 'https://shared.example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'shared-key')
    monkeypatch.setenv('QWEN_MODEL', 'shared-model')
    monkeypatch.setenv('QWEN_INTENT_API_BASE', 'https://intent.example.com/v1')
    monkeypatch.setenv('QWEN_INTENT_API_KEY', 'intent-key')
    monkeypatch.setenv('QWEN_INTENT_MODEL', 'intent-model')

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"seeds": ["object_type:ArrivalPlan"], "reasoning": "????????"}'
                        }
                    }
                ]
            }

    class FakeClient:
        def post(self, url, headers=None, json=None, timeout=None):
            assert url == 'https://shared.example.com/v1/chat/completions'
            assert headers == {'Authorization': 'Bearer shared-key'}
            assert json['model'] == 'intent-model'
            return FakeResponse()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.intent_resolver.get_http_client',
        lambda: FakeClient(),
    )

    result = resolve_intent(graph, '???????')

    assert result.seeds == ['object_type:ArrivalPlan']
    assert result.source == 'llm'

def test_resolve_intent_falls_back_on_invalid_json(monkeypatch):
    graph = _build_graph()

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{not-json}'
                        }
                    }
                ]
            }

    class FakeClient:
        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.intent_resolver.get_http_client',
        lambda: FakeClient(),
    )

    result = resolve_intent(graph, '到货计划是什么')

    assert result.seeds == []
    assert result.source == 'fallback'
    assert result.reasoning == ''
    assert 'Invalid JSON' in result.error


def test_resolve_intent_returns_disabled_when_config_is_missing(monkeypatch):
    graph = _build_graph()

    monkeypatch.delenv('QWEN_API_BASE', raising=False)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    monkeypatch.delenv('QWEN_MODEL', raising=False)
    monkeypatch.delenv('QWEN_INTENT_MODEL', raising=False)

    result = resolve_intent(graph, '到货计划是什么')

    assert result.seeds == []
    assert result.source == 'disabled'
    assert 'QWEN_API_BASE' in result.error
    assert 'QWEN_API_KEY' in result.error


def test_resolve_intent_filters_unknown_seed_ids(monkeypatch):
    graph = _build_graph()

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"seeds": ["object_type:PoDPosition", "object_type:Missing", "object_type:PoDPosition"], "reasoning": "问题更像在问泊位"}'
                        }
                    }
                ]
            }

    class FakeClient:
        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.intent_resolver.get_http_client',
        lambda: FakeClient(),
    )

    result = resolve_intent(graph, '泊位在哪里')

    assert result.seeds == ['object_type:PoDPosition']
    assert result.source == 'llm'
    assert result.error == ''




def test_resolve_intent_candidate_mode_filters_to_candidate_ids(monkeypatch):
    graph = _build_graph()

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"seeds": ["object_type:PoDPosition", "object_type:ArrivalPlan"], "reasoning": "\u66f4\u50cf\u5728\u95ee\u6cca\u4f4d"}'
                        }
                    }
                ]
            }

    class FakeClient:
        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.intent_resolver.get_http_client',
        lambda: FakeClient(),
    )

    result = resolve_intent(graph, '\u6cca\u4f4d\u5728\u54ea\u91cc', candidate_ids=['object_type:PoDPosition'])

    assert result.seeds == ['object_type:PoDPosition']
    assert result.source == 'llm_candidate_select'
    assert result.reasoning == '\u66f4\u50cf\u5728\u95ee\u6cca\u4f4d'
    assert result.error == ''


def test_resolve_intent_candidate_mode_limits_prompt_schema_to_candidates(monkeypatch):
    graph = _build_graph()

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    captured_payload = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"seeds": ["object_type:PoDPosition"], "reasoning": "\u547d\u4e2d\u6cca\u4f4d"}'
                        }
                    }
                ]
            }

    class FakeClient:
        def post(self, url, headers=None, json=None, timeout=None):
            captured_payload['json'] = json
            return FakeResponse()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.intent_resolver.get_http_client',
        lambda: FakeClient(),
    )

    result = resolve_intent(graph, '\u6cca\u4f4d\u5728\u54ea\u91cc', candidate_ids=['object_type:PoDPosition'])

    assert result.seeds == ['object_type:PoDPosition']
    assert result.source == 'llm_candidate_select'

    user_prompt = captured_payload['json']['messages'][1]['content']
    assert 'id=object_type:PoDPosition; chinese_description=\u6cca\u4f4d' in user_prompt
    assert 'id=object_type:ArrivalPlan; chinese_description=\u5230\u8d27\u8ba1\u5212' not in user_prompt

def test_build_prompt_uses_minimal_deduped_schema_summary(monkeypatch):
    graph = _build_graph()
    arrival_plan = graph.get_object('object_type:ArrivalPlan')
    assert arrival_plan is not None

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.intent_resolver._iter_prompt_objects',
        lambda graph: [arrival_plan, arrival_plan],
    )

    prompt = _build_prompt(graph, '到货计划是什么')

    assert prompt.count('id=object_type:ArrivalPlan; chinese_description=到货计划') == 1
    assert 'name=' not in prompt
    assert 'aliases=' not in prompt
    assert 'group=' not in prompt


def test_intent_resolver_defaults_to_qwen36_plus(monkeypatch):
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.delenv('QWEN_MODEL', raising=False)
    monkeypatch.delenv('QWEN_INTENT_MODEL', raising=False)

    config = _load_config()

    assert config is not None
    assert config.model == 'qwen3.6-plus'
