from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation
from cloud_delivery_ontology_palantir.search.intent_resolver import IntentResolution
from cloud_delivery_ontology_palantir.search.ontology_query_engine import retrieve_ontology_evidence


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
    assert result.relation_name_map['REFERENCES'] == '引用'
