from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class RetrievalStep:
    action: str
    message: str
    node_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceItem:
    evidence_id: str
    kind: str
    label: str
    message: str
    node_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    why_matched: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class TraceExpansionStep:
    step: int
    from_node_id: str
    edge_id: str
    to_node_id: str
    relation: str
    reason: str = ''
    snapshot_node_ids: list[str] = field(default_factory=list)
    snapshot_edge_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class SearchTrace:
    seed_node_ids: list[str] = field(default_factory=list)
    seed_resolution_source: str = ''
    seed_resolution_reasoning: str = ''
    seed_resolution_error: str = ''
    expansion_steps: list[TraceExpansionStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            'seed_node_ids': list(self.seed_node_ids),
            'seed_resolution_source': self.seed_resolution_source,
            'seed_resolution_reasoning': self.seed_resolution_reasoning,
            'seed_resolution_error': self.seed_resolution_error,
            'expansion_steps': [item.to_dict() for item in self.expansion_steps],
        }


@dataclass(slots=True)
class OntologyEvidenceBundle:
    question: str
    seed_node_ids: list[str]
    matched_node_ids: list[str]
    matched_edge_ids: list[str]
    highlight_steps: list[RetrievalStep]
    evidence_chain: list[EvidenceItem]
    insufficient_evidence: bool
    search_trace: SearchTrace = field(default_factory=SearchTrace)
    display_name_map: dict[str, str] = field(default_factory=dict)
    relation_name_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            'question': self.question,
            'seed_node_ids': list(self.seed_node_ids),
            'matched_node_ids': list(self.matched_node_ids),
            'matched_edge_ids': list(self.matched_edge_ids),
            'highlight_steps': [item.to_dict() for item in self.highlight_steps],
            'evidence_chain': [item.to_dict() for item in self.evidence_chain],
            'insufficient_evidence': self.insufficient_evidence,
            'search_trace': self.search_trace.to_dict(),
            'display_name_map': dict(self.display_name_map),
            'relation_name_map': dict(self.relation_name_map),
        }
