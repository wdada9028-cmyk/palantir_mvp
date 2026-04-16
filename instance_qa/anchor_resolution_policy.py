from __future__ import annotations

from dataclasses import dataclass

from .anchor_candidate_ranker import AnchorRankDecision
from .anchor_candidate_resolver import AnchorResolutionResult

_HIGH_CONFIDENCE_THRESHOLD = 0.80
_MEDIUM_CONFIDENCE_THRESHOLD = 0.60
_MAX_CANDIDATES = 5


@dataclass(frozen=True, slots=True)
class _CandidateTriplet:
    entity: str
    attribute: str
    value: str


def apply_anchor_resolution_policy(
    *,
    deterministic_result: AnchorResolutionResult | None,
    candidate_context: dict[str, object] | None,
    rank_decision: AnchorRankDecision | None,
) -> dict[str, object] | None:
    candidates = _collect_candidates(candidate_context, deterministic_result)
    if not candidates and deterministic_result is None and rank_decision is None:
        return None

    raw_anchor_text = _resolve_raw_anchor_text(candidate_context, deterministic_result)
    match_stage = _resolve_match_stage(deterministic_result, candidate_context)

    if rank_decision is None:
        if deterministic_result is not None and deterministic_result.selected is not None and deterministic_result.match_stage in {'exact', 'light'}:
            return _build_payload(
                raw_anchor_text=raw_anchor_text,
                match_stage=match_stage,
                selection={
                    'decision': 'select',
                    'confidence': 1.0,
                    'confidence_tier': 'high',
                    'reason': 'Deterministic exact/light match with unique selected anchor.',
                    'source': 'deterministic_short_circuit',
                },
                selected=_candidate_from_deterministic(deterministic_result),
                candidates=candidates,
            )

        fallback_selected = _candidate_from_deterministic(deterministic_result)
        fallback_decision = 'select' if fallback_selected is not None else 'ambiguous'
        fallback_confidence = 0.80 if fallback_selected is not None else 0.0
        return _build_payload(
            raw_anchor_text=raw_anchor_text,
            match_stage=match_stage,
            selection={
                'decision': fallback_decision,
                'confidence': fallback_confidence,
                'confidence_tier': _confidence_tier(fallback_confidence),
                'reason': 'Ranker unavailable; fallback to deterministic result.',
                'source': 'deterministic_fallback',
            },
            selected=fallback_selected,
            candidates=candidates,
        )

    tier = _confidence_tier(rank_decision.confidence)
    selection_decision = rank_decision.decision
    selected = None

    if rank_decision.decision == 'select':
        if tier == 'low':
            selection_decision = 'ambiguous'
        else:
            selected = _candidate_from_ranker_id(candidate_context, rank_decision.selected_candidate_id)
            if selected is None:
                selection_decision = 'ambiguous'

    return _build_payload(
        raw_anchor_text=raw_anchor_text,
        match_stage=match_stage,
        selection={
            'decision': selection_decision,
            'confidence': rank_decision.confidence,
            'confidence_tier': tier,
            'reason': rank_decision.reason,
            'source': 'ranker',
        },
        selected=selected,
        candidates=candidates,
    )


def _build_payload(
    *,
    raw_anchor_text: str,
    match_stage: str,
    selection: dict[str, object],
    selected: dict[str, str] | None,
    candidates: list[dict[str, str]],
) -> dict[str, object]:
    return {
        'raw_anchor_text': raw_anchor_text,
        'match_stage': match_stage,
        'selection': selection,
        'selected': selected,
        'candidates': candidates,
    }


def _resolve_raw_anchor_text(candidate_context: dict[str, object] | None, deterministic_result: AnchorResolutionResult | None) -> str:
    if isinstance(candidate_context, dict):
        value = str(candidate_context.get('raw_anchor_text') or '').strip()
        if value:
            return value
    if deterministic_result is not None:
        return str(deterministic_result.raw_anchor_text or '').strip()
    return ''


def _resolve_match_stage(deterministic_result: AnchorResolutionResult | None, candidate_context: dict[str, object] | None) -> str:
    if deterministic_result is not None:
        value = str(deterministic_result.match_stage or '').strip()
        if value:
            return value

    if not isinstance(candidate_context, dict):
        return ''
    candidates = candidate_context.get('candidates')
    if not isinstance(candidates, list):
        return ''
    for item in candidates:
        if not isinstance(item, dict):
            continue
        locator = item.get('locator')
        if not isinstance(locator, dict):
            continue
        value = str(locator.get('match_stage') or '').strip()
        if value:
            return value
    return ''


def _collect_candidates(
    candidate_context: dict[str, object] | None,
    deterministic_result: AnchorResolutionResult | None,
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    if isinstance(candidate_context, dict):
        items = candidate_context.get('candidates')
        if isinstance(items, list):
            for item in items:
                parsed = _candidate_from_context_item(item)
                if parsed is None:
                    continue
                key = (parsed.entity, parsed.attribute, parsed.value)
                if key in seen:
                    continue
                seen.add(key)
                result.append({'entity': parsed.entity, 'attribute': parsed.attribute, 'value': parsed.value})
                if len(result) >= _MAX_CANDIDATES:
                    return result

    if deterministic_result is not None:
        for candidate in deterministic_result.candidates:
            entity = str(candidate.entity or '').strip()
            attribute = str(candidate.attribute or '').strip()
            value = str(candidate.value or '').strip()
            if not entity or not attribute or not value:
                continue
            key = (entity, attribute, value)
            if key in seen:
                continue
            seen.add(key)
            result.append({'entity': entity, 'attribute': attribute, 'value': value})
            if len(result) >= _MAX_CANDIDATES:
                break

    return result


def _candidate_from_context_item(item: object) -> _CandidateTriplet | None:
    if not isinstance(item, dict):
        return None
    entity = str(item.get('entity') or '').strip()
    locator = item.get('locator')
    if not entity or not isinstance(locator, dict):
        return None
    attribute = str(locator.get('matched_attribute') or '').strip()
    value = str(locator.get('matched_value') or '').strip()
    if not attribute or not value:
        return None
    return _CandidateTriplet(entity=entity, attribute=attribute, value=value)


def _candidate_from_deterministic(deterministic_result: AnchorResolutionResult | None) -> dict[str, str] | None:
    if deterministic_result is None or deterministic_result.selected is None:
        return None
    selected = deterministic_result.selected
    entity = str(selected.entity or '').strip()
    attribute = str(selected.attribute or '').strip()
    value = str(selected.value or '').strip()
    if not entity or not attribute or not value:
        return None
    return {'entity': entity, 'attribute': attribute, 'value': value}


def _candidate_from_ranker_id(candidate_context: dict[str, object] | None, candidate_id: str) -> dict[str, str] | None:
    if not isinstance(candidate_context, dict):
        return None
    candidates = candidate_context.get('candidates')
    if not isinstance(candidates, list):
        return None

    target = str(candidate_id or '').strip()
    if not target:
        return None

    for item in candidates:
        if not isinstance(item, dict):
            continue
        if str(item.get('candidate_id') or '').strip() != target:
            continue
        parsed = _candidate_from_context_item(item)
        if parsed is None:
            return None
        return {'entity': parsed.entity, 'attribute': parsed.attribute, 'value': parsed.value}

    return None


def _confidence_tier(confidence: float) -> str:
    if confidence >= _HIGH_CONFIDENCE_THRESHOLD:
        return 'high'
    if confidence >= _MEDIUM_CONFIDENCE_THRESHOLD:
        return 'medium'
    return 'low'
