import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from cloud_delivery_ontology_palantir.qa.generator import GeneratorChunk, GeneratorResult, _build_fact_lines, _build_messages, iter_generated_answer
from cloud_delivery_ontology_palantir.qa.template_answering import TemplateAnswer
from cloud_delivery_ontology_palantir.search.ontology_query_models import (
    EvidenceItem,
    OntologyEvidenceBundle,
    RetrievalStep,
    SearchTrace,
    TraceExpansionStep,
)


def _build_bundle(*, with_relation: bool = True) -> OntologyEvidenceBundle:
    evidence_chain = [
        EvidenceItem(
            evidence_id='E1',
            kind='seed',
            label='RoomMilestone',
            message='\u95ee\u9898\u547d\u4e2d\u4e86\u5b9e\u4f53 \u673a\u623f\u91cc\u7a0b\u7891(RoomMilestone)',
            node_ids=['object_type:RoomMilestone'],
            why_matched=['\u5b9e\u4f53\u540d\u79f0\u5339\u914d'],
        )
    ]
    expansion_steps: list[TraceExpansionStep] = []
    matched_node_ids = ['object_type:RoomMilestone']
    matched_edge_ids: list[str] = []
    if with_relation:
        evidence_chain.append(
            EvidenceItem(
                evidence_id='E2',
                kind='relation',
                label='RoomMilestone APPLIES_TO PlacementPlan',
                message='\u673a\u623f\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\u65b9\u6848',
                node_ids=['object_type:RoomMilestone', 'object_type:PlacementPlan'],
                edge_ids=['e1'],
                why_matched=['\u5173\u7cfb\u90bb\u63a5\u6269\u5c55'],
            )
        )
        expansion_steps.append(
            TraceExpansionStep(
                step=1,
                from_node_id='object_type:RoomMilestone',
                edge_id='e1',
                to_node_id='object_type:PlacementPlan',
                relation='APPLIES_TO',
                reason='\u5173\u7cfb\u90bb\u63a5\u6269\u5c55',
                snapshot_node_ids=['object_type:RoomMilestone', 'object_type:PlacementPlan'],
                snapshot_edge_ids=['e1'],
            )
        )
        matched_node_ids.append('object_type:PlacementPlan')
        matched_edge_ids.append('e1')
    return OntologyEvidenceBundle(
        question='\u54ea\u4e9b\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\uff1f',
        seed_node_ids=['object_type:RoomMilestone'],
        matched_node_ids=matched_node_ids,
        matched_edge_ids=matched_edge_ids,
        highlight_steps=[
            RetrievalStep(
                action='anchor_node',
                message='\u5b9a\u4f4d\u5230 RoomMilestone',
                node_ids=['object_type:RoomMilestone'],
            )
        ],
        evidence_chain=evidence_chain,
        insufficient_evidence=False,
        search_trace=SearchTrace(
            seed_node_ids=['object_type:RoomMilestone'],
            seed_resolution_source='fallback',
            seed_resolution_reasoning='\u5b9e\u4f53\u540d\u79f0\u5339\u914d',
            seed_resolution_error='',
            expansion_steps=expansion_steps,
        ),
        display_name_map={
            'object_type:RoomMilestone': '\u673a\u623f\u91cc\u7a0b\u7891(RoomMilestone)',
            'object_type:PlacementPlan': '\u843d\u4f4d\u65b9\u6848(PlacementPlan)',
        },
        relation_name_map={'APPLIES_TO': '[\u4f5c\u7528\u4e8e]'},
    )


async def _collect(question: str, bundle: OntologyEvidenceBundle, fallback: TemplateAnswer):
    items = []
    async for item in iter_generated_answer(question, bundle, fallback):
        items.append(item)
    return items


def test_build_fact_lines_use_chinese_only_summary_labels():
    bundle = _build_bundle(with_relation=True)

    fact_lines = _build_fact_lines(bundle)

    assert fact_lines == ['\u673a\u623f\u91cc\u7a0b\u7891 [\u4f5c\u7528\u4e8e] \u843d\u4f4d\u65b9\u6848']
    assert 'RoomMilestone' not in fact_lines[0]
    assert 'PlacementPlan' not in fact_lines[0]


