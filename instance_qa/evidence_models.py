from dataclasses import asdict, dataclass, field
from typing import Any


def _as_json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _as_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_as_json_safe(item) for item in value]
    return value


@dataclass(slots=True)
class SchemaContext:
    entity_name: str
    entity_zh: str
    key_attributes: list[str] = field(default_factory=list)
    relevant_relations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _as_json_safe(asdict(self))


@dataclass(slots=True)
class InstanceEvidence:
    entity: str
    iid: str
    business_keys: dict[str, Any] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)
    schema_context: SchemaContext | None = None
    paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = _as_json_safe(asdict(self))
        if self.schema_context is not None:
            payload['schema_context'] = self.schema_context.to_dict()
        return payload


@dataclass(slots=True)
class EvidenceEdge:
    source_entity: str
    source_id: str
    relation: str
    target_entity: str
    target_id: str

    def to_dict(self) -> dict[str, Any]:
        return _as_json_safe(asdict(self))


@dataclass(slots=True)
class EntityEvidenceGroup:
    entity: str
    instances: list[InstanceEvidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'entity': self.entity,
            'instances': [item.to_dict() for item in self.instances],
        }


@dataclass(slots=True)
class EmptyEntityEvidence:
    entity: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return _as_json_safe(asdict(self))


@dataclass(slots=True)
class UnrelatedEntityEvidence:
    entity: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return _as_json_safe(asdict(self))


@dataclass(slots=True)
class OmittedEntityEvidence:
    entity: str
    omitted_count: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return _as_json_safe(asdict(self))


@dataclass(slots=True)
class EvidenceBundle:
    question: str
    understanding: dict[str, Any] = field(default_factory=dict)
    positive_evidence: list[EntityEvidenceGroup] = field(default_factory=list)
    edges: list[EvidenceEdge] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)
    empty_entities: list[EmptyEntityEvidence] = field(default_factory=list)
    unrelated_entities: list[UnrelatedEntityEvidence] = field(default_factory=list)
    omitted_entities: list[OmittedEntityEvidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'question': self.question,
            'understanding': _as_json_safe(self.understanding),
            'positive_evidence': [group.to_dict() for group in self.positive_evidence],
            'edges': [edge.to_dict() for edge in self.edges],
            'paths': _as_json_safe(self.paths),
            'empty_entities': [item.to_dict() for item in self.empty_entities],
            'unrelated_entities': [item.to_dict() for item in self.unrelated_entities],
            'omitted_entities': [item.to_dict() for item in self.omitted_entities],
        }
