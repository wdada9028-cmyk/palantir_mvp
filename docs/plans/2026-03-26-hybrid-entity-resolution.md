# Hybrid Entity Resolution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a stable hybrid entity-resolution path that uses deterministic exact/rule recall first, constrained LLM candidate selection second, and the existing full-ontology LLM fallback last.

**Architecture:** Keep the current retrieval flow intact and insert a new candidate-resolution layer between `parse_query(...)` and `resolve_intent(...)`. Exact canonical/alias hits remain authoritative, pattern/family matches become low-confidence candidates, and `resolve_intent(...)` gains an optional candidate-restricted mode so the LLM can only select from pre-recalled ontology IDs.

**Tech Stack:** Python 3.10+, dataclasses, existing query parser modules under `search/query_parser/`, existing Qwen-compatible HTTP resolver in `search/intent_resolver.py`, pytest.

---

### Task 1: Add low-confidence pattern/family entity matching

**Files:**
- Create: `search/query_parser/entity_patterns.yaml`
- Create: `search/query_parser/entity_pattern_matcher.py`
- Test: `tests/search/test_entity_pattern_matcher.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.search.query_parser.entity_pattern_matcher import EntityPatternMatcher


def test_pattern_matcher_maps_placement_plan_family_terms():
    matcher = EntityPatternMatcher.from_dict(
        {
            'PlacementPlan': {
                'root_terms': ['落位'],
                'suffix_terms': ['方案', '计划', '建议方案'],
            }
        }
    )

    mentions = matcher.match('哪些里程碑会影响落位方案执行')

    assert [(m.surface, m.canonical, m.source) for m in mentions] == [
        ('落位方案', 'PlacementPlan', 'pattern_rule')
    ]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_entity_pattern_matcher.py::test_pattern_matcher_maps_placement_plan_family_terms -q`
Expected: FAIL because module/file does not exist.

**Step 3: Write minimal implementation**

Create `search/query_parser/entity_patterns.yaml` with the first family definitions only:

```yaml
PlacementPlan:
  root_terms:
    - 落位
  suffix_terms:
    - 方案
    - 计划
    - 建议方案

ConstraintViolation:
  root_terms:
    - 约束
  suffix_terms:
    - 冲突
    - 冲突项
```

Create `search/query_parser/entity_pattern_matcher.py` with deterministic candidate generation:

```python
from __future__ import annotations

from pathlib import Path

from .models import EntityMention
from .utils import load_yaml_config

_DEFAULT_PATTERN_PATH = Path(__file__).with_name('entity_patterns.yaml')


class EntityPatternMatcher:
    def __init__(self, patterns: dict[str, dict[str, list[str]]]) -> None:
        self._patterns = patterns

    @classmethod
    def from_dict(cls, data: dict[str, dict[str, list[str]]]) -> 'EntityPatternMatcher':
        return cls(data)

    @classmethod
    def from_path(cls, path: str | Path = _DEFAULT_PATTERN_PATH) -> 'EntityPatternMatcher':
        payload = load_yaml_config(path)
        return cls.from_dict(payload)

    def match(self, text: str) -> list[EntityMention]:
        candidates: list[EntityMention] = []
        for canonical, payload in self._patterns.items():
            roots = payload.get('root_terms', [])
            suffixes = payload.get('suffix_terms', [])
            for root in roots:
                for suffix in suffixes:
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_entity_pattern_matcher.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add search/query_parser/entity_patterns.yaml search/query_parser/entity_pattern_matcher.py tests/search/test_entity_pattern_matcher.py
git commit -m "feat: add deterministic entity pattern matcher"
```

### Task 2: Extend parsed query output to separate exact hits and candidate hits

