from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation
from cloud_delivery_ontology_palantir.search.intent_resolver import IntentResolution
from cloud_delivery_ontology_palantir.search.query_parser.models import ParsedQuery, IntentResult
from cloud_delivery_ontology_palantir.search.ontology_query_engine import _normalize_query, retrieve_ontology_evidence


_ALL_RELATIONS = {
    'AGGREGATES': '[聚合]',
    'APPLIES_TO': '[作用于]',
    'ASSIGNED_TO': '[分配给]',
    'ASSIGNS': '[指派给]',
    'CONSTRAINS': '[约束]',
    'CONTAINS': '[包含]',
    'DEFINES': '[定义]',
    'DELIVERS': '[交付]',
    'DEPENDS_ON': '[依赖]',
    'EXECUTES': '[执行]',
    'GENERATES': '[生成]',
    'HAS': '[包含]',
    'OCCURS_AT': '[发生于位置]',
    'OCCURS_IN': '[发生于机房]',
    'REFERENCES': '[引用]',
    'SHIPS': '[运输]',
    'USES': '[使用]',
}


def build_test_graph() -> OntologyGraph:
    graph = OntologyGraph(metadata={"title": "测试"})
    graph.add_object(
        OntologyObject(
            id="object_type:PoD",
            type="ObjectType",
            name="PoD",
            attributes={
                "group": "4.3 设备与物流层",
                "chinese_description": "设备落位点",
                "key_properties": [{"name": "pod_id", "description": "PoD ID"}],
            },
        )
    )
    graph.add_object(
        OntologyObject(
            id="object_type:ArrivalPlan",
            type="ObjectType",
            name="ArrivalPlan",
            attributes={"group": "4.6 决策与解释层", "chinese_description": "到货计划"},
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id="object_type:ArrivalPlan",
            target_id="object_type:PoD",
            relation="APPLIES_TO",
            attributes={"description": "到货计划作用于 PoD"},
        )
    )
    return graph


def build_resolver_graph() -> OntologyGraph:
    graph = OntologyGraph(metadata={"title": "resolver"})
    graph.add_object(
        OntologyObject(
            id="object_type:ArrivalPlan",
            type="ObjectType",
            name="ArrivalPlan",
            attributes={"group": "4.6 决策与解释层", "chinese_description": "到货计划"},
        )
    )
    graph.add_object(
        OntologyObject(
            id="object_type:PoDPosition",
            type="ObjectType",
            name="PoDPosition",
            attributes={"group": "4.2 空间层", "chinese_description": "泊位"},
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id="object_type:ArrivalPlan",
            target_id="object_type:PoDPosition",
            relation="REFERENCES",
            attributes={"description": "到货计划引用泊位"},
        )
    )
    return graph


def build_hybrid_graph() -> OntologyGraph:
    graph = OntologyGraph(metadata={'title': 'hybrid'})
    for object_id, name, zh in [
        ('object_type:ConstraintViolation', 'ConstraintViolation', '\u7ea6\u675f\u51b2\u7a81'),
        ('object_type:PlacementPlan', 'PlacementPlan', '\u843d\u4f4d\u65b9\u6848'),
        ('object_type:RoomMilestone', 'RoomMilestone', '\u673a\u623f\u91cc\u7a0b\u7891'),
    ]:
        graph.add_object(
            OntologyObject(
                id=object_id,
                type='ObjectType',
                name=name,
                attributes={'chinese_description': zh},
            )
        )
    graph.add_relation(
        OntologyRelation(
            source_id='object_type:RoomMilestone',
            target_id='object_type:ConstraintViolation',
            relation='CONSTRAINS',
            attributes={'description': '\u673a\u623f\u91cc\u7a0b\u7891\u7ea6\u675f\u7ea6\u675f\u51b2\u7a81'},
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id='object_type:ConstraintViolation',
            target_id='object_type:PlacementPlan',
            relation='REFERENCES',
            attributes={'description': '\u7ea6\u675f\u51b2\u7a81\u5f15\u7528\u843d\u4f4d\u65b9\u6848'},
        )
    )
    return graph


def test_normalize_query_trims_question_mark_and_collapses_spaces():
    assert _normalize_query('  PoD   \u6709\u4ec0\u4e48\u5173\u7cfb\uff1f\uff1f  ') == 'PoD\u6709\u4ec0\u4e48\u5173\u7cfb'


def test_retrieve_ontology_evidence_passes_normalized_query_to_intent_resolver(monkeypatch):
    graph = build_test_graph()
    captured: list[tuple[str, tuple[str, ...] | None]] = []

    def fake_resolve_intent(graph, query, candidate_ids=None):
        captured.append((query, tuple(candidate_ids) if candidate_ids is not None else None))
        return IntentResolution(seeds=[], reasoning='', source='fallback', error='')

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        fake_resolve_intent,
    )

    retrieve_ontology_evidence(graph, '  \u4ea4\u4ed8\u8ba1\u5212   \u6709\u4ec0\u4e48\u5173\u7cfb\uff1f\uff1f  ')

    assert captured == [('\u4ea4\u4ed8\u8ba1\u5212\u6709\u4ec0\u4e48\u5173\u7cfb', None)]


