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
    metadata = fact_pack.get('metadata') if isinstance(fact_pack, dict) else {}
    if not isinstance(metadata, dict):
        metadata = {}
    target_attributes = metadata.get('target_attributes') if isinstance(metadata.get('target_attributes'), list) else []
    anchor = metadata.get('anchor') if isinstance(metadata.get('anchor'), dict) else {}

    if target_attributes and instance_count > 0:
        anchor_entity = str(anchor.get('entity') or '').strip()
        rows = instances.get(anchor_entity) if isinstance(instances, dict) else None
        if isinstance(rows, list) and rows:
            row = rows[0] if isinstance(rows[0], dict) else {}
            attribute = str(target_attributes[0])
            value = row.get(attribute) if isinstance(row, dict) else None
            identifier = str(anchor.get('id') or '').strip() or str((anchor.get('identifier') or {}).get('value') or '').strip()
            if value is not None and str(value).strip():
                if attribute.endswith('_status'):
                    return TemplateAnswer(answer=f'{identifier or question} \u5f53\u524d\u72b6\u6001\u4e3a {value}\u3002', insufficient_evidence=False)
                return TemplateAnswer(answer=f'{identifier or question} \u7684 {attribute} \u4e3a {value}\u3002', insufficient_evidence=False)

    if summary.get('answer_type') == 'deadline_risk':
        at_risk = bool(deadline_assessment.get('at_risk'))
        deadline = str(deadline_assessment.get('deadline') or '').strip() or '\u76ee\u6807\u65e5\u671f'
        supporting = deadline_assessment.get('supporting_facts') or []
        if at_risk:
            detail = f'\u4e3b\u8981\u4f9d\u636e\uff1a{supporting[0]}\u3002' if supporting else ''
            return TemplateAnswer(
                answer=f'\u95ee\u9898\u201c{question}\u201d\u53ef\u80fd\u5f71\u54cd {deadline} \u4ea4\u4ed8\u3002{detail}',
                insufficient_evidence=False,
            )
        return TemplateAnswer(
            answer=f'\u5f53\u524d\u8bc1\u636e\u663e\u793a\u95ee\u9898\u201c{question}\u201d\u6682\u672a\u5f71\u54cd {deadline} \u4ea4\u4ed8\u3002',
            insufficient_evidence=False,
        )

    if instance_count <= 0:
        return TemplateAnswer(
            answer=f'\u8bc1\u636e\u4e0d\u8db3\uff1a\u5f53\u524d\u672a\u68c0\u7d22\u5230\u4e0e\u201c{question}\u201d\u76f4\u63a5\u76f8\u5173\u7684\u5b9e\u4f8b\u6570\u636e\u3002',
            insufficient_evidence=True,
        )

    links = _instance_links(fact_pack)
    anchor_entity = str(anchor.get('entity') or '').strip()
    anchor_id = str(anchor.get('id') or '').strip()

    if links and anchor_entity and anchor_id and _looks_like_relation_question(question):
        return TemplateAnswer(
            answer=_build_relation_instance_summary(anchor_entity, anchor_id, links),
            insufficient_evidence=False,
        )

    if _looks_like_impact_question(question):
        return TemplateAnswer(
            answer=_build_impact_instance_summary(question, anchor_entity, anchor_id, instances, links),
            insufficient_evidence=False,
        )

    return TemplateAnswer(
        answer=_build_instance_overview_summary(question, anchor_entity, anchor_id, instances, links),
        insufficient_evidence=False,
    )


_ENTITY_LABELS = {
    'Room': '\u673a\u623f',
    'Floor': '\u697c\u5c42',
    'PoD': 'PoD',
    'PoDPosition': 'PoD\u843d\u4f4d',
    'ActivityInstance': '\u6d3b\u52a8\u5b9e\u4f8b',
    'RoomMilestone': '\u673a\u623f\u91cc\u7a0b\u7891',
    'WorkAssignment': '\u65bd\u5de5\u5206\u914d',
    'Project': '\u9879\u76ee',
}

_STATUS_KEYS = ('room_status', 'pod_status', 'activity_status', 'milestone_status', 'position_status', 'project_status')
_TIME_KEYS = ('due_time', 'planned_start_time', 'planned_finish_time', 'latest_finish_time', 'assignment_date')
_TARGET_KEYS = ('target_pod_count', 'required_handover_pod_count', 'max_pod_capacity')


