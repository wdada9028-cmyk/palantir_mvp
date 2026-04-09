# Lightweight Query Parser Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a lightweight alias + intent parsing layer that stabilizes seed selection and relation ranking without rewriting the existing retrieval pipeline.

**Architecture:** New deterministic query-parser helpers live under `search/query_parser/` and plug into `search/ontology_query_engine.py` as a thin pre-processing layer. Alias hits become preferred seeds, intent becomes a relation-ranking bias, and the existing graph expansion / evidence / answer pipeline remains intact.

**Tech Stack:** Python 3.11, dataclasses, pathlib, logging, regex, PyYAML, pytest

---

### Task 1: Add parser models and configuration skeleton

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/__init__.py`
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/models.py`
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/entity_aliases.yaml`
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/intent_rules.yaml`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_query_parser.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.search.query_parser.models import EntityMention, IntentResult, ParsedQuery, RetrievalPlan


def test_query_parser_models_construct_expected_shapes():
    mention = EntityMention(surface='??', canonical='Room', start=0, end=2, source='alias_rule')
    intent = IntentResult(name='relation_query', confidence=1.0, matched_rules=['??'])
    parsed = ParsedQuery(
        raw_query='????????',
        normalized_query='???????',
        mentions=[mention],
        canonical_entities=['Room'],
        intent=intent,
        unmatched_terms=['?????'],
    )
    plan = RetrievalPlan(
        seed_entities=['Room'],
        allowed_relations=['HAS'],
        blocked_relations=None,
        max_hop=2,
        answer_style='triple_list',
        ranking_policy='relation_first',
        debug_reason=['intent=relation_query'],
    )

    assert parsed.canonical_entities == ['Room']
    assert plan.seed_entities == ['Room']
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_query_parser.py::test_query_parser_models_construct_expected_shapes -v`
Expected: FAIL with import or module-not-found error.

**Step 3: Write minimal implementation**

Create the dataclasses in `search/query_parser/models.py`, export them from `__init__.py`, and add initial YAML files containing the agreed high-confidence alias and intent-rule seeds.

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_query_parser.py::test_query_parser_models_construct_expected_shapes -v`
Expected: PASS

**Step 5: Commit**

```bash
git add search/query_parser/__init__.py search/query_parser/models.py search/query_parser/entity_aliases.yaml search/query_parser/intent_rules.yaml tests/search/test_query_parser.py
git commit -m "feat: add query parser models and config"
```

### Task 2: Extract shared surface normalizer

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/surface_normalizer.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/ontology_query_engine.py`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_surface_normalizer.py`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_ontology_query_engine.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.search.query_parser.surface_normalizer import normalize_query


def test_normalize_query_removes_terminal_punctuation_and_collapses_spaces():
    assert normalize_query('  PoD   ???????  ') == 'PoD ?????'
```

Also add or adapt a retrieval-engine regression test so the engine imports and uses the shared normalizer rather than a private duplicate.

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_surface_normalizer.py -v`
Expected: FAIL with module-not-found error.

**Step 3: Write minimal implementation**

Move the current normalization logic into `search/query_parser/surface_normalizer.py` and update `search/ontology_query_engine.py` to import it.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/search/test_surface_normalizer.py tests/search/test_ontology_query_engine.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add search/query_parser/surface_normalizer.py search/ontology_query_engine.py tests/search/test_surface_normalizer.py tests/search/test_ontology_query_engine.py
git commit -m "refactor: share query surface normalization"
```

### Task 3: Implement deterministic alias registry

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/alias_registry.py`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_alias_registry.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.search.query_parser.alias_registry import AliasRegistry


def test_alias_registry_prefers_longest_non_overlapping_match():
    registry = AliasRegistry.from_dict({
        'PoDSchedule': ['PoD????', '????'],
        'Room': ['??'],
    })

    mentions = registry.match('???????PoD????')

    assert [(m.surface, m.canonical) for m in mentions] == [
        ('??', 'Room'),
        ('PoD????', 'PoDSchedule'),
    ]
```

Add checks for normalized-order output and exact `start/end` offsets against normalized text.

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_alias_registry.py -v`
Expected: FAIL because `AliasRegistry` does not exist.

**Step 3: Write minimal implementation**

Implement YAML-backed exact phrase matching with:
- stable alias sorting by phrase length descending then lexical tie-break
- non-overlap acceptance
- `EntityMention` offsets against normalized text
- `source='alias_rule'`

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_alias_registry.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add search/query_parser/alias_registry.py tests/search/test_alias_registry.py
git commit -m "feat: add deterministic entity alias matching"
```

### Task 4: Implement rule-based intent classifier

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/intent_classifier.py`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_intent_classifier.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.search.query_parser.intent_classifier import IntentClassifier


def test_intent_classifier_chooses_highest_priority_match():
    classifier = IntentClassifier.from_dict({
        'impact_analysis': {'priority': 100, 'keywords': ['??', '??']},
        'listing_query': {'priority': 40, 'keywords': ['??']},
    })

    result = classifier.classify('?????PoD????????')

    assert result.name == 'impact_analysis'
    assert '??' in result.matched_rules
```

Also cover relation query and default-to-listing fallback.

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_intent_classifier.py -v`
Expected: FAIL because `IntentClassifier` does not exist.

**Step 3: Write minimal implementation**