**Files:**
- Modify: `search/query_parser/models.py`
- Modify: `search/query_parser/parser.py`
- Modify: `search/query_parser/__init__.py`
- Test: `tests/search/test_query_parser.py`
- Test: `tests/search/test_query_parser_integration.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.search.query_parser import parse_query


def test_parse_query_separates_exact_entities_from_pattern_candidates():
    parsed = parse_query('哪些里程碑会因为约束冲突影响到落位方案的执行')

    assert parsed.high_confidence_entities == ['ConstraintViolation']
    assert parsed.candidate_entities == ['PlacementPlan']
    assert [(m.surface, m.source) for m in parsed.mentions] == [
        ('约束冲突', 'alias_rule'),
        ('落位方案', 'pattern_rule'),
    ]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_query_parser.py::test_parse_query_separates_exact_entities_from_pattern_candidates -q`
Expected: FAIL because `ParsedQuery` lacks these fields.

**Step 3: Write minimal implementation**

Extend `ParsedQuery` in `search/query_parser/models.py`:

```python
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
```

Update `parser.py` to:
- instantiate cached `EntityPatternMatcher`
- collect exact alias mentions first
- collect pattern mentions second
- suppress pattern mentions overlapped by exact mentions
- set:
  - `canonical_entities = merge(high_confidence_entities, candidate_entities)`
  - `high_confidence_entities = dedup(alias canonicals)`
  - `candidate_entities = dedup(pattern canonicals not already exact)`

**Step 4: Run tests to verify they pass**

Run:
- `pytest tests/search/test_query_parser.py -q`
- `pytest tests/search/test_query_parser_integration.py -q`

Expected: PASS.

**Step 5: Commit**

```bash
git add search/query_parser/models.py search/query_parser/parser.py search/query_parser/__init__.py tests/search/test_query_parser.py tests/search/test_query_parser_integration.py
git commit -m "feat: separate exact and candidate query entities"
```

### Task 3: Add constrained candidate-selection mode to the existing LLM resolver

**Files:**
- Modify: `search/intent_resolver.py`
- Test: `tests/search/test_intent_resolver.py`

**Step 1: Write the failing test**

```python
def test_resolve_intent_candidate_mode_filters_to_candidate_ids(monkeypatch):
    graph = _build_graph()
    monkeypatch.setenv('QWEN_API_BASE', 'https://example.com/v1')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {
                        'message': {
                            'content': '{"seeds": ["object_type:PoDPosition", "object_type:ArrivalPlan"], "reasoning": "更像在问泊位"}'
                        }
                    }
                ]
            }

    class FakeClient:
        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr('cloud_delivery_ontology_palantir.search.intent_resolver.get_http_client', lambda: FakeClient())

    result = resolve_intent(graph, '泊位在哪里', candidate_ids=['object_type:PoDPosition'])

    assert result.seeds == ['object_type:PoDPosition']
    assert result.source == 'llm_candidate_select'
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_intent_resolver.py::test_resolve_intent_candidate_mode_filters_to_candidate_ids -q`
Expected: FAIL because `candidate_ids` is unsupported.

**Step 3: Write minimal implementation**

Change signature to support `candidate_ids: list[str] | None = None`.

Behavior:
- `candidate_ids is None`: preserve current behavior exactly
- `candidate_ids` provided:
  - allowed object set = intersection of candidate IDs with graph object IDs
  - prompt only lists candidate objects
  - success source = `llm_candidate_select`
  - if no valid result, return `fallback` with error text

**Step 4: Run tests to verify they pass**

Run: `pytest tests/search/test_intent_resolver.py -q`
Expected: PASS with existing resolver behavior unchanged.

**Step 5: Commit**

```bash
git add search/intent_resolver.py tests/search/test_intent_resolver.py
git commit -m "feat: add constrained candidate intent resolution"
```

### Task 4: Integrate hybrid seed resolution into ontology retrieval

**Files:**
- Modify: `search/ontology_query_engine.py`
- Test: `tests/search/test_ontology_query_engine.py`

**Step 1: Write the failing tests**

Add:
- exact hit + pattern candidate => merge exact with constrained LLM selection
- exact-only hit => skip constrained LLM selection