def test_build_messages_explicitly_forbids_repeating_trace_steps():
    messages = _build_messages('\u54ea\u4e9b\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\uff1f', ['\u673a\u623f\u91cc\u7a0b\u7891 [\u4f5c\u7528\u4e8e] \u843d\u4f4d\u65b9\u6848'])

    assert '\u4e0d\u8981\u590d\u8ff0\u68c0\u7d22\u8def\u5f84' in messages[0]['content']
    assert '\u4e0d\u8981\u8f93\u51fa\u82f1\u6587\u5b9e\u4f53\u540d' in messages[0]['content']


def test_iter_generated_answer_streams_chunks_for_summary_style_output(monkeypatch):
    bundle = _build_bundle(with_relation=True)
    fallback = TemplateAnswer(answer='fallback', insufficient_evidence=False)

    class FakeChunk:
        def __init__(self, text: str):
            self.choices = [SimpleNamespace(delta=SimpleNamespace(content=text))]

    async def fake_stream():
        for text in ['\u7ed3\u8bba\uff1a', '\u673a\u623f\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\u65b9\u6848\u3002']:
            yield FakeChunk(text)

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(return_value=fake_stream())
            )
        )
    )
    monkeypatch.setattr('cloud_delivery_ontology_palantir.qa.generator.get_openai_client', lambda: fake_client)
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    monkeypatch.setenv('QWEN_MODEL', 'qwen2.5-32b-instruct')

    chunks = asyncio.run(_collect('\u54ea\u4e9b\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\uff1f', bundle, fallback))

    assert [item.delta for item in chunks[:-1]] == ['\u7ed3\u8bba\uff1a', '\u673a\u623f\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\u65b9\u6848\u3002']
    result = chunks[-1]
    assert isinstance(result, GeneratorResult)
    assert result.used_fallback is False
    assert 'RoomMilestone' not in result.answer_text
    assert 'PlacementPlan' not in result.answer_text


def test_iter_generated_answer_falls_back_when_qwen_config_missing(monkeypatch):
    bundle = _build_bundle(with_relation=True)
    fallback = TemplateAnswer(answer='deterministic fallback', insufficient_evidence=False)

    monkeypatch.delenv('QWEN_API_BASE', raising=False)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)

    chunks = asyncio.run(_collect('\u54ea\u4e9b\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\uff1f', bundle, fallback))

    assert chunks == [GeneratorResult(answer_text='deterministic fallback', used_fallback=True)]


def test_iter_generated_answer_falls_back_when_no_facts(monkeypatch):
    bundle = _build_bundle(with_relation=False)
    fallback = TemplateAnswer(answer='deterministic fallback', insufficient_evidence=False)

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(side_effect=AssertionError('generator should not call OpenAI when no facts'))
            )
        )
    )
    monkeypatch.setattr('cloud_delivery_ontology_palantir.qa.generator.get_openai_client', lambda: fake_client)
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    chunks = asyncio.run(_collect('\u54ea\u4e9b\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\uff1f', bundle, fallback))

    assert chunks == [GeneratorResult(answer_text='deterministic fallback', used_fallback=True)]


def test_iter_generated_answer_falls_back_after_mid_stream_exception(monkeypatch):
    bundle = _build_bundle(with_relation=True)
    fallback = TemplateAnswer(answer='deterministic fallback', insufficient_evidence=False)

    class FakeChunk:
        def __init__(self, text: str):
            self.choices = [SimpleNamespace(delta=SimpleNamespace(content=text))]

    async def fake_stream():
        yield FakeChunk('\u7ed3\u8bba\uff1a')
        raise RuntimeError('stream boom')

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(return_value=fake_stream())
            )
        )
    )
    monkeypatch.setattr('cloud_delivery_ontology_palantir.qa.generator.get_openai_client', lambda: fake_client)
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    chunks = asyncio.run(_collect('\u54ea\u4e9b\u91cc\u7a0b\u7891\u4f1a\u5f71\u54cd\u843d\u4f4d\uff1f', bundle, fallback))

    assert isinstance(chunks[0], GeneratorChunk)
    assert chunks[0].delta == '\u7ed3\u8bba\uff1a'
    assert chunks[-1] == GeneratorResult(answer_text='deterministic fallback', used_fallback=True)
