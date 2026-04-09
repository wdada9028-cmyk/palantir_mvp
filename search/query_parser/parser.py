from __future__ import annotations

import logging
import re
from functools import lru_cache

from .alias_registry import AliasRegistry
from .entity_pattern_matcher import EntityPatternMatcher
from .intent_classifier import IntentClassifier
from .models import EntityMention, ParsedQuery
from .surface_normalizer import normalize_query

logger = logging.getLogger(__name__)
_TOKEN_RE = re.compile(r'[A-Za-z0-9_]+|[一-鿿]+')

@lru_cache(maxsize=1)
def _default_alias_registry() -> AliasRegistry:
    return AliasRegistry.from_path()

@lru_cache(maxsize=1)
def _default_entity_pattern_matcher() -> EntityPatternMatcher:
    return EntityPatternMatcher.from_path()

@lru_cache(maxsize=1)
def _default_intent_classifier() -> IntentClassifier:
    return IntentClassifier.from_path()

def parse_query(
    raw_query: str,
    *,
    alias_registry: AliasRegistry | None = None,
    entity_pattern_matcher: EntityPatternMatcher | None = None,
    intent_classifier: IntentClassifier | None = None,
) -> ParsedQuery:
    normalized_query = normalize_query(raw_query)
    alias_registry = alias_registry or _default_alias_registry()
    entity_pattern_matcher = entity_pattern_matcher or _default_entity_pattern_matcher()
    intent_classifier = intent_classifier or _default_intent_classifier()

    exact_mentions = alias_registry.match(normalized_query)
    pattern_mentions = entity_pattern_matcher.match(normalized_query)
    pattern_mentions = _drop_pattern_mentions_overlapping_exact(pattern_mentions, exact_mentions)
    mentions = _merge_mentions(exact_mentions, pattern_mentions)

    high_confidence_entities = _stable_dedup([item.canonical for item in exact_mentions])
    candidate_entities = _stable_dedup([
        item.canonical
        for item in pattern_mentions
        if item.canonical not in high_confidence_entities
    ])
    canonical_entities = _stable_dedup([*high_confidence_entities, *candidate_entities])

    intent = intent_classifier.classify(normalized_query)
    unmatched_terms = _extract_unmatched_terms(normalized_query, mentions)
    parsed = ParsedQuery(
        raw_query=raw_query,
        normalized_query=normalized_query,
        mentions=mentions,
        canonical_entities=canonical_entities,
        high_confidence_entities=high_confidence_entities,
        candidate_entities=candidate_entities,
        intent=intent,
        unmatched_terms=unmatched_terms,
    )
    logger.debug(
        'query.parsed',
        extra={
            'raw_query': raw_query,
            'normalized_query': normalized_query,
            'canonical_entities': canonical_entities,
            'high_confidence_entities': high_confidence_entities,
            'candidate_entities': candidate_entities,
            'intent': intent.name,
            'unmatched_terms': unmatched_terms,
        },
    )
    return parsed

def _drop_pattern_mentions_overlapping_exact(
    pattern_mentions: list[EntityMention],
    exact_mentions: list[EntityMention],
) -> list[EntityMention]:
    exact_spans = [(item.start, item.end) for item in exact_mentions]
    result: list[EntityMention] = []
    for mention in pattern_mentions:
        if any(_spans_overlap(mention.start, mention.end, start, end) for start, end in exact_spans):
            continue
        result.append(mention)
    return result

def _merge_mentions(
    exact_mentions: list[EntityMention],
    pattern_mentions: list[EntityMention],
) -> list[EntityMention]:
    source_rank = {
        'alias_rule': 0,
        'pattern_rule': 1,
    }
    merged = [*exact_mentions, *pattern_mentions]
    merged.sort(
        key=lambda item: (
            item.start,
            -(item.end - item.start),
            source_rank.get(item.source, 99),
            item.surface,
            item.canonical,
        )
    )
    return merged

def _spans_overlap(left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
    return not (left_end <= right_start or left_start >= right_end)

def _extract_unmatched_terms(normalized_query: str, mentions: list[EntityMention]) -> list[str]:
    covered = [False] * len(normalized_query)
    for mention in mentions:
        for index in range(mention.start, mention.end):
            if 0 <= index < len(covered):
                covered[index] = True
    unmatched: list[str] = []
    for match in _TOKEN_RE.finditer(normalized_query):
        if all(covered[index] for index in range(match.start(), match.end())):
            continue
        unmatched.append(match.group(0))
    return _stable_dedup(unmatched)

def _stable_dedup(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
