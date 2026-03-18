from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject
from cloud_delivery_ontology_palantir.search.intent_resolver import resolve_intent


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
