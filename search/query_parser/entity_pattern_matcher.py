from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import EntityMention
from .utils import load_yaml_config

_DEFAULT_PATTERN_PATH = Path(__file__).with_name('entity_patterns.yaml')


class EntityPatternMatcher:
    def __init__(self, patterns: dict[str, dict[str, list[str]]]) -> None:
        self._patterns = patterns

    @classmethod
    def from_dict(cls, data: dict[str, dict[str, list[str]]]) -> 'EntityPatternMatcher':
        if not isinstance(data, dict):
            raise ValueError('Entity patterns must be a mapping')

        normalized: dict[str, dict[str, list[str]]] = {}
        for canonical, payload in data.items():
            if not isinstance(payload, dict):
                raise ValueError(f'Entity patterns for {canonical!r} must be a mapping')

            root_terms = _as_string_list(payload.get('root_terms', []), canonical=str(canonical), field='root_terms')
            suffix_terms = _as_string_list(payload.get('suffix_terms', []), canonical=str(canonical), field='suffix_terms')
            if not root_terms or not suffix_terms:
                continue
            normalized[str(canonical)] = {
                'root_terms': root_terms,
                'suffix_terms': suffix_terms,
            }
        return cls(normalized)

    @classmethod
    def from_path(cls, path: str | Path = _DEFAULT_PATTERN_PATH) -> 'EntityPatternMatcher':
        payload = load_yaml_config(path)
        return cls.from_dict(payload)

    def match(self, text: str) -> list[EntityMention]:
        candidates: list[EntityMention] = []
        for canonical, payload in self._patterns.items():
            for root in payload['root_terms']:
                for suffix in payload['suffix_terms']:
                    phrase = f'{root}{suffix}'
                    start = text.find(phrase)
                    while start != -1:
                        candidates.append(
                            EntityMention(
                                surface=phrase,
                                canonical=canonical,
                                start=start,
                                end=start + len(phrase),
                                source='pattern_rule',
                                confidence=0.6,
                            )
                        )
                        start = text.find(phrase, start + 1)
        candidates.sort(key=lambda item: (item.start, -(item.end - item.start), item.surface, item.canonical))
        return _non_overlapping(candidates)


def _as_string_list(value: Any, *, canonical: str, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f'Entity patterns for {canonical!r} field {field!r} must be a list')
    return [str(item).strip() for item in value if str(item).strip()]


def _non_overlapping(candidates: list[EntityMention]) -> list[EntityMention]:
    occupied: list[tuple[int, int]] = []
    result: list[EntityMention] = []
    for candidate in candidates:
        if any(not (candidate.end <= start or candidate.start >= end) for start, end in occupied):
            continue
        result.append(candidate)
        occupied.append((candidate.start, candidate.end))
    return result
