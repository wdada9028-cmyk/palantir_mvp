from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .documents import ChunkObjectLink, DocumentChunk, SourceDocument
from .ontology import OntologyGraph
from .schedule import ScheduleResult


@dataclass(slots=True)
class ProjectArtifacts:
    documents: list[SourceDocument] = field(default_factory=list)
    chunks: list[DocumentChunk] = field(default_factory=list)
    chunk_links: list[ChunkObjectLink] = field(default_factory=list)
    ontology: OntologyGraph = field(default_factory=OntologyGraph)
    schedule: ScheduleResult | None = None
    vector_index: Any = None
    embedding_client: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'documents': [item.to_dict() for item in self.documents],
            'chunks': [item.to_dict() for item in self.chunks],
            'chunk_links': [item.to_dict() for item in self.chunk_links],
            'ontology': self.ontology.to_dict(),
            'schedule': None if self.schedule is None else self.schedule.to_dict(),
            'metadata': dict(self.metadata),
        }
