from __future__ import annotations

from dataclasses import dataclass

from ..search.ontology_query_models import OntologyEvidenceBundle


@dataclass(slots=True)
class TemplateAnswer:
    answer: str
    insufficient_evidence: bool

    def to_dict(self) -> dict[str, object]:
        return {
            'answer': self.answer,
            'insufficient_evidence': self.insufficient_evidence,
        }


def build_template_answer(bundle: OntologyEvidenceBundle) -> TemplateAnswer:
    evidence_refs = ''.join(f'[{item.evidence_id}]' for item in bundle.evidence_chain)
    relation_items = [item for item in bundle.evidence_chain if item.kind == 'relation']
    seed_labels = [item.label for item in bundle.evidence_chain if item.kind in {'seed', 'node'}]
    trace_report = _build_search_trace_report(bundle, seed_labels)

    if bundle.insufficient_evidence:
        anchor_text = f'已命中本体实体：{", ".join(seed_labels)}。' if seed_labels else ''
        parts = []
        if trace_report:
            parts.append(f'检索路径报告：{trace_report}。')
        parts.append(
            f'证据不足：当前系统仅包含本体定义，不包含实例运行状态或实时数据，'
            f'无法直接回答“{bundle.question}”。{anchor_text}证据：{evidence_refs or "[E0]"}。'
        )
        return TemplateAnswer(answer=''.join(parts), insufficient_evidence=True)

    if relation_items:
        relation_text = '；'.join(item.label for item in relation_items)
        summary = f'根据当前本体定义，命中了这些关系：{relation_text}。证据：{evidence_refs}。'
    elif seed_labels:
        entity_text = '、'.join(seed_labels)
        summary = f'根据当前本体定义，问题主要命中实体：{entity_text}。证据：{evidence_refs}。'
    else:
        summary = f'证据不足：当前本体定义中未匹配到可用实体或关系。证据：{evidence_refs or "[E0]"}。'

    if trace_report:
        summary = f'检索路径报告：{trace_report}。{summary}'
    return TemplateAnswer(answer=summary, insufficient_evidence=False)


def _build_search_trace_report(bundle: OntologyEvidenceBundle, seed_labels: list[str]) -> str:
    parts: list[str] = []
    anchor_labels = seed_labels or [_node_name(node_id) for node_id in bundle.search_trace.seed_node_ids]
    if anchor_labels:
        parts.append(f'通过匹配“{"、".join(anchor_labels)}”定位到核心概念')
    for step in bundle.search_trace.expansion_steps:
        to_name = _node_name(step.to_node_id)
        if to_name:
            parts.append(f'随后沿“{step.relation}”关系扩展到“{to_name}”')
    return '；'.join(part for part in parts if part)


def _node_name(node_id: str) -> str:
    return str(node_id or '').split(':', 1)[-1]
