from __future__ import annotations

from dataclasses import dataclass

from .anchor_locator_registry import AnchorLocatorConfig
from .anchor_normalizer import normalize_anchor_text_light, normalize_anchor_text_loose


@dataclass(frozen=True, slots=True)
class AnchorCandidate:
    entity: str
    attribute: str
    value: str
    source_row: dict[str, object]


@dataclass(frozen=True, slots=True)
class AnchorResolutionResult:
    raw_anchor_text: str
    match_stage: str
    selected: AnchorCandidate | None
    candidates: list[AnchorCandidate]


def resolve_anchor_candidates(
    *,
    raw_anchor_text: str,
    locator_registry: dict[str, AnchorLocatorConfig],
    candidate_rows_by_entity: dict[str, list[dict[str, object]]],
) -> AnchorResolutionResult:
    raw_value = str(raw_anchor_text or '').strip()
    exact_candidates = _collect_candidates(raw_value, locator_registry, candidate_rows_by_entity, stage='exact')
    if len(exact_candidates) == 1:
        return AnchorResolutionResult(raw_anchor_text=raw_value, match_stage='exact', selected=exact_candidates[0], candidates=exact_candidates)
    if exact_candidates:
        return AnchorResolutionResult(raw_anchor_text=raw_value, match_stage='exact', selected=None, candidates=exact_candidates)

    light_candidates = _collect_candidates(raw_value, locator_registry, candidate_rows_by_entity, stage='light')
    if len(light_candidates) == 1:
        return AnchorResolutionResult(raw_anchor_text=raw_value, match_stage='light', selected=light_candidates[0], candidates=light_candidates)
    if light_candidates:
        return AnchorResolutionResult(raw_anchor_text=raw_value, match_stage='light', selected=None, candidates=light_candidates)

    loose_candidates = _collect_candidates(raw_value, locator_registry, candidate_rows_by_entity, stage='loose')
    if loose_candidates:
        return AnchorResolutionResult(raw_anchor_text=raw_value, match_stage='loose', selected=None, candidates=loose_candidates)

    return AnchorResolutionResult(raw_anchor_text=raw_value, match_stage='none', selected=None, candidates=[])


def _collect_candidates(
    raw_anchor_text: str,
    locator_registry: dict[str, AnchorLocatorConfig],
    candidate_rows_by_entity: dict[str, list[dict[str, object]]],
    *,
    stage: str,
) -> list[AnchorCandidate]:
    normalized_query_light = normalize_anchor_text_light(raw_anchor_text)
    normalized_query_loose = normalize_anchor_text_loose(raw_anchor_text)
    result: list[AnchorCandidate] = []
    seen: set[tuple[str, str, str]] = set()

    for entity_name, config in locator_registry.items():
        for row in candidate_rows_by_entity.get(entity_name, []):
            if not isinstance(row, dict):
                continue
            for attribute in config.lookup_attributes:
                value = str(row.get(attribute) or '').strip()
                if not value:
                    continue
                if stage == 'exact':
                    matched = raw_anchor_text == value
                elif stage == 'light':
                    matched = normalized_query_light and normalize_anchor_text_light(value) == normalized_query_light
                else:
                    matched = normalized_query_loose and normalize_anchor_text_loose(value) == normalized_query_loose
                if not matched:
                    continue
                key = (entity_name, attribute, value)
                if key in seen:
                    continue
                seen.add(key)
                result.append(AnchorCandidate(entity=entity_name, attribute=attribute, value=value, source_row=row))
    return result
