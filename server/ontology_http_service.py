from __future__ import annotations

import json
from collections.abc import Iterable
from uuid import uuid4

from ..qa.template_answering import TemplateAnswer
from ..search.ontology_query_models import OntologyEvidenceBundle, RetrievalStep, TraceExpansionStep

DEFAULT_TRACE_DELAY_MS = 650


def sse_event(name: str, payload: dict[str, object]) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def iter_qa_events(
    bundle: OntologyEvidenceBundle,
    answer: TemplateAnswer,
    trace_delay_ms: int = DEFAULT_TRACE_DELAY_MS,
) -> Iterable[str]:
    session_id = uuid4().hex
    step_counter = 0

    if bundle.search_trace.seed_node_ids:
        step_counter += 1
        yield sse_event(
            'trace_anchor',
            {
                'session_id': session_id,
                'step': step_counter,
                'message': '已定位问题相关的核心实体',
                'node_ids': list(bundle.search_trace.seed_node_ids),
                'edge_ids': [],
                'evidence_ids': [item.evidence_id for item in bundle.evidence_chain if item.kind == 'seed'],
                'delay_ms': trace_delay_ms,
            },
        )

    for trace_step in bundle.search_trace.expansion_steps:
        step_counter += 1
        yield sse_event('trace_expand', _trace_expand_payload(session_id, step_counter, trace_step, trace_delay_ms))

    for step in bundle.highlight_steps:
        step_counter += 1
        yield sse_event(step.action, _step_payload(session_id, step_counter, step))

    for item in bundle.evidence_chain:
        step_counter += 1
        yield sse_event(
            'evidence',
            {
                'session_id': session_id,
                'step': step_counter,
                'message': item.message,
                'node_ids': item.node_ids,
                'edge_ids': item.edge_ids,
                'evidence_ids': [item.evidence_id],
                'evidence': item.to_dict(),
            },
        )

    step_counter += 1
    yield sse_event(
        'evidence_final',
        {
            'session_id': session_id,
            'step': step_counter,
            'message': '已确认最终证据链',
            'node_ids': bundle.matched_node_ids,
            'edge_ids': bundle.matched_edge_ids,
            'evidence_ids': [item.evidence_id for item in bundle.evidence_chain],
            'evidence_chain': [item.to_dict() for item in bundle.evidence_chain],
            'search_trace': bundle.search_trace.to_dict(),
        },
    )

    step_counter += 1
    yield sse_event(
        'answer_done',
        {
            'session_id': session_id,
            'step': step_counter,
            'message': '已生成回答',
            'node_ids': bundle.matched_node_ids,
            'edge_ids': bundle.matched_edge_ids,
            'evidence_ids': [item.evidence_id for item in bundle.evidence_chain],
            'answer': answer.answer,
            'evidence_chain': [item.to_dict() for item in bundle.evidence_chain],
            'matched_node_ids': bundle.matched_node_ids,
            'matched_edge_ids': bundle.matched_edge_ids,
            'insufficient_evidence': answer.insufficient_evidence,
            'search_trace': bundle.search_trace.to_dict(),
        },
    )


def _step_payload(session_id: str, step_number: int, step: RetrievalStep) -> dict[str, object]:
    return {
        'session_id': session_id,
        'step': step_number,
        'message': step.message,
        'node_ids': step.node_ids,
        'edge_ids': step.edge_ids,
        'evidence_ids': step.evidence_ids,
    }


def _trace_expand_payload(
    session_id: str,
    step_number: int,
    trace_step: TraceExpansionStep,
    trace_delay_ms: int,
) -> dict[str, object]:
    return {
        'session_id': session_id,
        'step': step_number,
        'message': f'正在沿 {trace_step.relation} 关系扩展检索路径',
        'node_ids': list(trace_step.snapshot_node_ids),
        'edge_ids': list(trace_step.snapshot_edge_ids),
        'evidence_ids': [],
        'delay_ms': trace_delay_ms,
        'trace_step': trace_step.to_dict(),
        'from_node_id': trace_step.from_node_id,
        'edge_id': trace_step.edge_id,
        'to_node_id': trace_step.to_node_id,
        'relation': trace_step.relation,
        'reason': trace_step.reason,
        'snapshot_node_ids': list(trace_step.snapshot_node_ids),
        'snapshot_edge_ids': list(trace_step.snapshot_edge_ids),
    }
