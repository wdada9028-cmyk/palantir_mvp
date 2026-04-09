from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .models import IntentResult
from .utils import load_yaml_config

logger = logging.getLogger(__name__)
_DEFAULT_RULE_PATH = Path(__file__).with_name('intent_rules.yaml')


class IntentClassifier:
    def __init__(self, rules: dict[str, dict[str, Any]]) -> None:
        self._rules = rules
        self._ordered_names = sorted(
            rules,
            key=lambda name: (-int(rules[name].get('priority', 0)), name),
        )

    @classmethod
    def from_dict(cls, rules: dict[str, dict[str, Any]]) -> 'IntentClassifier':
        normalized: dict[str, dict[str, Any]] = {}
        for name, payload in rules.items():
            normalized[str(name)] = {
                'priority': int(payload.get('priority', 0)),
                'keywords': [str(item) for item in payload.get('keywords', [])],
            }
        return cls(normalized)

    @classmethod
    def from_path(cls, path: str | Path = _DEFAULT_RULE_PATH) -> 'IntentClassifier':
        payload = load_yaml_config(path)
        if not isinstance(payload, dict):
            raise ValueError('Intent rules must be a mapping')
        return cls.from_dict(payload)

    def classify(self, text: str) -> IntentResult:
        best_name = 'listing_query'
        best_score = float('-inf')
        best_matches: list[str] = []
        for name in self._ordered_names:
            rule = self._rules[name]
            matched = [keyword for keyword in rule.get('keywords', []) if keyword and keyword in text]
            score = len(matched) * 1000 + int(rule.get('priority', 0))
            if matched and score > best_score:
                best_name = name
                best_score = score
                best_matches = matched
        if best_score == float('-inf'):
            fallback = 'listing_query' if 'listing_query' in self._rules else 'unknown'
            result = IntentResult(name=fallback, confidence=0.0, matched_rules=[])
            logger.debug('intent.classify', extra={'text': text, 'intent': result.name, 'matched_rules': []})
            return result
        confidence = min(1.0, 0.5 + 0.1 * len(best_matches))
        result = IntentResult(name=best_name, confidence=confidence, matched_rules=best_matches)
        logger.debug('intent.classify', extra={'text': text, 'intent': result.name, 'matched_rules': result.matched_rules})
        return result