def test_retrieve_ontology_evidence_returns_animation_steps_and_chain():
    graph = build_test_graph()

    result = retrieve_ontology_evidence(graph, "PoD 有什么关系")

    assert result.seed_node_ids == ["object_type:PoD"]
    assert result.highlight_steps
    assert result.evidence_chain
    assert any(step.action == "anchor_node" for step in result.highlight_steps)
    assert any(item.kind == "relation" for item in result.evidence_chain)


def test_retrieve_ontology_evidence_keeps_legacy_step_payload_shape():
    graph = build_test_graph()

    result = retrieve_ontology_evidence(graph, "PoD 有什么关系")
    step = result.highlight_steps[0]
    payload = step.to_dict()

    assert set(payload) == {"action", "message", "node_ids", "edge_ids", "evidence_ids"}
    assert not hasattr(step, "step_title")
    assert not hasattr(step, "new_node_ids")
    assert not hasattr(step, "focus_node_ids")


def test_retrieve_ontology_evidence_records_deterministic_search_trace():
    graph = build_test_graph()

    result = retrieve_ontology_evidence(graph, "PoD 有什么关系")

    assert result.search_trace.seed_node_ids == ["object_type:PoD"]
    assert [step.edge_id for step in result.search_trace.expansion_steps] == ["e1"]
    step = result.search_trace.expansion_steps[0]
    assert step.step == 1
    assert step.from_node_id == "object_type:ArrivalPlan"
    assert step.to_node_id == "object_type:PoD"
    assert step.relation == "APPLIES_TO"
    assert step.snapshot_node_ids == ["object_type:PoD", "object_type:ArrivalPlan"]
    assert step.snapshot_edge_ids == ["e1"]


def test_retrieve_ontology_evidence_prefers_llm_seed_resolution(monkeypatch):
    graph = build_resolver_graph()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        lambda graph, query: IntentResolution(
            seeds=['object_type:ArrivalPlan'],
            reasoning='问题更像在问到货计划',
            source='llm',
            error='',
        ),
    )

    result = retrieve_ontology_evidence(graph, '泊位是什么')

    assert result.seed_node_ids == ['object_type:ArrivalPlan']
    assert result.search_trace.seed_resolution_source == 'llm'
    assert result.search_trace.seed_resolution_reasoning == '问题更像在问到货计划'
    assert result.search_trace.seed_resolution_error == ''


def test_retrieve_ontology_evidence_falls_back_to_keyword_seed_resolution(monkeypatch):
    graph = build_resolver_graph()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        lambda graph, query: IntentResolution(
            seeds=[],
            reasoning='',
            source='fallback',
            error='Invalid JSON: bad payload',
        ),
    )

    result = retrieve_ontology_evidence(graph, '泊位是什么')

    assert result.seed_node_ids == ['object_type:PoDPosition']
    assert result.search_trace.seed_resolution_source == 'fallback'
    assert result.search_trace.seed_resolution_reasoning == ''
    assert result.search_trace.seed_resolution_error == 'Invalid JSON: bad payload'


def test_retrieve_ontology_evidence_builds_localized_display_maps(monkeypatch):
    graph = build_resolver_graph()

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        lambda graph, query: IntentResolution(
            seeds=['object_type:ArrivalPlan'],
            reasoning='问题更像在问到货计划',
            source='llm',
            error='',
        ),
    )

    result = retrieve_ontology_evidence(graph, '到货计划和泊位是什么关系')

    assert result.display_name_map['object_type:ArrivalPlan'] == '到货计划(ArrivalPlan)'
    assert result.display_name_map['object_type:PoDPosition'] == '泊位(PoDPosition)'
    assert result.relation_name_map['REFERENCES'] == '[引用]'


def test_retrieve_ontology_evidence_relation_name_map_covers_current_ontology_relations():
    graph = OntologyGraph(metadata={'title': 'relations'})
    graph.add_object(
        OntologyObject(
            id='object_type:Left',
            type='ObjectType',
            name='Left',
            attributes={'chinese_description': '左实体'},
        )
    )
    graph.add_object(
        OntologyObject(
            id='object_type:Right',
            type='ObjectType',
            name='Right',
            attributes={'chinese_description': '右实体'},
        )
    )
    for relation_code in _ALL_RELATIONS:
        graph.add_relation(
            OntologyRelation(
                source_id='object_type:Left',
                target_id='object_type:Right',
                relation=relation_code,
            )
        )

    result = retrieve_ontology_evidence(graph, '左实体')

    assert result.relation_name_map == _ALL_RELATIONS
    assert all(value.startswith('[') and value.endswith(']') for value in result.relation_name_map.values())


