from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EntityMention:
    surface: str
    canonical: str
    start: int
    end: int
    source: str
    confidence: float = 1.0


@dataclass(slots=True)
class IntentResult:
    name: str
    confidence: float
    matched_rules: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedQuery:
    raw_query: str
    normalized_query: str
    mentions: list[EntityMention] = field(default_factory=list)
    canonical_entities: list[str] = field(default_factory=list)
    high_confidence_entities: list[str] = field(default_factory=list)
    candidate_entities: list[str] = field(default_factory=list)
    intent: IntentResult = field(default_factory=lambda: IntentResult(name='listing_query', confidence=0.0, matched_rules=[]))
    unmatched_terms: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RetrievalPlan:
    seed_entities: list[str] = field(default_factory=list)
    allowed_relations: list[str] | None = None
    blocked_relations: list[str] | None = None
    max_hop: int = 2
    answer_style: str = 'entity_list'
    ranking_policy: str = 'seed_first'
    debug_reason: list[str] = field(default_factory=list)
