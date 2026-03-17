from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceDocument:
    id: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'metadata': dict(self.metadata),
        }


@dataclass(slots=True)
class DocumentChunk:
    id: str
    document_id: str
    ordinal: int
    text: str
    start_offset: int
    end_offset: int
    embedding: list[float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'document_id': self.document_id,
            'ordinal': self.ordinal,
            'text': self.text,
            'start_offset': self.start_offset,
            'end_offset': self.end_offset,
            'embedding': list(self.embedding) if self.embedding is not None else None,
            'metadata': dict(self.metadata),
        }


@dataclass(slots=True)
class ChunkObjectLink:
    chunk_id: str
    object_id: str
    link_type: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'object_id': self.object_id,
            'link_type': self.link_type,
            'score': self.score,
            'metadata': dict(self.metadata),
        }
