from __future__ import annotations

import re
from dataclasses import dataclass

from ..search.ontology_query_models import OntologyEvidenceBundle, TraceExpansionStep


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
    seed_labels = _dedupe_preserve_order([_summary_name(bundle, node_id) for node_id in bundle.seed_node_ids])
    unique_trace_steps = _dedupe_trace_steps(bundle.search_trace.expansion_steps)
    relation_lines = _build_relation_summary_lines(bundle, unique_trace_steps)

    if bundle.insufficient_evidence:
        parts: list[str] = [
            f'证据不足：当前系统仅包含本体定义，不包含实例运行状态或实时数据，无法直接回答“{bundle.question}”。'
        ]
        if seed_labels:
            parts.append(f'已命中的本体实体包括：{"、".join(seed_labels)}。')
        return TemplateAnswer(answer=''.join(parts), insufficient_evidence=True)

    if relation_lines:
        summary = '根据当前本体定义，相关关键关系包括：\n' + '\n'.join(f'- {line}' for line in relation_lines)
    elif seed_labels:
        summary = f'根据当前本体定义，问题主要涉及这些实体：{"、".join(seed_labels)}。'
    else:
        summary = '证据不足：当前本体定义中未匹配到可用实体或关系。'
    return TemplateAnswer(answer=summary, insufficient_evidence=False)


def _build_search_trace_report(bundle: OntologyEvidenceBundle, trace_steps: list[TraceExpansionStep]) -> str:
    formatter = _TraceNameFormatter(bundle)
    sections: list[str] = []

    anchor_ids = bundle.search_trace.seed_node_ids or bundle.seed_node_ids
    anchor_labels = _dedupe_preserve_order([formatter.format(node_id) for node_id in anchor_ids if node_id])
    if anchor_labels:
        sections.append(_render_trace_section('识别出的核心实体', anchor_labels))

    reasoning = bundle.search_trace.seed_resolution_reasoning.strip()
    reasoning_lines = _split_trace_lines(reasoning)
    if reasoning_lines:
        sections.append(_render_trace_section('实体识别依据', reasoning_lines))

    expansion_lines = [
        f'从{formatter.format(step.from_node_id)} 沿 {_relation_name(bundle, step.relation)} 扩展到 {formatter.format(step.to_node_id)}'
        for step in trace_steps
    ]
    expansion_lines = _dedupe_preserve_order(expansion_lines)
    if expansion_lines:
        sections.append(_render_trace_section('关键扩展', expansion_lines))

    relation_lines = [
        f'{formatter.format(step.from_node_id)} {_relation_name(bundle, step.relation)} {formatter.format(step.to_node_id)}'
        for step in trace_steps
    ]
    relation_lines = _dedupe_preserve_order(relation_lines)
    if relation_lines:
        sections.append(_render_trace_section('命中的关键关系', relation_lines))

    fallback_lines = _split_trace_lines(bundle.search_trace.seed_resolution_error)
    if fallback_lines:
        sections.append(_render_trace_section('解析回退信息', fallback_lines))

    return '\n\n'.join(section for section in sections if section)


def _render_trace_section(title: str, lines: list[str]) -> str:
    cleaned_lines = [line.strip() for line in lines if line and line.strip()]
    if not cleaned_lines:
        return ''
    return title + '\n' + '\n'.join(f'- {line}' for line in cleaned_lines)


def _split_trace_lines(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r'[\r\n。；;]+', text)
    return [part.strip() for part in parts if part and part.strip()]


def _build_relation_summary_lines(bundle: OntologyEvidenceBundle, trace_steps: list[TraceExpansionStep]) -> list[str]:
    lines = [
        f'{_summary_name(bundle, step.from_node_id)} {_relation_name(bundle, step.relation)} {_summary_name(bundle, step.to_node_id)}'
        for step in trace_steps
    ]
    if lines:
        return _dedupe_preserve_order(lines)

    fallback_lines: list[str] = []
    visited_edges: set[tuple[str, str, str]] = set()
    for item in bundle.evidence_chain:
        if item.kind != 'relation' or len(item.node_ids) < 2:
            continue
        left = _summary_name(bundle, item.node_ids[0])
        right = _summary_name(bundle, item.node_ids[1])
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
    label, english = _display_parts(bundle, node_id)
    if label and english and label != english:
        return f'{label}({english})'
    return label or english


def _summary_name(bundle: OntologyEvidenceBundle, node_id: str) -> str:
    label, english = _display_parts(bundle, node_id)
    return label or english


def _display_parts(bundle: OntologyEvidenceBundle, node_id: str) -> tuple[str, str]:
    english = str(node_id or '').split(':', 1)[-1].strip() or node_id
    raw_display_name = bundle.display_name_map.get(node_id, '').strip()
    if not raw_display_name:
        return '', english

    suffix_token = f'({english})'
    label = raw_display_name[:-len(suffix_token)].strip() if raw_display_name.endswith(suffix_token) else raw_display_name
    label = re.split(r'[。；;，,：:\n\r]', label, maxsplit=1)[0].strip()
    if not label or label == english:
        return '', english
    return label, english


class _TraceNameFormatter:
    def __init__(self, bundle: OntologyEvidenceBundle) -> None:
        self._bundle = bundle
        self._seen: set[str] = set()

    def format(self, node_id: str) -> str:
        label, english = _display_parts(self._bundle, node_id)
        if not label:
            return english
        if not english or label == english:
            return label
        if node_id in self._seen:
            return label
        self._seen.add(node_id)
        return f'{label}({english})'


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


def build_instance_template_answer(question: str, fact_pack: dict[str, object], reasoning_result: dict[str, object]) -> TemplateAnswer:
    instances = fact_pack.get('instances') if isinstance(fact_pack, dict) else {}
    instance_count = 0
    if isinstance(instances, dict):
        instance_count = sum(len(items) for items in instances.values() if isinstance(items, list))

    summary = reasoning_result.get('summary', {}) if isinstance(reasoning_result, dict) else {}
    deadline_assessment = reasoning_result.get('deadline_assessment', {}) if isinstance(reasoning_result, dict) else {}

    if summary.get('answer_type') == 'deadline_risk':
        at_risk = bool(deadline_assessment.get('at_risk'))
        deadline = deadline_assessment.get('deadline')
        supporting = deadline_assessment.get('supporting_facts') or []
        if at_risk:
            detail = f' 关键依据：{supporting[0]}。' if supporting else ''
            return TemplateAnswer(answer=f'存在交付风险：{question} 可能影响截止日期 {deadline}。{detail}', insufficient_evidence=False)
        return TemplateAnswer(answer=f'当前未发现明确交付风险：{question} 在截止日期 {deadline} 前暂无直接风险证据。', insufficient_evidence=False)

    if instance_count <= 0:
        return TemplateAnswer(answer=f'证据不足：当前未检索到与“{question}”直接相关的实例数据。', insufficient_evidence=True)

    affected = reasoning_result.get('affected_entities') if isinstance(reasoning_result, dict) else []
    affected_count = len(affected) if isinstance(affected, list) else 0
    return TemplateAnswer(answer=f'已识别潜在受影响对象 {affected_count or instance_count} 个，建议优先核查关键路径任务。', insufficient_evidence=False)
