from __future__ import annotations

import re
from collections import defaultdict

from ..models.ontology import OntologyGraph, OntologyObject, OntologyRelation
from .intent_resolver import IntentResolution, resolve_intent
from .query_parser import build_retrieval_plan, merge_seed_entities, normalize_query, parse_query
from .ontology_query_models import EvidenceItem, OntologyEvidenceBundle, RetrievalStep, SearchTrace, TraceExpansionStep

_RUNTIME_HINTS = {
    '宕机',
    '离线',
    '在线',
    '实时',
    '状态',
    '当前',
    '现在',
    '今天',
    '昨天',
    '最近',
    '实例',
    '服务器',
    '机器',
    'cpu',
    'memory',
    'usage',
    '利用率',
    '延迟',
    '告警',
}
_RELATION_WORDS = {'关系', '关联', '依赖', '上下游', '影响', '链接'}
_RELATION_TRANSLATIONS = {
    'HAS': '包含',
    'AGGREGATES': '聚合',
    'APPLIES_TO': '作用于',
    'ASSIGNED_TO': '分配给',
    'ASSIGNS': '指派给',
    'CONSTRAINS': '约束',
    'CONTAINS': '包含',
    'DEFINES': '定义',
    'DELIVERS': '交付',
    'DEPENDS_ON': '依赖',
    'EXECUTES': '执行',
    'GENERATES': '生成',
    'OCCURS_AT': '发生于位置',
    'OCCURS_IN': '发生于机房',
    'REFERENCES': '引用',
    'SHIPS': '运输',
    'USES': '使用',
}


