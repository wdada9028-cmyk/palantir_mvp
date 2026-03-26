# Lightweight Query Parser Design

**Date:** 2026-03-25

## Goal
Add a lightweight, deterministic query-parsing layer that improves seed stability and retrieval relevance without replacing the existing LLM-assisted retrieval pipeline.

## Problem
The current flow already has surface normalization, local graph scoring, optional LLM seed resolution, graph expansion, evidence packing, and LLM answer generation. The instability problem is mainly in two places:
- semantically equivalent surface forms do not always map to the same ontology entity seeds
- broad graph expansion can pull in adjacent but low-value relations for process / impact questions

A full retrieval planner with hard relation whitelists, multi-stage sufficiency checks, and fallback expansion would likely overcomplicate the current codebase.

## Chosen Scope
This design intentionally stops at the minimum layer that should produce visible improvement:
1. keep the current normalized-query entry point
2. add deterministic alias-to-entity parsing
3. add deterministic intent classification
4. merge alias entities with existing LLM seed entities, with alias precedence
5. use intent only as a **relation-score bias**, not as a hard relation gate

This means the system becomes more stable without introducing a second retrieval engine.

## Non-goals
- No hard `allowed_relations` execution gate in this phase
- No evidence-sufficiency controller
- No multi-stage expansion fallback planner
- No answer-generation rewrite
- No schema changes to ontology objects or relations
- No fuzzy semantic rewrite model

## Architecture
### New package
Create a new package under `search/query_parser/`:
- `models.py`
- `surface_normalizer.py`
- `alias_registry.py`
- `intent_classifier.py`
- `parser.py`
- `retrieval_planner.py`
- `entity_aliases.yaml`
- `intent_rules.yaml`

### Key integration path
Existing high-level flow becomes:

`raw question -> normalize -> parse aliases + intent -> call existing LLM intent resolver -> merge seeds -> existing graph scoring/expansion with relation bias -> evidence bundle -> existing answer layer`

### Why this fits the repo well
- stays inside the existing `search/` module boundary
- reuses the current `retrieve_ontology_evidence(...)` pipeline
- avoids introducing a detached `src/` layout that does not match this repo
- preserves current SSE / template-answer / generator layers

## Data structures
### `EntityMention`
Offsets are defined against `normalized_query`, not `raw_query`.

Reason:
- matching is performed on normalized text
- this keeps offsets deterministic
- avoids raw/normalized offset drift caused by Unicode and punctuation cleanup

### `ParsedQuery`
Carries:
- `raw_query`
- `normalized_query`
- `mentions`
- `canonical_entities`
- `intent`
- `unmatched_terms`

### `RetrievalPlan`
In this phase, `RetrievalPlan` is **soft guidance** only.
Its `allowed_relations` field should be interpreted as **preferred relations for scoring bias**, not a hard filter.

## Alias strategy
### Principles
- exact phrase matching only
- deterministic
- longest-match-first
- non-overlapping mentions only
- configuration-driven via YAML

### Alias coverage
Start with high-confidence aliases only.
Do **not** include generic words like `??`, `??`, `??`, `??` by themselves.

Good examples:
- `?? -> Room`
- `PoD???? -> PoDSchedule`
- `???? -> ActivityInstance`
- `???? -> WorkAssignment`

### Why this is enough
This should already stabilize real queries like:
- `?????????PoD????`
- `PoD?????????`

## Intent strategy
### Intent categories
- `impact_analysis`
- `dependency_analysis`
- `process_query`
- `constraint_query`
- `relation_query`
- `definition_query`
- `listing_query`

### Classification rule
Use YAML-driven keyword rules with deterministic priority.
If multiple intents hit, choose the highest priority one.
If nothing hits, default to `listing_query` because it is the least disruptive fallback for the current retrieval style.

## Retrieval-plan strategy
### Critical simplification
Do **not** make intent a hard gate on graph traversal.

Instead:
- `seed_entities` comes from parsed aliases + optional LLM entities
- `allowed_relations` means preferred relations for ranking bias
- graph expansion may still traverse other relations
- preferred relations simply score higher

### Why this matters
If `impact_analysis` were turned into a hard whitelist, the system could miss structurally important edges like `HAS` or `CONTAINS` that provide context. Using relation bias keeps recall while improving ranking.

## Integration details
### `surface_normalizer.py`
Move / reuse the current query normalization logic here so the query parser and the retrieval engine share one normalization rule.

### `parser.py`
`parse_query(raw_query: str) -> ParsedQuery`

Steps:
1. normalize query
2. match aliases
3. classify intent
4. stable-dedup canonical entities
5. derive unmatched terms for debug only

### `retrieval_planner.py`
Provide:
- `build_retrieval_plan(parsed: ParsedQuery) -> RetrievalPlan`
- `merge_seed_entities(alias_entities, llm_entities=None) -> list[str]`

### `search/ontology_query_engine.py`
Minimal changes only:
1. call `parse_query(question)`
2. call the existing `resolve_intent(graph, parsed.normalized_query)`
3. merge alias entities with LLM seeds
4. add relation-bias scoring based on parsed intent / plan

Do not rewrite the whole retrieval loop.

## Logging
Use `logging.getLogger(__name__)` in each new module.
Key debug points:
- raw query
- normalized query
- alias matches
- detected intent
- merged canonical entities
- retrieval plan summary

## Testing
Add tests under `tests/search/` for:
- surface normalization
- alias matching
- intent classification
- parsed-query stability
- retrieval-plan defaults and seed merge
- one integration test showing punctuation-stable parsing and seed merge behavior

## Expected visible effect
For real process-style questions about PoD scheduling:
- seed entity selection becomes more stable
- process-relevant relations rank earlier
- unrelated side-context edges are less likely to dominate the evidence chain
- same question with / without punctuation produces the same parsed query and the same initial seed set

## Risk level
Low to medium.
The change is additive, configuration-driven, and can fall back to the current resolver path if alias or intent parsing fails.
