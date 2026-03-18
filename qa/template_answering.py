from __future__ import annotations

import re
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
    seed_labels = _dedupe_preserve_order([_display_name(bundle, node_id) for node_id in bundle.seed_node_ids])
    unique_trace_steps = _dedupe_trace_steps(bundle.search_trace.expansion_steps)
    trace_report = _build_search_trace_report(bundle, unique_trace_steps)
    relation_lines = _build_relation_summary_lines(bundle, unique_trace_steps)

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

    if relation_lines:
        summary = '命中关系：\n' + '\n'.join(f'- {line}' for line in relation_lines)
        summary = f'{summary}\n证据：{evidence_refs or "[E0]"}。'
    elif seed_labels:
        summary = f'根据当前本体定义，问题主要命中实体：{"、".join(seed_labels)}。证据：{evidence_refs or "[E0]"}。'
    else:
        summary = f'证据不足：当前本体定义中未匹配到可用实体或关系。证据：{evidence_refs or "[E0]"}。'

    if trace_report:
        summary = f'检索路径报告：{trace_report}。{summary}'
    return TemplateAnswer(answer=summary, insufficient_evidence=False)


def _build_search_trace_report(bundle: OntologyEvidenceBundle, trace_steps: list[TraceExpansionStep]) -> str:
    parts: list[str] = []
    reasoning = bundle.search_trace.seed_resolution_reasoning.strip()
    if reasoning:
        parts.append(reasoning)

    anchor_ids = bundle.search_trace.seed_node_ids or bundle.seed_node_ids
    anchor_labels = _dedupe_preserve_order([_display_name(bundle, node_id) for node_id in anchor_ids if node_id])
    if anchor_labels:
        parts.append(f'通过匹配“{"、".join(anchor_labels)}”定位到核心概念')

    for step in trace_steps:
        parts.append(
            f'随后从 {_display_name(bundle, step.from_node_id)} 沿 {_relation_name(bundle, step.relation)} 扩展到 {_display_name(bundle, step.to_node_id)}'
        )

    if bundle.search_trace.seed_resolution_error:
        parts.append(f'解析回退：{bundle.search_trace.seed_resolution_error}')

    return '；'.join(part for part in parts if part)


def _build_relation_summary_lines(bundle: OntologyEvidenceBundle, trace_steps: list[TraceExpansionStep]) -> list[str]:
    lines = [
        f'{_display_name(bundle, step.from_node_id)} {_relation_name(bundle, step.relation)} {_display_name(bundle, step.to_node_id)}'
        for step in trace_steps
    ]
    if lines:
        return lines

    fallback_lines: list[str] = []
    visited_edges: set[tuple[str, str, str]] = set()
    for item in bundle.evidence_chain:
        if item.kind != 'relation' or len(item.node_ids) < 2:
            continue
        left = _display_name(bundle, item.node_ids[0])
        right = _display_name(bundle, item.node_ids[1])
        key = (left, '[关联]', right)
        if key in visited_edges:
            continue
        visited_edges.add(key)
        fallback_lines.append(f'{left} [关联] {right}')
    return fallback_lines


def _dedupe_trace_steps(trace_steps: list[TraceExpansionStep]) -> list[TraceExpansionStep]:
    visited_edges: set[tuple[str, str, str]] = set()
    result: list[TraceExpansionStep] = []
    for step in trace_steps:
        key = (step.from_node_id, step.relation, step.to_node_id)
        if key in visited_edges:
            continue
        visited_edges.add(key)
        result.append(step)
    return result


def _display_name(bundle: OntologyEvidenceBundle, node_id: str) -> str:
    suffix = str(node_id or '').split(':', 1)[-1].strip() or node_id
    raw_display_name = bundle.display_name_map.get(node_id, '').strip()
    if not raw_display_name:
        return suffix

    suffix_token = f'({suffix})'
    label = raw_display_name[:-len(suffix_token)].strip() if raw_display_name.endswith(suffix_token) else raw_display_name
    label = re.split(r'[。；;，,：:\n\r]', label, maxsplit=1)[0].strip()
    if not label or label == suffix:
        return suffix
    return f'{label}({suffix})'


def _relation_name(bundle: OntologyEvidenceBundle, relation: str) -> str:
    label = bundle.relation_name_map.get(relation, relation).strip()
    if label.startswith('[') and label.endswith(']'):
        return label
    return f'[{label}]'


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