def retrieve_ontology_evidence(graph: OntologyGraph, question: str) -> OntologyEvidenceBundle:
    parsed_query = parse_query(question)
    retrieval_plan = build_retrieval_plan(parsed_query)
    normalized_query = parsed_query.normalized_query
    normalized_question = _normalize_text(normalized_query)
    tokens = _question_tokens(normalized_query)
    runtime_question = _looks_like_runtime_question(normalized_question)
    preferred_relations = set(retrieval_plan.allowed_relations or [])

    node_scores: dict[str, int] = {}
    node_reasons: dict[str, list[str]] = defaultdict(list)
    for obj in graph.objects.values():
        score, reasons = _score_object(obj, normalized_question, tokens)
        if score > 0 and _is_entity_name_fully_shadowed_by_mentions(obj.name, normalized_query, parsed_query.canonical_entities, parsed_query.mentions):
            score = 0
        if score > 0:
            node_scores[obj.id] = score
            node_reasons[obj.id].extend(reasons)

    high_confidence_seed_ids = _canonical_entities_to_object_ids(graph, parsed_query.high_confidence_entities)
    candidate_seed_ids = _canonical_entities_to_object_ids(graph, parsed_query.candidate_entities)
    for object_id in high_confidence_seed_ids:
        canonical = object_id.split(':', 1)[-1]
        node_scores[object_id] = node_scores.get(object_id, 0) + 200
        node_reasons[object_id].append(f'\u547d\u4e2d\u9ad8\u7f6e\u4fe1\u5b9e\u4f53 {canonical}')

    relation_matches: list[tuple[int, str, OntologyRelation, list[str]]] = []
    for index, relation in enumerate(graph.relations, start=1):
        score, reasons = _score_relation(relation, normalized_question, tokens)
        if relation.relation in preferred_relations:
            score += 10
            reasons.append(f'\u547d\u4e2d\u610f\u56fe\u4f18\u5148\u5173\u7cfb {relation.relation}')
        if score <= 0:
            continue
        edge_id = _edge_id(index)
        reason_lines = _dedupe_preserve_order(reasons)
        relation_matches.append((score, edge_id, relation, reason_lines))
        node_scores.setdefault(relation.source_id, 0)
        node_scores[relation.source_id] += max(score // 2, 1)
        node_reasons[relation.source_id].append(f'\u547d\u4e2d\u5173\u7cfb {relation.relation} \u7684\u5173\u8054\u8282\u70b9')
        node_scores.setdefault(relation.target_id, 0)
        node_scores[relation.target_id] += max(score // 2, 1)
        node_reasons[relation.target_id].append(f'\u547d\u4e2d\u5173\u7cfb {relation.relation} \u7684\u5173\u8054\u8282\u70b9')

    intent_resolution = IntentResolution(seeds=[], reasoning='', source='fallback', error='')
    seed_match_resolution = intent_resolution
    seed_node_ids = list(high_confidence_seed_ids)
    seed_resolution_source = ''
    seed_resolution_reasoning = ''
    seed_resolution_error = ''

    if seed_node_ids:
        seed_resolution_source = 'alias_rule'
        seed_resolution_reasoning = '\uff1b'.join(parsed_query.high_confidence_entities)

    if candidate_seed_ids:
        candidate_resolution = resolve_intent(graph, normalized_query, candidate_ids=candidate_seed_ids)
        candidate_selected_ids = [seed for seed in candidate_resolution.seeds if graph.get_object(seed) is not None]
        for seed_id in candidate_selected_ids:
            node_scores[seed_id] = node_scores.get(seed_id, 0) + 40
            node_reasons[seed_id].append('\u004c\u004c\u004d\u5019\u9009\u5224\u522b\u547d\u4e2d')
        if candidate_selected_ids:
            seed_node_ids = merge_seed_entities(seed_node_ids, candidate_selected_ids)
            selected_candidate_entities = _object_ids_to_canonical_entities(candidate_selected_ids)
            if high_confidence_seed_ids:
                seed_resolution_source = 'hybrid'
                seed_resolution_reasoning = '\uff1b'.join(
                    merge_seed_entities(parsed_query.high_confidence_entities, selected_candidate_entities)
                )
            else:
                seed_resolution_source = candidate_resolution.source
                seed_resolution_reasoning = candidate_resolution.reasoning or '\uff1b'.join(selected_candidate_entities)
            seed_resolution_error = candidate_resolution.error
            seed_match_resolution = candidate_resolution

    if not seed_node_ids:
        intent_resolution = resolve_intent(graph, normalized_query)
        seed_match_resolution = intent_resolution
        llm_seed_ids = [seed for seed in intent_resolution.seeds if graph.get_object(seed) is not None]
        for seed_id in llm_seed_ids:
            node_scores[seed_id] = node_scores.get(seed_id, 0) + 40
            node_reasons[seed_id].append('\u004c\u004c\u004d\u5168\u91cf\u56de\u9000\u547d\u4e2d')
        if llm_seed_ids:
            seed_node_ids = list(llm_seed_ids)
        else:
            seed_node_ids = _select_seed_node_ids(node_scores)
        seed_resolution_source = intent_resolution.source
        seed_resolution_reasoning = intent_resolution.reasoning
        seed_resolution_error = intent_resolution.error

    display_name_map = _build_display_name_map(graph)
    relation_name_map = _build_relation_name_map(graph)

    matched_node_ids = list(seed_node_ids)
    matched_edge_ids: list[str] = []
    evidence_chain: list[EvidenceItem] = []
    evidence_counter = 1
    evidence_ids_for_steps: list[str] = []
    trace_snapshot_node_ids = list(seed_node_ids)
    trace_snapshot_edge_ids: list[str] = []
    expansion_steps: list[TraceExpansionStep] = []

    for node_id in seed_node_ids:
        obj = graph.get_object(node_id)
        if obj is None:
            continue
        evidence_id = _evidence_id(evidence_counter)
        evidence_counter += 1
        evidence_ids_for_steps.append(evidence_id)
        evidence_chain.append(
            EvidenceItem(
                evidence_id=evidence_id,
                kind='seed',
                label=obj.name,
                message=f'\u95ee\u9898\u547d\u4e2d\u4e86\u5b9e\u4f53 {display_name_map.get(obj.id, obj.name)}',
                node_ids=[obj.id],
                why_matched=_seed_match_reasons(node_reasons.get(obj.id), seed_match_resolution),
            )
        )

    relation_reason_map = {edge_id: reasons for _, edge_id, _, reasons in relation_matches}
    for index, relation in _iter_seed_adjacent_relations(graph.relations, seed_node_ids, preferred_relations, relation_reason_map):
        edge_id = _edge_id(index)
        matched_edge_ids.append(edge_id)
        matched_node_ids.extend([relation.source_id, relation.target_id])
        trace_snapshot_node_ids.extend([relation.source_id, relation.target_id])
        trace_snapshot_edge_ids.append(edge_id)
        reason_lines = _dedupe_preserve_order(relation_reason_map.get(edge_id) or ['\u5173\u7cfb\u90bb\u63a5\u6269\u5c55'])
        expansion_steps.append(
            TraceExpansionStep(
                step=len(expansion_steps) + 1,
                from_node_id=relation.source_id,
                edge_id=edge_id,
                to_node_id=relation.target_id,
                relation=relation.relation,
                reason='\uff1b'.join(reason_lines),
                snapshot_node_ids=_dedupe_preserve_order(list(trace_snapshot_node_ids)),
                snapshot_edge_ids=_dedupe_preserve_order(list(trace_snapshot_edge_ids)),
            )
        )
        evidence_id = _evidence_id(evidence_counter)
        evidence_counter += 1
        evidence_ids_for_steps.append(evidence_id)
        label = f'{_object_label(graph, relation.source_id)} {relation.relation} {_object_label(graph, relation.target_id)}'
        evidence_chain.append(
            EvidenceItem(
                evidence_id=evidence_id,
                kind='relation',
                label=label,
                message=str(relation.attributes.get('description', '') or label),
                node_ids=[relation.source_id, relation.target_id],
                edge_ids=[edge_id],
                why_matched=reason_lines,
            )
        )

    matched_node_ids = _dedupe_preserve_order(matched_node_ids)
    matched_edge_ids = _dedupe_preserve_order(matched_edge_ids)

    highlight_steps: list[RetrievalStep] = []
    if seed_node_ids:
        highlight_steps.append(
            RetrievalStep(
                action='anchor_node',
                message='\u5df2\u5b9a\u4f4d\u95ee\u9898\u76f8\u5173\u7684\u6838\u5fc3\u5b9e\u4f53',
                node_ids=list(seed_node_ids),
                edge_ids=[],
                evidence_ids=[item.evidence_id for item in evidence_chain if item.kind == 'seed'],
            )
        )

    if matched_edge_ids:
        highlight_steps.append(
            RetrievalStep(
                action='expand_neighbors',
                message='\u6b63\u5728\u6269\u5c55\u76f8\u90bb\u5173\u7cfb\u8282\u70b9',
                node_ids=list(matched_node_ids),
                edge_ids=list(matched_edge_ids),
                evidence_ids=[item.evidence_id for item in evidence_chain if item.kind == 'relation'],
            )
        )

    if matched_node_ids:
        highlight_steps.append(
            RetrievalStep(
                action='filter_nodes',
                message='\u6b63\u5728\u8fc7\u6ee4\u65e0\u5173\u8282\u70b9\u5e76\u4fdd\u7559\u5019\u9009\u5b50\u56fe',
                node_ids=list(matched_node_ids),
                edge_ids=list(matched_edge_ids),
                evidence_ids=list(evidence_ids_for_steps),
            )
        )
        highlight_steps.append(
            RetrievalStep(
                action='focus_subgraph',
                message='\u5df2\u805a\u7126\u6700\u7ec8\u8bc1\u636e\u5b50\u56fe',
                node_ids=list(matched_node_ids),
                edge_ids=list(matched_edge_ids),
                evidence_ids=list(evidence_ids_for_steps),
            )
        )

    insufficient_evidence = runtime_question or not matched_node_ids
    if not evidence_chain:
        evidence_chain.append(
            EvidenceItem(
                evidence_id=_evidence_id(evidence_counter),
                kind='filter_result',
                label='\u672a\u627e\u5230\u5339\u914d\u5b9e\u4f53',
                message='\u5f53\u524d\u95ee\u9898\u672a\u5728\u672c\u4f53\u5b9a\u4e49\u4e2d\u547d\u4e2d\u53ef\u7528\u5b9e\u4f53\u6216\u5173\u7cfb',
                why_matched=['\u672a\u547d\u4e2d\u5f53\u524d\u672c\u4f53\u4e2d\u7684\u5b9a\u4e49\u5b9e\u4f53'],
            )
        )

    return OntologyEvidenceBundle(
        question=question,
        seed_node_ids=list(seed_node_ids),
        matched_node_ids=list(matched_node_ids),
        matched_edge_ids=list(matched_edge_ids),
        highlight_steps=highlight_steps,
        evidence_chain=evidence_chain,
        insufficient_evidence=insufficient_evidence,
        search_trace=SearchTrace(
            seed_node_ids=list(seed_node_ids),
            seed_resolution_source=seed_resolution_source,
            seed_resolution_reasoning=seed_resolution_reasoning,
            seed_resolution_error=seed_resolution_error,
            expansion_steps=expansion_steps,
        ),
        display_name_map=display_name_map,
        relation_name_map=relation_name_map,
    )


def _select_seed_node_ids(node_scores: dict[str, int]) -> list[str]:
    if not node_scores:
        return []
    ranked = sorted(node_scores.items(), key=lambda item: (-item[1], item[0]))
    top_score = ranked[0][1]
    threshold = max(top_score - 25, 1)
    return [node_id for node_id, score in ranked if score >= threshold][:3]


def _score_object(obj: OntologyObject, normalized_question: str, tokens: list[str]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    name_candidates = [obj.name, *obj.aliases]
    for candidate in name_candidates:
        normalized_candidate = _normalize_text(candidate)
        if not normalized_candidate:
            continue
        if normalized_candidate in normalized_question:
            score += 120 if candidate == obj.name else 80
            reasons.append(f'命中实体名 {candidate}')

    text_fields = {
        '中文释义': obj.attributes.get('chinese_description', ''),
        '所属分组': obj.attributes.get('group', ''),
        '语义定义': obj.attributes.get('semantic_definition', ''),
        '关键属性': ' '.join(_named_item_texts(obj.attributes.get('key_properties'))),
        '状态建议': ' '.join(_named_item_texts(obj.attributes.get('status_values'))),
        '规则约束': ' '.join(_string_values(obj.attributes.get('rules'))),
        '说明': ' '.join(_string_values(obj.attributes.get('notes'))),
    }
    for label, value in text_fields.items():
        normalized_value = _normalize_text(value)
        if not normalized_value:
            continue
        if normalized_value in normalized_question:
            score += 40
            reasons.append(f'{label}整体命中')
            continue
        for token in tokens:
            if len(token) < 2:
                continue
            if token in normalized_value:
                score += 15
                reasons.append(f'{label}命中关键词 {token}')

    if any(word in normalized_question for word in _RELATION_WORDS) and score > 0:
        score += 5
    return score, _dedupe_preserve_order(reasons)


def _score_relation(relation: OntologyRelation, normalized_question: str, tokens: list[str]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    relation_texts = [relation.relation, relation.attributes.get('description', '')]
    for text in relation_texts:
        normalized_text = _normalize_text(text)
        if not normalized_text:
            continue
        if normalized_text in normalized_question:
            score += 70
            reasons.append(f'命中关系文本 {text}')
            continue
        for token in tokens:
            if len(token) < 2:
                continue
            if token in normalized_text:
                score += 12
                reasons.append(f'关系文本命中关键词 {token}')
    return score, _dedupe_preserve_order(reasons)


def _build_display_name_map(graph: OntologyGraph) -> dict[str, str]:
    display_name_map: dict[str, str] = {}
    for object_id, obj in graph.objects.items():
        english_name = str(obj.name or object_id.split(':', 1)[-1]).strip() or object_id
        chinese_name = str(obj.attributes.get('chinese_description', '') or '').strip()
        if chinese_name and chinese_name != english_name:
            display_name_map[object_id] = f'{chinese_name}({english_name})'
        else:
            display_name_map[object_id] = english_name
    return display_name_map


def _build_relation_name_map(graph: OntologyGraph) -> dict[str, str]:
    relation_name_map: dict[str, str] = {}
    for relation in graph.relations:
        translated = _RELATION_TRANSLATIONS.get(relation.relation, relation.relation)
        if translated.startswith('[') and translated.endswith(']'):
            relation_name_map[relation.relation] = translated
        else:
            relation_name_map[relation.relation] = f'[{translated}]'
    return relation_name_map



def _canonical_entities_to_object_ids(graph: OntologyGraph, canonical_entities: list[str]) -> list[str]:
    result: list[str] = []
    for canonical in canonical_entities:
        object_id = f'object_type:{canonical}'
        if graph.get_object(object_id) is None:
            continue
        result.append(object_id)
    return _dedupe_preserve_order(result)


def _object_ids_to_canonical_entities(object_ids: list[str]) -> list[str]:
    return _dedupe_preserve_order([object_id.split(':', 1)[-1] for object_id in object_ids if object_id])

def _seed_match_reasons(existing_reasons: list[str] | None, intent_resolution: IntentResolution) -> list[str]:
    if existing_reasons:
        return _dedupe_preserve_order(existing_reasons)
    if intent_resolution.source == 'llm':
        if intent_resolution.reasoning:
            return [intent_resolution.reasoning]
        return ['语义意图解析命中']
    return ['实体名称匹配']


def _normalize_query(value: object) -> str:
    return normalize_query(value)


def _normalize_text(value: object) -> str:
    return re.sub(r'\s+', ' ', str(value or '').strip().lower())


def _question_tokens(question: str) -> list[str]:
    tokens = re.findall(r'[a-z0-9_]+|[\u4e00-\u9fff]+', _normalize_text(question))
    return _dedupe_preserve_order(tokens)


def _named_item_texts(values: object) -> list[str]:
    texts: list[str] = []
    if not isinstance(values, list):
        return texts
    for item in values:
        if isinstance(item, dict):
            name = str(item.get('name', '') or '').strip()
            description = str(item.get('description', '') or '').strip()
            joined = ' '.join(part for part in (name, description) if part)
            if joined:
                texts.append(joined)
            continue
        text = str(item or '').strip()
        if text:
            texts.append(text)
    return texts


def _is_entity_name_fully_shadowed_by_mentions(
    entity_name: str,
    normalized_query: str,
    canonical_entities: list[str],
    mentions: list[object],
) -> bool:
    if entity_name in canonical_entities:
        return False
    query_text = _normalize_text(normalized_query)
    needle = _normalize_text(entity_name)
    if not needle:
        return False
    spans: list[tuple[int, int]] = []
    start = query_text.find(needle)
    while start != -1:
        spans.append((start, start + len(needle)))
        start = query_text.find(needle, start + 1)
    if not spans:
        return False
    mention_spans = [(mention.start, mention.end) for mention in mentions]
    return all(any(span_start >= mention_start and span_end <= mention_end for mention_start, mention_end in mention_spans) for span_start, span_end in spans)


def _string_values(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [text for text in (str(item or '').strip() for item in values) if text]



def _iter_seed_adjacent_relations(
    relations: list[OntologyRelation],
    seed_node_ids: list[str],
    preferred_relations: set[str],
    relation_reason_map: dict[str, list[str]],
) -> list[tuple[int, OntologyRelation]]:
    seed_rank = {node_id: index for index, node_id in enumerate(seed_node_ids)}
    guided: list[tuple[int, OntologyRelation]] = []
    fallback: list[tuple[int, OntologyRelation]] = []
    for index, relation in enumerate(relations, start=1):
        if relation.source_id not in seed_rank and relation.target_id not in seed_rank:
            continue
        item = (index, relation)
        if _edge_id(index) in relation_reason_map:
            guided.append(item)
        else:
            fallback.append(item)
    candidates = guided or fallback
    candidates.sort(
        key=lambda item: (
            min(seed_rank.get(item[1].source_id, 999), seed_rank.get(item[1].target_id, 999)),
            0 if item[1].relation in preferred_relations else 1,
            item[0],
        )
    )
    return candidates


def _edge_id(index: int) -> str:
    return f'e{index}'


def _evidence_id(index: int) -> str:
    return f'E{index}'


def _object_label(graph: OntologyGraph, object_id: str) -> str:
    obj = graph.get_object(object_id)
    return obj.name if obj is not None else object_id


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _looks_like_runtime_question(normalized_question: str) -> bool:
    return any(hint in normalized_question for hint in _RUNTIME_HINTS)