**Step 2: Run tests to verify they fail**

Run:
- `pytest tests/search/test_ontology_query_engine.py::test_retrieve_ontology_evidence_merges_exact_entities_with_candidate_llm_selection -q`
- `pytest tests/search/test_ontology_query_engine.py::test_retrieve_ontology_evidence_skips_candidate_llm_when_exact_entities_are_sufficient -q`

Expected: FAIL because the engine still uses only alias vs full fallback behavior.

**Step 3: Write minimal implementation**

Modify seed selection logic:
- map `parsed_query.high_confidence_entities` to object IDs
- map `parsed_query.candidate_entities` to object IDs
- if high-confidence IDs exist, use them as initial seeds
- if candidate IDs exist, call `resolve_intent(..., candidate_ids=candidate_object_ids)` and merge into seeds
- only call full fallback `resolve_intent(graph, normalized_query)` when seeds are still empty
- keep relation scoring and answer formatting untouched

**Step 4: Run tests to verify they pass**

Run: `pytest tests/search/test_ontology_query_engine.py -q`
Expected: PASS with old behaviors still covered.

**Step 5: Commit**

```bash
git add search/ontology_query_engine.py tests/search/test_ontology_query_engine.py
git commit -m "feat: integrate hybrid entity seed resolution"
```

### Task 5: Add business-value aliases/patterns and regression coverage for the real query

**Files:**
- Modify: `search/query_parser/entity_aliases.yaml`
- Modify: `search/query_parser/entity_patterns.yaml`
- Test: `tests/search/test_query_parser_integration.py`

**Step 1: Write the failing test**

```python
def test_real_constraint_vs_placement_question_hits_both_entities():
    parsed = parse_query('哪些里程碑会因为约束冲突影响到落位方案的执行？')

    assert parsed.high_confidence_entities == ['ConstraintViolation']
    assert parsed.candidate_entities == ['PlacementPlan']
    assert parsed.canonical_entities == ['ConstraintViolation', 'PlacementPlan']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_query_parser_integration.py::test_real_constraint_vs_placement_question_hits_both_entities -q`
Expected: FAIL before config/rule integration is complete.

**Step 3: Write minimal implementation**

Add the immediate alias fix too:

```yaml
PlacementPlan:
  - 落位建议方案
  - 落位计划
  - 落位方案
```

Keep the pattern family so future nearby variants still hit.

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_query_parser_integration.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add search/query_parser/entity_aliases.yaml search/query_parser/entity_patterns.yaml tests/search/test_query_parser_integration.py
git commit -m "feat: cover placement plan family terms"
```

### Task 6: Final regression sweep

**Files:**
- Verify only

**Step 1: Run focused search tests**

Run:
- `pytest tests/search/test_entity_pattern_matcher.py -q`
- `pytest tests/search/test_query_parser.py tests/search/test_query_parser_integration.py -q`
- `pytest tests/search/test_intent_resolver.py tests/search/test_ontology_query_engine.py -q`

Expected: all PASS.

**Step 2: Run QA/server regression tests**

Run:
- `pytest tests/qa/test_template_answering.py tests/qa/test_generator.py -q`
- `pytest tests/server/test_ontology_http_app.py -q`

Expected: PASS; hybrid seed resolution should not affect trace formatting or answer formatting.

**Step 3: Run full suite**

Run: `pytest tests -q`
Expected: PASS.

**Step 4: Commit**

```bash
git add .
git commit -m "test: verify hybrid entity resolution regression sweep"
```

### Notes for the implementer

- Keep `merge_seed_entities(...)` stable-order and alias/exact-first.
- Do not change the answer-summary or trace formatting in this feature.
- Do not remove the current full-ontology LLM fallback; only demote it behind exact/rule/candidate-select.
- Keep candidate LLM calls narrow and optional. If exact entities already fully determine seeds, skip LLM.
- Preserve deterministic behavior in parser outputs: same query in => same mentions/entities order out.
