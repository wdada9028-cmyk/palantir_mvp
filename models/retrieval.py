from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .ontology import OntologyObject, OntologyRelation


@dataclass(slots=True)
class QueryIntent:
    intent: str
    entities: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    focus_types: list[str] = field(default_factory=list)
    focus_relations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RetrievalHit:
    node: OntologyObject
    score: float
    hops: int
    matched_relations: list[str] = field(default_factory=list)
    evidence_quotes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'node': self.node.to_dict(),
            'score': self.score,
            'hops': self.hops,
            'matched_relations': list(self.matched_relations),
            'evidence_quotes': list(self.evidence_quotes),
        }


@dataclass(slots=True)
class RetrievalResult:
    intent: QueryIntent
    hits: list[RetrievalHit] = field(default_factory=list)
    edges: list[OntologyRelation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'intent': {
                'intent': self.intent.intent,
                'entities': list(self.intent.entities),
                'constraints': list(self.intent.constraints),
                'focus_types': list(self.intent.focus_types),
                'focus_relations': list(self.intent.focus_relations),
            },
            'hits': [item.to_dict() for item in self.hits],
            'edges': [item.to_dict() for item in self.edges],
        }


@dataclass(slots=True)
class ChunkHit:
    chunk_id: str
    semantic_score: float = 0.0
    lexical_score: float = 0.0
    fused_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'semantic_score': self.semantic_score,
            'lexical_score': self.lexical_score,
            'fused_score': self.fused_score,
        }


@dataclass(slots=True)
class ObjectHit:
    object_id: str
    score: float
    supporting_chunk_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'object_id': self.object_id,
            'score': self.score,
            'supporting_chunk_ids': list(self.supporting_chunk_ids),
        }


@dataclass(slots=True)
class Citation:
    chunk_id: str
    document_id: str
    text: str
    object_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'document_id': self.document_id,
            'text': self.text,
            'object_ids': list(self.object_ids),
        }


@dataclass(slots=True)
class RetrievalBundle:
    intent: str
    chunk_hits: list[ChunkHit] = field(default_factory=list)
    object_hits: list[ObjectHit] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    relations: list[OntologyRelation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'intent': self.intent,
            'chunk_hits': [item.to_dict() for item in self.chunk_hits],
            'object_hits': [item.to_dict() for item in self.object_hits],
            'citations': [item.to_dict() for item in self.citations],
            'relations': [item.to_dict() for item in self.relations],
        }
