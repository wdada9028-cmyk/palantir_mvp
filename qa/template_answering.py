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
    impact_summary = reasoning_result.get('impact_summary', {}) if isinstance(reasoning_result, dict) else {}

    if summary.get('answer_type') == 'deadline_risk':
        at_risk = bool(deadline_assessment.get('at_risk'))
        deadline = str(deadline_assessment.get('deadline') or '').strip() or '\u76ee\u6807\u65e5\u671f'
        supporting = deadline_assessment.get('supporting_facts') or []
        if at_risk:
            detail = f"\u4e3b\u8981\u4f9d\u636e\uff1a{supporting[0]}\u3002" if supporting else ''
            return TemplateAnswer(
                answer=f"\u5224\u65ad\u7ed3\u679c\uff1a\u95ee\u9898\u201c{question}\u201d\u53ef\u80fd\u5f71\u54cd {deadline} \u4ea4\u4ed8\u3002{detail}",
                insufficient_evidence=False,
            )
        return TemplateAnswer(
            answer=f"\u5224\u65ad\u7ed3\u679c\uff1a\u5f53\u524d\u8bc1\u636e\u663e\u793a\u95ee\u9898\u201c{question}\u201d\u6682\u672a\u5f71\u54cd {deadline} \u4ea4\u4ed8\u3002",
            insufficient_evidence=False,
        )

    if instance_count <= 0:
        return TemplateAnswer(
            answer=f"\u8bc1\u636e\u4e0d\u8db3\uff1a\u5f53\u524d\u672a\u68c0\u7d22\u5230\u4e0e\u201c{question}\u201d\u76f4\u63a5\u76f8\u5173\u7684\u5b9e\u4f8b\u6570\u636e\u3002",
            insufficient_evidence=True,
        )

    direct_counts = impact_summary.get('direct_counts') if isinstance(impact_summary, dict) else {}
    propagated_counts = impact_summary.get('propagated_counts') if isinstance(impact_summary, dict) else {}
    if (isinstance(direct_counts, dict) and direct_counts) or (isinstance(propagated_counts, dict) and propagated_counts):
        parts: list[str] = ['\u5df2\u8bc6\u522b\u4ee5\u4e0b\u6f5c\u5728\u5f71\u54cd\uff1a']
        if isinstance(direct_counts, dict) and direct_counts:
            parts.append(f"\u76f4\u63a5\u5f71\u54cd\uff1a{_format_impact_counts(direct_counts)}\u3002")
        if isinstance(propagated_counts, dict) and propagated_counts:
            parts.append(f"\u4f20\u64ad\u5f71\u54cd\uff1a{_format_impact_counts(propagated_counts)}\u3002")
        parts.append('\u5efa\u8bae\u4f18\u5148\u6838\u67e5\u65bd\u5de5\u5206\u914d\u3001\u76f8\u5173PoD\u3001\u65bd\u5de5\u6d3b\u52a8\u4e0ePoD\u6392\u671f\u3002')
        return TemplateAnswer(answer=''.join(parts), insufficient_evidence=False)

    affected = reasoning_result.get('affected_entities') if isinstance(reasoning_result, dict) else []
    affected_count = len(affected) if isinstance(affected, list) else 0
    return TemplateAnswer(
        answer=f"\u5df2\u8bc6\u522b\u6f5c\u5728\u53d7\u5f71\u54cd\u5bf9\u8c61 {affected_count or instance_count} \u4e2a\uff0c\u5efa\u8bae\u4f18\u5148\u6838\u67e5\u5173\u952e\u8def\u5f84\u4efb\u52a1\u3002",
        insufficient_evidence=False,
    )


def _format_impact_counts(counts: dict[str, object]) -> str:
    parts: list[str] = []
    for entity, value in counts.items():
        try:
            count = int(value)
        except Exception:
            count = 0
        if count <= 0:
            continue
        parts.append(f'{entity} {count} \u4e2a')
    return '\u3001'.join(parts) if parts else '\u65e0'
