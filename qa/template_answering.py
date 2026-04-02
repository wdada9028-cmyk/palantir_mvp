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
    seed_labels = _dedupe_preserve_order([_summary_name(bundle, node_id) for node_id in bundle.seed_node_ids])
    unique_trace_steps = _dedupe_trace_steps(bundle.search_trace.expansion_steps)
    relation_lines = _build_relation_summary_lines(bundle, unique_trace_steps)

    if bundle.insufficient_evidence:
        parts: list[str] = [
            f'\u8bc1\u636e\u4e0d\u8db3\uff1a\u5f53\u524d\u7cfb\u7edf\u4ec5\u5305\u542b\u672c\u4f53\u5b9a\u4e49\uff0c\u4e0d\u5305\u542b\u5b9e\u4f8b\u8fd0\u884c\u72b6\u6001\u6216\u5b9e\u65f6\u6570\u636e\uff0c\u65e0\u6cd5\u76f4\u63a5\u56de\u7b54\u201c{bundle.question}\u201d\u3002'
        ]
        if seed_labels:
            joined_seed_labels = '\u3001'.join(seed_labels)
            parts.append(f'\u5df2\u547d\u4e2d\u7684\u672c\u4f53\u5b9e\u4f53\u5305\u62ec\uff1a{joined_seed_labels}\u3002')
        return TemplateAnswer(answer=''.join(parts), insufficient_evidence=True)

    if relation_lines:
        summary = '\u6839\u636e\u5f53\u524d\u672c\u4f53\u5b9a\u4e49\uff0c\u76f8\u5173\u5173\u952e\u5173\u7cfb\u5305\u62ec\uff1a\n' + '\n'.join(f'- {line}' for line in relation_lines)
    elif seed_labels:
        joined_seed_labels = '\u3001'.join(seed_labels)
        summary = f'\u6839\u636e\u5f53\u524d\u672c\u4f53\u5b9a\u4e49\uff0c\u95ee\u9898\u4e3b\u8981\u6d89\u53ca\u8fd9\u4e9b\u5b9e\u4f53\uff1a{joined_seed_labels}\u3002'
    else:
        summary = '\u8bc1\u636e\u4e0d\u8db3\uff1a\u5f53\u524d\u672c\u4f53\u5b9a\u4e49\u4e2d\u672a\u5339\u914d\u5230\u53ef\u7528\u5b9e\u4f53\u6216\u5173\u7cfb\u3002'
    return TemplateAnswer(answer=summary, insufficient_evidence=False)


def _build_search_trace_report(bundle: OntologyEvidenceBundle, trace_steps: list[TraceExpansionStep]) -> str:
    formatter = _TraceNameFormatter(bundle)
    sections: list[str] = []

    anchor_ids = bundle.search_trace.seed_node_ids or bundle.seed_node_ids
    anchor_labels = _dedupe_preserve_order([formatter.format(node_id) for node_id in anchor_ids if node_id])
    if anchor_labels:
        sections.append(_render_trace_section('\u8bc6\u522b\u51fa\u7684\u6838\u5fc3\u5b9e\u4f53', anchor_labels))

    reasoning = bundle.search_trace.seed_resolution_reasoning.strip()
    reasoning_lines = _split_trace_lines(reasoning)
    if reasoning_lines:
        sections.append(_render_trace_section('\u5b9e\u4f53\u8bc6\u522b\u4f9d\u636e', reasoning_lines))

    expansion_lines = [
        f'\u4ece{formatter.format(step.from_node_id)} \u6cbf {_relation_name(bundle, step.relation)} \u6269\u5c55\u5230 {formatter.format(step.to_node_id)}'
        for step in trace_steps
    ]
    expansion_lines = _dedupe_preserve_order(expansion_lines)
    if expansion_lines:
        sections.append(_render_trace_section('\u5173\u952e\u6269\u5c55', expansion_lines))

    relation_lines = [
        f'{formatter.format(step.from_node_id)} {_relation_name(bundle, step.relation)} {formatter.format(step.to_node_id)}'
        for step in trace_steps
    ]
    relation_lines = _dedupe_preserve_order(relation_lines)
    if relation_lines:
        sections.append(_render_trace_section('\u547d\u4e2d\u7684\u5173\u952e\u5173\u7cfb', relation_lines))

    fallback_lines = _split_trace_lines(bundle.search_trace.seed_resolution_error)
    if fallback_lines:
        sections.append(_render_trace_section('\u89e3\u6790\u56de\u9000', fallback_lines))

    return '\n\n'.join(section for section in sections if section)


def _render_trace_section(title: str, lines: list[str]) -> str:
    cleaned_lines = [line.strip() for line in lines if line and line.strip()]
    if not cleaned_lines:
        return ''
    return title + '\n' + '\n'.join(f'- {line}' for line in cleaned_lines)


def _split_trace_lines(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r'[\r\n?;]+', text)
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
        key = (left, '[\u5173\u8054]', right)
        if key in visited_edges:
            continue
        visited_edges.add(key)
        fallback_lines.append(f'{left} [\u5173\u8054] {right}')
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
    label = re.split(r'[\u3002\uff1b;\uff0c,\uff1a:\n\r]', label, maxsplit=1)[0].strip()
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
            detail = f'??????{supporting[0]}' if supporting else ''
            return TemplateAnswer(answer=f'?????????{question}?????????? {deadline}?{detail}?', insufficient_evidence=False)
        return TemplateAnswer(answer=f'?????????{question}?????????????? {deadline}??', insufficient_evidence=False)

    if instance_count <= 0:
        return TemplateAnswer(answer=f'???????????????{question}???????', insufficient_evidence=True)

    affected = reasoning_result.get('affected_entities') if isinstance(reasoning_result, dict) else []
    affected_count = len(affected) if isinstance(affected, list) else 0
    return TemplateAnswer(answer=f'???????????? {affected_count or instance_count} ????????????', insufficient_evidence=False)