def _instance_links(fact_pack: dict[str, object]) -> list[dict[str, str]]:
    raw = fact_pack.get('links') if isinstance(fact_pack, dict) else None
    if not isinstance(raw, list):
        return []
    result: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            result.append(
                {
                    'source_entity': str(item['source_entity']),
                    'source_id': str(item['source_id']),
                    'relation': str(item['relation']),
                    'target_entity': str(item['target_entity']),
                    'target_id': str(item['target_id']),
                }
            )
        except Exception:
            continue
    return result


def _looks_like_relation_question(question: str) -> bool:
    text = str(question or '')
    return any(token in text for token in ('\u5173\u7cfb', '\u5173\u8054', '\u76f8\u5173', '\u8fde\u63a5'))


def _looks_like_impact_question(question: str) -> bool:
    text = str(question or '')
    return any(token in text for token in ('\u5f71\u54cd', '\u98ce\u9669', '\u65ad\u7535', '\u505c\u7535', '\u706b\u707e', '\u5ef6\u671f', '\u5ef6\u8bef', '\u63a8\u8fdf'))


def _build_relation_instance_summary(anchor_entity: str, anchor_id: str, links: list[dict[str, str]]) -> str:
    related = _collect_direct_neighbors(anchor_entity, anchor_id, links)
    if not related:
        return f'{anchor_id or anchor_entity} \u5f53\u524d\u672a\u68c0\u7d22\u5230\u76f4\u63a5\u5173\u8054\u7684\u5b9e\u4f8b\u3002'

    grouped: dict[str, list[str]] = {}
    for entity, instance_id in related:
        grouped.setdefault(entity, []).append(instance_id)

    segments: list[str] = []
    for entity, ids in grouped.items():
        label = _ENTITY_LABELS.get(entity, entity)
        segments.append(f'{label} {_join_labels(ids)}')
    return f'{anchor_id} \u5f53\u524d\u76f4\u63a5\u5173\u8054\u7684\u5b9e\u4f8b\u5305\u62ec {_join_clauses(segments)}\u3002'


def _build_impact_instance_summary(question: str, anchor_entity: str, anchor_id: str, instances: object, links: list[dict[str, str]]) -> str:
    clauses: list[str] = []

    anchor_row = _find_instance_row(instances, anchor_entity, anchor_id)
    anchor_profile = _describe_instance(anchor_entity, anchor_id, anchor_row)
    if anchor_profile:
        clauses.append(anchor_profile)

    for row in _instance_rows(instances, 'PoD')[:3]:
        pod_id = _instance_identifier('PoD', row)
        status = _first_present(row, _STATUS_KEYS)
        position = _linked_neighbor_ids('PoD', pod_id, 'PoDPosition', links)
        if status and position:
            clauses.append(f'{pod_id} \u5f53\u524d\u72b6\u6001\u4e3a {status}\uff0c\u5df2\u5173\u8054\u843d\u4f4d {_join_labels(position)}')
        elif status:
            clauses.append(f'{pod_id} \u5f53\u524d\u72b6\u6001\u4e3a {status}')

    for row in _instance_rows(instances, 'ActivityInstance')[:3]:
        activity_id = _instance_identifier('ActivityInstance', row)
        status = _first_present(row, _STATUS_KEYS)
        if status:
            clauses.append(f'{activity_id} \u5f53\u524d\u72b6\u6001\u4e3a {status}')

    for row in _instance_rows(instances, 'RoomMilestone')[:2]:
        milestone_id = _instance_identifier('RoomMilestone', row)
        status = _first_present(row, _STATUS_KEYS)
        due_time = _first_present(row, _TIME_KEYS)
        target = _first_present(row, _TARGET_KEYS)
        details = []
        if status:
            details.append(f'\u72b6\u6001\u4e3a {status}')
        if target:
            details.append(f'\u76ee\u6807\u503c\u4e3a {target}')
        if due_time:
            details.append(f'\u622a\u6b62\u65f6\u95f4\u4e3a {due_time}')
        if details:
            clauses.append(f'{milestone_id} ' + '\uff0c'.join(details))

    clauses = _dedupe_preserve_order([item for item in clauses if item])
    if not clauses:
        return f'{question}\uff0c\u5f53\u524d\u5df2\u68c0\u7d22\u5230\u76f8\u5173\u5b9e\u4f8b\uff0c\u4f46\u81ea\u52a8\u6458\u8981\u672a\u63d0\u70bc\u51fa\u5173\u952e\u4e1a\u52a1\u70b9\u3002'

    intro = f'{anchor_id or anchor_entity} \u5bf9\u5e94\u95ee\u9898\u201c{question}\u201d\u7684\u5173\u952e\u5f71\u54cd\u96c6\u4e2d\u5728\u4ee5\u4e0b\u5b9e\u4f8b\uff1a'
    return intro + '\uff1b'.join(clauses) + '\u3002'


