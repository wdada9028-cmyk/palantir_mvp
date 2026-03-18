from __future__ import annotations

from dataclasses import dataclass

from ..search.ontology_query_models import EvidenceItem, OntologyEvidenceBundle, TraceExpansionStep


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
    seed_labels = [_display_name(bundle, node_id) for node_id in bundle.seed_node_ids]
    trace_report = _build_search_trace_report(bundle)
    relation_items = [item for item in bundle.evidence_chain if item.kind == 'relation']

    if bundle.insufficient_evidence:
        parts: list[str] = []
        if trace_report:
            parts.append(f'检索路径报告：{trace_report}。')
        parts.append(
            f'证据不足：当前系统仅包含本体定义，不包含实例运行状态或实时数据，无法直接回答“{bundle.question}”。'
        )
        if seed_labels:
            parts.append(f'已命中本体实体：{"、".join(seed_labels)}。')
        parts.append(f'证据：{evidence_refs or "[E0]"}。')
        return TemplateAnswer(answer=''.join(parts), insufficient_evidence=True)

    if relation_items:
        relation_text = '；'.join(_relation_summary(bundle, item) for item in relation_items)
        summary = f'根据当前本体定义，命中了这些关系：{relation_text}。证据：{evidence_refs or "[E0]"}。'
    elif seed_labels:
        summary = f'根据当前本体定义，问题主要命中实体：{"、".join(seed_labels)}。证据：{evidence_refs or "[E0]"}。'
    else:
        summary = f'证据不足：当前本体定义中未匹配到可用实体或关系。证据：{evidence_refs or "[E0]"}。'

    if trace_report:
        summary = f'检索路径报告：{trace_report}。{summary}'
    return TemplateAnswer(answer=summary, insufficient_evidence=False)


def _build_search_trace_report(bundle: OntologyEvidenceBundle) -> str:
    parts: list[str] = []
    reasoning = bundle.search_trace.seed_resolution_reasoning.strip()
    if reasoning:
        parts.append(reasoning)

    anchor_ids = bundle.search_trace.seed_node_ids or bundle.seed_node_ids
    anchor_labels = [_display_name(bundle, node_id) for node_id in anchor_ids if node_id]
    if anchor_labels:
        parts.append(f'通过匹配“{"、".join(anchor_labels)}”定位到核心概念')

    for step in bundle.search_trace.expansion_steps:
        parts.append(
            f'随后从{_display_name(bundle, step.from_node_id)}沿[{_relation_name(bundle, step.relation)}]扩展到{_display_name(bundle, step.to_node_id)}'
        )

    if bundle.search_trace.seed_resolution_error:
        parts.append(f'解析回退：{bundle.search_trace.seed_resolution_error}')

    return '；'.join(part for part in parts if part)


def _relation_summary(bundle: OntologyEvidenceBundle, item: EvidenceItem) -> str:
    trace_steps_by_edge = {step.edge_id: step for step in bundle.search_trace.expansion_steps}
    for edge_id in item.edge_ids:
        trace_step = trace_steps_by_edge.get(edge_id)
        if trace_step is not None:
            return _format_relation_path(bundle, trace_step)
    if len(item.node_ids) >= 2:
        left = _display_name(bundle, item.node_ids[0])
        right = _display_name(bundle, item.node_ids[1])
        return f'{left}[关联]{right}'
    return item.message


def _format_relation_path(bundle: OntologyEvidenceBundle, step: TraceExpansionStep) -> str:
    return (
        f'{_display_name(bundle, step.from_node_id)}'
        f'[{_relation_name(bundle, step.relation)}]'
        f'{_display_name(bundle, step.to_node_id)}'
    )


def _display_name(bundle: OntologyEvidenceBundle, node_id: str) -> str:
    display_name = bundle.display_name_map.get(node_id, '').strip()
    if display_name:
        return display_name
    suffix = str(node_id or '').split(':', 1)[-1].strip()
    return suffix or node_id


def _relation_name(bundle: OntologyEvidenceBundle, relation: str) -> str:
    return bundle.relation_name_map.get(relation, relation)