Implement YAML-backed keyword matching with:
- deterministic priority ordering
- simple score = matched keyword count + normalized priority component
- default fallback to `listing_query`

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_intent_classifier.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add search/query_parser/intent_classifier.py tests/search/test_intent_classifier.py
git commit -m "feat: add rule-based query intent classifier"
```

### Task 5: Implement parsed-query assembly

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/parser.py`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_query_parser.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.search.query_parser.parser import parse_query


def test_parse_query_returns_stable_parsed_query_for_punctuation_variants():
    left = parse_query('????????????PoD?????')
    right = parse_query('????????????PoD????')

    assert left.normalized_query == right.normalized_query
    assert left.canonical_entities == right.canonical_entities == ['Room', 'PoDSchedule']
    assert left.intent.name == right.intent.name == 'impact_analysis'
```

Add one test asserting unmatched terms are returned as a non-blocking debug list.

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_query_parser.py -v`
Expected: FAIL because `parse_query` does not exist.

**Step 3: Write minimal implementation**

Implement `parse_query(raw_query: str) -> ParsedQuery` using:
- shared normalizer
- alias registry
- intent classifier
- stable dedup of canonical entities
- a simple unmatched-term extractor that only serves debug purposes

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_query_parser.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add search/query_parser/parser.py tests/search/test_query_parser.py
git commit -m "feat: assemble parsed query with aliases and intent"
```

### Task 6: Implement soft retrieval planner and seed merge

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/query_parser/retrieval_planner.py`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_retrieval_planner.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.search.query_parser.models import IntentResult, ParsedQuery
from cloud_delivery_ontology_palantir.search.query_parser.retrieval_planner import build_retrieval_plan, merge_seed_entities


def test_merge_seed_entities_keeps_alias_entities_first_and_deduped():
    merged = merge_seed_entities(['Room', 'PoDSchedule'], ['PoDSchedule', 'ActivityInstance'])
    assert merged == ['Room', 'PoDSchedule', 'ActivityInstance']


def test_build_retrieval_plan_for_process_query_prefers_process_relations():
    parsed = ParsedQuery(
        raw_query='PoD????????',
        normalized_query='PoD????????',
        mentions=[],
        canonical_entities=['PoD', 'ActivityInstance'],
        intent=IntentResult(name='process_query', confidence=1.0, matched_rules=['??']),
        unmatched_terms=[],
    )

    plan = build_retrieval_plan(parsed)

    assert plan.seed_entities == ['PoD', 'ActivityInstance']
    assert 'DEPENDS_ON' in (plan.allowed_relations or [])
    assert plan.max_hop == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_retrieval_planner.py -v`
Expected: FAIL because planner functions do not exist.

**Step 3: Write minimal implementation**

Build a planner that returns soft preferences only:
- alias entities become seed entities
- `allowed_relations` represent relation-bias preferences, not hard gates
- `debug_reason` explains intent and selected relation bias

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_retrieval_planner.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add search/query_parser/retrieval_planner.py tests/search/test_retrieval_planner.py
git commit -m "feat: add soft retrieval planning and seed merge"
```

### Task 7: Integrate parser + planner into the retrieval engine

**Files:**
- Modify: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/search/ontology_query_engine.py`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_ontology_query_engine.py`
- Test: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/tests/search/test_query_parser_integration.py`

**Step 1: Write the failing tests**

Add tests proving:
1. alias-derived canonical entities are forwarded into seed selection before LLM-only fallback
2. punctuation variants produce the same alias-derived seeds
3. process or impact intent changes relation scoring preference without turning non-preferred relations into impossible matches

Example:

```python
def test_retrieve_ontology_evidence_prefers_alias_seed_entities_before_llm(monkeypatch):
    ...
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_ontology_query_engine.py tests/search/test_query_parser_integration.py -q`
Expected: FAIL on missing parser/planner integration behavior.

**Step 3: Write minimal implementation**

In `retrieve_ontology_evidence(...)`:
- parse the raw question first
- call LLM intent resolver with `parsed.normalized_query`
- merge alias canonical entities (converted to `object_type:<Name>`) with LLM seed IDs
- apply relation-score bias using `plan.allowed_relations`
- do not hard-filter graph expansion by relation type in this phase

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_ontology_query_engine.py tests/search/test_query_parser_integration.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add search/ontology_query_engine.py tests/search/test_ontology_query_engine.py tests/search/test_query_parser_integration.py
git commit -m "feat: integrate lightweight query parser into retrieval"
```

### Task 8: Add docs and final verification

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/docs/query-parser.md`
- Modify: `C:/Users/w00949875/.codex/worktrees/2833/palantir_mvp/requirements.txt`

**Step 1: Write the docs and dependency update**

Document:
- module responsibilities
- how to edit alias and intent YAML files
- how to run parser tests
- how the parser integrates with `retrieve_ontology_evidence(...)`
- the limitation that `allowed_relations` are soft preferences, not hard gates

Add `PyYAML` to `requirements.txt` if it is not already present.

**Step 2: Run focused verification**

Run: `pytest tests/search/test_surface_normalizer.py tests/search/test_alias_registry.py tests/search/test_intent_classifier.py tests/search/test_query_parser.py tests/search/test_retrieval_planner.py tests/search/test_query_parser_integration.py tests/search/test_ontology_query_engine.py -q`
Expected: PASS

**Step 3: Run full verification**

Run: `pytest tests -q`
Expected: PASS

**Step 4: Commit**

```bash
git add docs/query-parser.md requirements.txt tests/search search/query_parser
git commit -m "docs: add lightweight query parser module guide"
```