def test_retrieve_ontology_evidence_merges_exact_entities_with_candidate_llm_selection(monkeypatch):
    graph = build_hybrid_graph()
    captured: list[tuple[str, tuple[str, ...] | None]] = []

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.parse_query',
        lambda question: ParsedQuery(
            raw_query=question,
            normalized_query='哪些里程碑会因为约束冲突影响到落位方案的执行',
            mentions=[],
            canonical_entities=['ConstraintViolation', 'PlacementPlan'],
            high_confidence_entities=['ConstraintViolation'],
            candidate_entities=['PlacementPlan'],
            intent=IntentResult(name='constraint_query', confidence=1.0, matched_rules=['约束', '冲突']),
            unmatched_terms=[],
        ),
    )

    def fake_resolve_intent(graph, query, candidate_ids=None):
        captured.append((query, tuple(candidate_ids) if candidate_ids is not None else None))
        if candidate_ids is not None:
            return IntentResolution(
                seeds=['object_type:PlacementPlan'],
                reasoning='落位方案更像在问 PlacementPlan',
                source='llm_candidate_select',
                error='',
            )
        return IntentResolution(seeds=[], reasoning='', source='fallback', error='')

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        fake_resolve_intent,
    )

    result = retrieve_ontology_evidence(graph, '哪些里程碑会因为约束冲突影响到落位方案的执行')

    assert result.seed_node_ids == ['object_type:ConstraintViolation', 'object_type:PlacementPlan']
    assert result.search_trace.seed_resolution_source == 'hybrid'
    assert result.search_trace.seed_resolution_reasoning == 'ConstraintViolation；PlacementPlan'
    assert result.search_trace.seed_resolution_error == ''
    assert captured == [('哪些里程碑会因为约束冲突影响到落位方案的执行', ('object_type:PlacementPlan',))]




def test_retrieve_ontology_evidence_uses_candidate_only_llm_selection_without_full_fallback(monkeypatch):
    graph = build_hybrid_graph()
    calls: list[tuple[str, tuple[str, ...] | None]] = []

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.parse_query',
        lambda question: ParsedQuery(
            raw_query=question,
            normalized_query='\u843d\u4f4d\u65b9\u6848\u53d7\u54ea\u4e9b\u51b2\u7a81\u5f71\u54cd',
            mentions=[],
            canonical_entities=['PlacementPlan'],
            high_confidence_entities=[],
            candidate_entities=['PlacementPlan'],
            intent=IntentResult(name='constraint_query', confidence=1.0, matched_rules=['\u51b2\u7a81']),
            unmatched_terms=[],
        ),
    )

    def fake_resolve_intent(graph, query, candidate_ids=None):
        calls.append((query, tuple(candidate_ids) if candidate_ids is not None else None))
        if candidate_ids is None:
            raise AssertionError('full fallback should not be called')
        return IntentResolution(
            seeds=['object_type:PlacementPlan'],
            reasoning='\u5019\u9009\u5b9e\u4f53\u6307\u5411 PlacementPlan',
            source='llm_candidate_select',
            error='',
        )

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        fake_resolve_intent,
    )

    result = retrieve_ontology_evidence(graph, '\u843d\u4f4d\u65b9\u6848\u53d7\u54ea\u4e9b\u51b2\u7a81\u5f71\u54cd')

    assert result.seed_node_ids == ['object_type:PlacementPlan']
    assert result.search_trace.seed_resolution_source == 'llm_candidate_select'
    assert result.search_trace.seed_resolution_reasoning == '\u5019\u9009\u5b9e\u4f53\u6307\u5411 PlacementPlan'
    assert calls == [('落位方案受哪些冲突影响', ('object_type:PlacementPlan',))]

def test_retrieve_ontology_evidence_skips_candidate_llm_when_exact_entities_are_sufficient(monkeypatch):
    graph = build_hybrid_graph()
    calls: list[tuple[str, tuple[str, ...] | None]] = []

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.parse_query',
        lambda question: ParsedQuery(
            raw_query=question,
            normalized_query='约束冲突是什么',
            mentions=[],
            canonical_entities=['ConstraintViolation'],
            high_confidence_entities=['ConstraintViolation'],
            candidate_entities=[],
            intent=IntentResult(name='definition_query', confidence=1.0, matched_rules=['是什么']),
            unmatched_terms=[],
        ),
    )

    def fake_resolve_intent(graph, query, candidate_ids=None):
        calls.append((query, tuple(candidate_ids) if candidate_ids is not None else None))
        return IntentResolution(seeds=[], reasoning='', source='fallback', error='')

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.search.ontology_query_engine.resolve_intent',
        fake_resolve_intent,
    )

    result = retrieve_ontology_evidence(graph, '约束冲突是什么')

    assert result.seed_node_ids == ['object_type:ConstraintViolation']
    assert result.search_trace.seed_resolution_source == 'alias_rule'
    assert calls == []
