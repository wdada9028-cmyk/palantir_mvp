# Ontology Intent Resolver and Semantic Retrieval Design

**Date:** 2026-03-18

## Goal
Allow fuzzy Chinese questions to resolve to ontology schema IDs through a Qwen2.5-32B intent resolver, while keeping the current graph traversal, highlighting, and answer-generation pipeline intact.

## Constraints
- Keep the existing graph traversal algorithm in `D:/????/AI?????/??????/palantir_mvp/search/ontology_query_engine.py`.
- The LLM path must be optional: missing config, timeout, bad JSON, or service failure must fall back to the current keyword seed selection.
- Use an OpenAI-compatible HTTP interface with `temperature=0.1`.
- Do not add new runtime dependencies if the current environment can support the integration.
- Retrieval path reports should stop exposing raw English-only IDs to end users.

## Chosen Approach
Add a dedicated semantic seed resolver module that converts a user question into ontology object IDs before the existing retrieval flow runs. The resolver will build a compact ontology context from the in-memory `OntologyGraph`, call the configured Qwen2.5-32B endpoint, validate the returned IDs against the graph, and return either a stable LLM result or a structured fallback result.

`retrieve_ontology_evidence()` will call the resolver first, then choose between:
1. LLM-provided seed IDs when valid seeds are returned.
2. The current `_select_seed_node_ids()` keyword scoring path when the resolver is unavailable, invalid, or empty.

This keeps the traversal logic unchanged while improving recall for colloquial Chinese phrasing.

## Resolver Design
### New module
Create `D:/????/AI?????/??????/palantir_mvp/search/intent_resolver.py`.

### Public API
Expose:
- `IntentResolution`
  - `seeds: list[str]`
  - `reasoning: str`
  - `source: str` (`llm`, `fallback`, `disabled`)
  - `error: str`
- `resolve_intent(graph, query, *, timeout_s=3.0) -> IntentResolution`

### Model context
Build prompt context from graph objects of type `ObjectType` using:
- object ID
- English name
- aliases
- Chinese description
- group

The resolver should not read the markdown file directly at query time; it should reuse the already-built graph so runtime behavior always matches the served ontology.

### Prompt contract
The prompt must:
- describe the ontology entity list
- ask the model to identify which ontology entities the user refers to
- force JSON output with `seeds` and `reasoning`
- explicitly say: if no matching entity exists in the provided list, return `[]` and do not guess nonexistent IDs

### HTTP client
Use `httpx.Client` with either:
- a module-level singleton client with configured limits, or
- a context-managed client factory if tests need isolation

Recommended limits:
- low connection count
- explicit timeout
- keep-alive enabled

### Environment variables
Use:
- `QWEN_API_BASE`
- `QWEN_API_KEY`
- `QWEN_MODEL` (default `qwen2.5-32b-instruct`)

If required config is missing, return a non-throwing fallback result immediately.

## Retrieval Integration
### Seed selection flow
`retrieve_ontology_evidence()` should:
1. normalize the question as today
2. call `resolve_intent(graph, question)`
3. if valid seeds exist, use them as initial seeds
4. otherwise run the current keyword scoring and `_select_seed_node_ids()` path unchanged
5. continue the existing expansion, evidence, and highlight-step generation unchanged

### Trace enrichment
Extend `SearchTrace` so the first part of the trace records:
- resolution source
- reasoning
- error if fallback happened because of failure

This allows the front-end and answer layer to explain why a seed was selected without changing the traversal data structure.

## Answer Rendering Design
### Display name mapping
Populate `OntologyEvidenceBundle` with:
- `display_name_map: dict[str, str]`
- `relation_name_map: dict[str, str]`

Display format for entities must be:
- `???(??ID)`
- example: `????(PlacementPlan)`

If Chinese text is missing, fall back to the English name/ID.

### Relation rendering
Map relation codes to readable Chinese labels using the same translation table already used by graph export when possible. Search trace output should render relation names as bracketed labels such as `[??]` or `[???]`.

### Output example
Instead of:
- `??? REFERENCES ??? PoD`

Render:
- `???[??]?????[????(PoD)]`

## Failure Handling
Resolver failures must never break retrieval. Treat the following as soft failures:
- missing API base or key
- timeout
- HTTP non-200
- invalid JSON
- seeds that are not present in the graph
- empty seeds

All of these should produce a fallback result and preserve the legacy keyword path.

## Testing Design
### Resolver tests
Add `D:/????/AI?????/??????/palantir_mvp/tests/search/test_intent_resolver.py` to cover:
- valid JSON response
- empty list response
- invalid JSON response
- timeout/HTTP failure
- invalid seed filtering
- config-missing disabled path

### Query engine tests
Extend `D:/????/AI?????/??????/palantir_mvp/tests/search/test_ontology_query_engine.py` to cover:
- LLM seeds override keyword scoring
- fallback still resolves English IDs when the resolver fails
- trace stores resolver reasoning/source/error

### Template answer tests
Extend `D:/????/AI?????/??????/palantir_mvp/tests/qa/test_template_answering.py` to cover:
- trace reports use `???(??ID)` labels
- relation names are localized
- final output no longer exposes raw English-only path text

## Rejected Alternatives
1. Inject the LLM call directly into traversal logic
   - rejected because retrieval and transport concerns become tightly coupled
2. Replace keyword retrieval entirely with LLM selection
   - rejected because service failure would break deterministic local behavior
3. Build a static synonym table only
   - rejected because it does not solve fuzzy colloquial questions like `?????`