def _build_instance_overview_summary(question: str, anchor_entity: str, anchor_id: str, instances: object, links: list[dict[str, str]]) -> str:
    anchor_row = _find_instance_row(instances, anchor_entity, anchor_id)
    profile = _describe_instance(anchor_entity, anchor_id, anchor_row)
    neighbors = _collect_direct_neighbors(anchor_entity, anchor_id, links)
    if neighbors:
        grouped: dict[str, list[str]] = {}
        for entity, instance_id in neighbors:
            grouped.setdefault(entity, []).append(instance_id)
        neighbor_segments = [f'{_ENTITY_LABELS.get(entity, entity)} {_join_labels(ids)}' for entity, ids in grouped.items()]
        if profile:
            return profile + '\uff1b\u5f53\u524d\u76f4\u63a5\u5173\u8054 ' + _join_clauses(neighbor_segments) + '\u3002'
        return f'{anchor_id or anchor_entity} \u5f53\u524d\u76f4\u63a5\u5173\u8054 {_join_clauses(neighbor_segments)}\u3002'
    if profile:
        return profile + '\u3002'
    return f'{question}\uff0c\u5f53\u524d\u5df2\u68c0\u7d22\u5230\u76f8\u5173\u5b9e\u4f8b\uff0c\u4f46\u672a\u6574\u7406\u51fa\u66f4\u5b8c\u6574\u7684\u5b9e\u4f8b\u753b\u50cf\u3002'


def _describe_instance(entity: str, instance_id: str, row: dict[str, object] | None) -> str:
    if not instance_id:
        return ''
    label = _ENTITY_LABELS.get(entity, entity)
    if not isinstance(row, dict):
        return f'{label} {instance_id}'
    details: list[str] = []
    status = _first_present(row, _STATUS_KEYS)
    if status:
        details.append(f'\u72b6\u6001\u4e3a {status}')
    for key in _TARGET_KEYS:
        value = row.get(key)
        if value is not None and str(value).strip():
            details.append(f'{key}={value}')
            break
    for key in _TIME_KEYS:
        value = row.get(key)
        if value is not None and str(value).strip():
            details.append(f'{key}={value}')
            break
    if details:
        return f'{label} {instance_id} ' + '\uff0c'.join(details)
    return f'{label} {instance_id}'


def _collect_direct_neighbors(anchor_entity: str, anchor_id: str, links: list[dict[str, str]]) -> list[tuple[str, str]]:
    neighbors: list[tuple[str, str]] = []
    for link in links:
        if link['source_entity'] == anchor_entity and link['source_id'] == anchor_id:
            neighbors.append((link['target_entity'], link['target_id']))
        elif link['target_entity'] == anchor_entity and link['target_id'] == anchor_id:
            neighbors.append((link['source_entity'], link['source_id']))
    deduped: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in neighbors:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _linked_neighbor_ids(anchor_entity: str, anchor_id: str, neighbor_entity: str, links: list[dict[str, str]]) -> list[str]:
    values: list[str] = []
    for entity, instance_id in _collect_direct_neighbors(anchor_entity, anchor_id, links):
        if entity == neighbor_entity:
            values.append(instance_id)
    return _dedupe_preserve_order(values)


def _instance_rows(instances: object, entity: str) -> list[dict[str, object]]:
    if not isinstance(instances, dict):
        return []
    rows = instances.get(entity)
    if not isinstance(rows, list):
        return []
    return [item for item in rows if isinstance(item, dict)]


def _find_instance_row(instances: object, entity: str, instance_id: str) -> dict[str, object] | None:
    if not entity or not instance_id:
        return None
    for row in _instance_rows(instances, entity):
        if _instance_identifier(entity, row) == instance_id:
            return row
    return None


def _instance_identifier(entity_name: str, row: dict[str, object]) -> str:
    for key in ('id', f'{entity_name.lower()}_id', 'pod_code', 'assignment_id', 'activity_id', 'pod_schedule_id', 'position_id', 'project_id', 'milestone_id', 'room_id', 'floor_id'):
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return ''


def _first_present(row: dict[str, object], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ''


def _join_labels(values: list[str]) -> str:
    values = [str(value).strip() for value in values if str(value).strip()]
    values = _dedupe_preserve_order(values)
    if not values:
        return ''
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f'{values[0]} \u548c {values[1]}'
    return '\u3001'.join(values[:-1]) + f' \u548c {values[-1]}'


def _join_clauses(values: list[str]) -> str:
    values = [str(value).strip() for value in values if str(value).strip()]
    if not values:
        return ''
    if len(values) == 1:
        return values[0]
    return '\uff0c'.join(values)
