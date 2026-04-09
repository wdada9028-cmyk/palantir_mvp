from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

from .models import EntityMention
from .utils import load_yaml_config

logger = logging.getLogger(__name__)
_DEFAULT_ALIAS_PATH = Path(__file__).with_name('entity_aliases.yaml')


class AliasRegistry:
    def __init__(self, canonical_to_aliases: dict[str, list[str]]) -> None:
        self._canonical_to_aliases = {
            canonical: [alias for alias in aliases if alias]
            for canonical, aliases in canonical_to_aliases.items()
            if aliases
        }
        self._alias_entries = sorted(
            [
                (alias, canonical)
                for canonical, aliases in self._canonical_to_aliases.items()
                for alias in aliases
            ],
            key=lambda item: (-len(item[0]), item[0], item[1]),
        )

    @classmethod
    def from_dict(cls, data: dict[str, list[str]]) -> 'AliasRegistry':
        return cls({str(key): [str(item) for item in value] for key, value in data.items()})

    @classmethod
    def from_path(cls, path: str | Path = _DEFAULT_ALIAS_PATH) -> 'AliasRegistry':
        payload = load_yaml_config(path)
        normalized: dict[str, list[str]] = {}
        for canonical, aliases in payload.items():
            if not isinstance(aliases, list):
                raise ValueError(f'Alias config for {canonical!r} must be a list')
            normalized[str(canonical)] = [str(item) for item in aliases]
        return cls.from_dict(normalized)

    def match(self, text: str) -> list[EntityMention]:
        candidates: list[EntityMention] = []
        for alias, canonical in self._alias_entries:
            start = text.find(alias)
            while start != -1:
                candidates.append(
                    EntityMention(
                        surface=alias,
                        canonical=canonical,
                        start=start,
                        end=start + len(alias),
                        source='alias_rule',
                    )
                )
                start = text.find(alias, start + 1)
        candidates.sort(key=lambda item: (item.start, -(item.end - item.start), item.surface, item.canonical))
        matches: list[EntityMention] = []
        occupied: list[tuple[int, int]] = []
        for candidate in candidates:
            if any(not (candidate.end <= start or candidate.start >= end) for start, end in occupied):
                continue
            matches.append(candidate)
            occupied.append((candidate.start, candidate.end))
        logger.debug('alias.match', extra={'text': text, 'matches': [asdict(item) for item in matches]})
        return matches
