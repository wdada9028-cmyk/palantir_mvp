from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation
from cloud_delivery_ontology_palantir.search.ontology_query_engine import retrieve_ontology_evidence


def test_retrieve_ontology_evidence_returns_animation_steps_and_chain():
    graph = OntologyGraph(metadata={"title": "??"})
    graph.add_object(
        OntologyObject(
            id="object_type:PoD",
            type="ObjectType",
            name="PoD",
            attributes={
                "group": "4.3 ??????",
                "chinese_description": "?????",
                "key_properties": [{"name": "pod_id", "description": "PoD ID"}],
            },
        )
    )
    graph.add_object(
        OntologyObject(
            id="object_type:ArrivalPlan",
            type="ObjectType",
            name="ArrivalPlan",
            attributes={"group": "4.6 ??????", "chinese_description": "????"},
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id="object_type:ArrivalPlan",
            target_id="object_type:PoD",
            relation="APPLIES_TO",
            attributes={"description": "???????PoD"},
        )
    )

    result = retrieve_ontology_evidence(graph, "PoD ???????")

    assert result.seed_node_ids == ["object_type:PoD"]
    assert result.highlight_steps
    assert result.evidence_chain
    assert any(step.action == "anchor_node" for step in result.highlight_steps)
    assert any(item.kind == "relation" for item in result.evidence_chain)


def test_retrieve_ontology_evidence_keeps_legacy_step_payload_shape():
    graph = OntologyGraph(metadata={"title": "??"})
    graph.add_object(
        OntologyObject(
            id="object_type:PoD",
            type="ObjectType",
            name="PoD",
            attributes={"group": "4.3 ??????", "chinese_description": "?????"},
        )
    )
    graph.add_object(
        OntologyObject(
            id="object_type:ArrivalPlan",
            type="ObjectType",
            name="ArrivalPlan",
            attributes={"group": "4.6 ??????", "chinese_description": "????"},
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id="object_type:ArrivalPlan",
            target_id="object_type:PoD",
            relation="APPLIES_TO",
            attributes={"description": "???????PoD"},
        )
    )

    result = retrieve_ontology_evidence(graph, "PoD ?????")
    step = result.highlight_steps[0]
    payload = step.to_dict()

    assert set(payload) == {"action", "message", "node_ids", "edge_ids", "evidence_ids"}
    assert not hasattr(step, "step_title")
    assert not hasattr(step, "new_node_ids")
    assert not hasattr(step, "focus_node_ids")
