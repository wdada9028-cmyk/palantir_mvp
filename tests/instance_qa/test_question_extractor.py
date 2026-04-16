from cloud_delivery_ontology_palantir.instance_qa.question_extractor import build_question_extraction_prompt, parse_question_dsl_payload
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaAdjacency, SchemaEntity, SchemaRegistry


def test_parse_question_dsl_payload_normalizes_room_power_outage_question():
    payload = {
        "mode": "impact_analysis",
        "anchor": {
            "entity": "Room",
            "identifier": {"attribute": "room_id", "value": "01"},
            "surface": "01??",
        },
        "scenario": {
            "event_type": "power_outage",
            "duration": {"value": 7, "unit": "day"},
            "start_time": None,
            "severity": None,
            "raw_event": "??",
        },
        "goal": {
            "type": "list_impacts",
            "target_entity": None,
            "target_metric": None,
            "deadline": None,
        },
        "constraints": {"statuses": [], "time_window": None, "limit": 20},
    }

    question = parse_question_dsl_payload(payload)

    assert question.mode == "impact_analysis"
    assert question.anchor.entity == "Room"
    assert question.anchor.identifier.attribute == "room_id"
    assert question.anchor.identifier.value == "01"
    assert question.scenario.event_type == "power_outage"
    assert question.scenario.duration.value == 7
    assert question.constraints.limit == 20


def test_build_question_extraction_prompt_lists_allowed_schema_entities_and_events():
    registry = SchemaRegistry(
        entities={
            "Room": SchemaEntity(name="Room", object_id="object_type:Room", attributes=["room_id"], key_attributes=["room_id"]),
            "PoD": SchemaEntity(name="PoD", object_id="object_type:PoD", attributes=["pod_id"], key_attributes=["pod_id"]),
        },
        relations=[],
        adjacency={
            "Room": [SchemaAdjacency(entity="Room", relation="OCCURS_IN", direction="in", neighbor_entity="WorkAssignment")],
            "PoD": [],
        },
    )

    prompt = build_question_extraction_prompt(registry, "01??????????????")

    assert "Room" in prompt
    assert "PoD" in prompt
    assert "power_outage" in prompt
    assert "generic_incident" in prompt
    assert "01??????????????" in prompt
