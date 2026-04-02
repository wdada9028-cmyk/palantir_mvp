from cloud_delivery_ontology_palantir.instance_qa.question_models import AnchorRef, ConstraintRef, DurationRef, GoalRef, IdentifierRef, QuestionDSL, ScenarioRef
from cloud_delivery_ontology_palantir.instance_qa.question_validator import validate_question_dsl
from cloud_delivery_ontology_palantir.instance_qa.schema_registry import SchemaEntity, SchemaRegistry


def _schema_registry() -> SchemaRegistry:
    return SchemaRegistry(
        entities={
            "Room": SchemaEntity(name="Room", object_id="object_type:Room", attributes=["room_id", "room_status"], key_attributes=["room_id"]),
            "PoD": SchemaEntity(name="PoD", object_id="object_type:PoD", attributes=["pod_id", "pod_status"], key_attributes=["pod_id"]),
        },
        relations=[],
        adjacency={"Room": [], "PoD": []},
    )


def test_validate_question_dsl_rejects_unknown_anchor_entity():
    question = QuestionDSL(
        mode="impact_analysis",
        anchor=AnchorRef(entity="UnknownRoom", identifier=IdentifierRef(attribute="room_id", value="01"), surface="01??"),
        scenario=ScenarioRef(event_type="power_outage", duration=DurationRef(value=7, unit="day"), start_time=None, severity=None, raw_event="??"),
        goal=GoalRef(type="list_impacts", target_entity=None, target_metric=None, deadline=None),
        constraints=ConstraintRef(statuses=[], time_window=None, limit=20),
    )

    error = validate_question_dsl(question, _schema_registry())

    assert "UnknownRoom" in error


def test_validate_question_dsl_accepts_known_entity_and_identifier_attribute():
    question = QuestionDSL(
        mode="impact_analysis",
        anchor=AnchorRef(entity="Room", identifier=IdentifierRef(attribute="room_id", value="01"), surface="01??"),
        scenario=ScenarioRef(event_type="power_outage", duration=DurationRef(value=7, unit="day"), start_time=None, severity=None, raw_event="??"),
        goal=GoalRef(type="list_impacts", target_entity="PoD", target_metric=None, deadline=None),
        constraints=ConstraintRef(statuses=[], time_window=None, limit=20),
    )

    assert validate_question_dsl(question, _schema_registry()) is None
