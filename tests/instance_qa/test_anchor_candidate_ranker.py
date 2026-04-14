from cloud_delivery_ontology_palantir.instance_qa.anchor_candidate_ranker import (
    _load_config,
    build_anchor_candidate_ranker_prompt,
    get_openai_client,
    parse_anchor_rank_payload,
    resolve_anchor_candidate_rank,
)


def _candidate_context(candidate_count: int = 2) -> dict[str, object]:
    return {
        'raw_anchor_text': 'pod-001',
        'question': 'pod-001的状态是什么？',
        'candidate_entity': 'PoD',
        'candidates': [
            {
                'candidate_id': f'cand_{idx}',
                'entity': 'PoD',
                'locator': {
                    'matched_attribute': 'pod_id',
                    'matched_value': f'POD-00{idx}',
                    'match_stage': 'light',
                },
                'identity': {'primary_id': f'POD-00{idx}', 'display_name': '', 'aliases': []},
                'core_attributes': {'pod_status': 'Installing'},
                'business_context': [],
            }
            for idx in range(1, candidate_count + 1)
        ],
    }


def test_build_anchor_candidate_ranker_prompt_embeds_question_schema_and_candidate_payload():
    prompt = build_anchor_candidate_ranker_prompt(
        question='pod-001的状态是什么？',
        schema_markdown='# schema markdown',
        candidate_context=_candidate_context(2),
        max_candidates=5,
    )

    assert 'Return JSON only.' in prompt
    assert 'pod-001的状态是什么？' in prompt
    assert '# schema markdown' in prompt
    assert 'Candidate context:' in prompt
    assert '"candidate_id": "cand_1"' in prompt


def test_build_anchor_candidate_ranker_prompt_limits_candidates():
    prompt = build_anchor_candidate_ranker_prompt(
        question='pod-001的状态是什么？',
        schema_markdown='# schema',
        candidate_context=_candidate_context(8),
        max_candidates=3,
    )

    assert '"candidate_id": "cand_1"' in prompt
    assert '"candidate_id": "cand_2"' in prompt
    assert '"candidate_id": "cand_3"' in prompt
    assert '"candidate_id": "cand_4"' not in prompt


def test_parse_anchor_rank_payload_supports_all_decisions():
    for decision in ('select', 'ambiguous', 'reject'):
        result = parse_anchor_rank_payload(
            {
                'decision': decision,
                'selected_candidate_id': 'cand_1' if decision == 'select' else '',
                'confidence': 0.9,
                'reason': 'ok',
            }
        )
        assert result.decision == decision


def test_anchor_ranker_defaults_to_qwen35_35b_a3b(monkeypatch):
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.delenv('QWEN_ANCHOR_RANKER_MODEL', raising=False)

    config = _load_config()

    assert config is not None
    assert config.model == 'Qwen3.5-35B-A3B'


def test_get_openai_client_uses_ranker_timeout_and_retries(monkeypatch):
    import sys
    from types import SimpleNamespace

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.setenv('QWEN_ANCHOR_RANKER_MODEL', 'Qwen3.5-35B-A3B')

    captured = {}

    class FakeOpenAI:
        def __init__(self, *, api_key, base_url, max_retries, timeout):
            captured['api_key'] = api_key
            captured['base_url'] = base_url
            captured['max_retries'] = max_retries
            captured['timeout'] = timeout

    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(OpenAI=FakeOpenAI))

    client = get_openai_client(timeout_s=45.0)

    assert client is not None
    assert captured == {
        'api_key': 'test-key',
        'base_url': 'https://example.com/v1',
        'max_retries': 2,
        'timeout': 45.0,
    }


def test_resolve_anchor_candidate_rank_returns_none_on_invalid_json(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.setenv('QWEN_ANCHOR_RANKER_MODEL', 'Qwen3.5-35B-A3B')

    class FakeCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(message=SimpleNamespace(content='not-json')),
                ]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.instance_qa.anchor_candidate_ranker.get_openai_client',
        lambda timeout_s=60.0: fake_client,
    )

    result = resolve_anchor_candidate_rank(
        question='pod-001的状态是什么？',
        schema_markdown='# schema',
        candidate_context=_candidate_context(2),
    )

    assert result is None


def test_resolve_anchor_candidate_rank_uses_ranker_model_and_parses_response(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.setenv('QWEN_ANCHOR_RANKER_MODEL', 'Qwen3.5-35B-A3B')

    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"decision": "select", "selected_candidate_id": "cand_1", "confidence": 0.92, "reason": "best match"}'
                        )
                    )
                ]
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.instance_qa.anchor_candidate_ranker.get_openai_client',
        lambda timeout_s=60.0: fake_client,
    )

    result = resolve_anchor_candidate_rank(
        question='pod-001的状态是什么？',
        schema_markdown='# schema',
        candidate_context=_candidate_context(6),
        max_candidates=4,
        timeout_s=90.0,
    )

    assert result is not None
    assert result.decision == 'select'
    assert result.selected_candidate_id == 'cand_1'
    assert result.confidence == 0.92
    assert captured['model'] == 'Qwen3.5-35B-A3B'
    assert captured['temperature'] == 0.0
    assert captured['response_format'] == {'type': 'json_object'}
    assert captured['timeout'] == 90.0
    assert '"candidate_id": "cand_4"' in captured['messages'][1]['content']
    assert '"candidate_id": "cand_5"' not in captured['messages'][1]['content']
