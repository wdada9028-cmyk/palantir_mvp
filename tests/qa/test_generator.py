import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from cloud_delivery_ontology_palantir.qa.generator import GeneratorChunk, GeneratorResult, iter_generated_answer
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
            message='问题命中了实体 机房里程碑(RoomMilestone)',
            node_ids=['object_type:RoomMilestone'],
            why_matched=['实体名称匹配'],
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
                message='机房里程碑会影响落位方案',
                node_ids=['object_type:RoomMilestone', 'object_type:PlacementPlan'],
                edge_ids=['e1'],
                why_matched=['关系邻接扩展'],
            )
        )
        expansion_steps.append(
            TraceExpansionStep(
                step=1,
                from_node_id='object_type:RoomMilestone',
                edge_id='e1',
                to_node_id='object_type:PlacementPlan',
                relation='APPLIES_TO',
                reason='关系邻接扩展',
                snapshot_node_ids=['object_type:RoomMilestone', 'object_type:PlacementPlan'],
                snapshot_edge_ids=['e1'],
            )
        )
        matched_node_ids.append('object_type:PlacementPlan')
        matched_edge_ids.append('e1')
    return OntologyEvidenceBundle(
        question='哪些里程碑会影响落位？',
        seed_node_ids=['object_type:RoomMilestone'],
        matched_node_ids=matched_node_ids,
        matched_edge_ids=matched_edge_ids,
        highlight_steps=[
            RetrievalStep(
                action='anchor_node',
                message='定位到 RoomMilestone',
                node_ids=['object_type:RoomMilestone'],
            )
        ],
        evidence_chain=evidence_chain,
        insufficient_evidence=False,
        search_trace=SearchTrace(
            seed_node_ids=['object_type:RoomMilestone'],
            seed_resolution_source='fallback',
            seed_resolution_reasoning='实体名称匹配',
            seed_resolution_error='',
            expansion_steps=expansion_steps,
        ),
        display_name_map={
            'object_type:RoomMilestone': '机房里程碑(RoomMilestone)',
            'object_type:PlacementPlan': '落位方案(PlacementPlan)',
        },
        relation_name_map={'APPLIES_TO': '[作用于]'},
    )


async def _collect(question: str, bundle: OntologyEvidenceBundle, fallback: TemplateAnswer):
    items = []
    async for item in iter_generated_answer(question, bundle, fallback):
        items.append(item)
    return items


def test_iter_generated_answer_streams_chunks_and_preserves_entity_labels(monkeypatch):
    bundle = _build_bundle(with_relation=True)
    fallback = TemplateAnswer(answer='fallback', insufficient_evidence=False)

    class FakeChunk:
        def __init__(self, text: str):
            self.choices = [SimpleNamespace(delta=SimpleNamespace(content=text))]

    async def fake_stream():
        for text in ['结论：', '机房里程碑(RoomMilestone)', ' 会影响落位方案(PlacementPlan)。']:
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

    chunks = asyncio.run(_collect('哪些里程碑会影响落位？', bundle, fallback))

    assert [item.delta for item in chunks[:-1]] == ['结论：', '机房里程碑(RoomMilestone)', ' 会影响落位方案(PlacementPlan)。']
    result = chunks[-1]
    assert isinstance(result, GeneratorResult)
    assert result.used_fallback is False
    assert result.answer_text.startswith('结论：')
    assert '机房里程碑(RoomMilestone)' in result.answer_text
    assert '落位方案(PlacementPlan)' in result.answer_text


def test_iter_generated_answer_falls_back_when_qwen_config_missing(monkeypatch):
    bundle = _build_bundle(with_relation=True)
    fallback = TemplateAnswer(answer='deterministic fallback', insufficient_evidence=False)

    monkeypatch.delenv('QWEN_API_BASE', raising=False)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)

    chunks = asyncio.run(_collect('哪些里程碑会影响落位？', bundle, fallback))

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

    chunks = asyncio.run(_collect('哪些里程碑会影响落位？', bundle, fallback))

    assert chunks == [GeneratorResult(answer_text='deterministic fallback', used_fallback=True)]


def test_iter_generated_answer_falls_back_after_mid_stream_exception(monkeypatch):
    bundle = _build_bundle(with_relation=True)
    fallback = TemplateAnswer(answer='deterministic fallback', insufficient_evidence=False)

    class FakeChunk:
        def __init__(self, text: str):
            self.choices = [SimpleNamespace(delta=SimpleNamespace(content=text))]

    async def fake_stream():
        yield FakeChunk('结论：')
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

    chunks = asyncio.run(_collect('哪些里程碑会影响落位？', bundle, fallback))

    assert isinstance(chunks[0], GeneratorChunk)
    assert chunks[0].delta == '结论：'
    assert chunks[-1] == GeneratorResult(answer_text='deterministic fallback', used_fallback=True)
