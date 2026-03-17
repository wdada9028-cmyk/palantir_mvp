# Ontology Search Trace Playback Design

**Date:** 2026-03-17

## Goal
Enhance the ontology QA flow so users can watch deterministic retrieval progress over the ontology graph in real time, while preserving the current SSE contract for backward compatibility.

## Constraints
- Do not modify `ontology/definition_markdown_parser.py`.
- Keep ontology markdown as the single source of truth.
- Preserve the legacy `/api/qa/stream` event contract.
- Add new trace events without breaking existing tests/consumers.
- Use Unicode-safe strings in generated HTML/JS templates.
- Reset playback state fully in `clearQaPresentation()` before each new query.

## Chosen Approach
Adopt a dual-protocol incremental extension:
- Keep legacy SSE events: `anchor_node`, `expand_neighbors`, `filter_nodes`, `focus_subgraph`, `evidence`, `answer_done`.
- Add new SSE events: `trace_anchor`, `trace_expand`, `evidence_final`.
- Extend the retrieval bundle with deterministic `search_trace` data.
- Upgrade the front-end with a trace-oriented `PlaybackController` that prefers the new protocol and falls back to legacy behavior only when necessary.

## Rejected Alternatives
1. Full protocol replacement
   - Cleaner, but breaks compatibility and expands regression risk.
2. Final trace blob only, with front-end local decomposition
   - Simpler backend, but weaker observability and testability.

## Data Model Design
### `search/ontology_query_models.py`
Add:
- `TraceExpansionStep`
  - `step`
  - `from_node_id`
  - `edge_id`
  - `to_node_id`
  - `relation`
  - `reason`
  - `snapshot_node_ids`
  - `snapshot_edge_ids`
- `SearchTrace`
  - `seed_node_ids`
  - `expansion_steps`
- `OntologyEvidenceBundle.search_trace`

## Retrieval Design
### `search/ontology_query_engine.py`
- Preserve deterministic node selection and relation traversal order.
- Reuse the current seed node scoring/selection logic.
- While expanding from seed nodes through adjacent relations, record each path step as a `TraceExpansionStep`.
- Store cumulative snapshot node/edge IDs at each step for playback and evidence click-back.
- Continue producing `highlight_steps` and `evidence_chain` for compatibility.

## SSE Design
### `server/ontology_http_service.py`
Emit both old and new events.
New event order:
1. `trace_anchor`
2. `trace_expand` (zero or more)
3. `evidence_final`
4. `answer_done`

Rules:
- Do not sleep server-side.
- Include `delay_ms` in trace payloads so the front-end schedules playback.
- Keep `answer_done` as the final answer carrier.

## Front-End Playback Design
### `export/graph_export.py`
Enhance the generated HTML/JS with:
- CSS classes:
  - `.searching-node`
  - `.trace-path`
  - `.trace-dimmed`
- A trace-first `PlaybackController` managing:
  - queue
  - running state
  - timers
  - persisted evidence data
  - evidence snapshots
  - current snapshot
- Behaviors:
  - `trace_anchor`: focus seed nodes, fit view, dim unrelated elements, pulse searching nodes.
  - `trace_expand`: sequentially highlight traversed edge and destination node, maintain cumulative path state.
  - `evidence_final`: populate clickable evidence timeline buttons.
  - timeline click: `replayFromSnapshot(snapshot)` and visibly re-highlight the recovered path.
- Keep legacy listeners only as a fallback path if no new trace events arrive.

## Answer Design
### `qa/template_answering.py`
Return two parts:
1. Search trace report
2. Current conclusion / evidence summary

Generate path narration from `search_trace`, for example:
- Match report: through matching a core concept
- Expansion report: along a relation to another concept
- Retain insufficient-evidence messaging for runtime-status questions.

## Testing Design
### Search
- Assert `search_trace.seed_node_ids`.
- Assert deterministic `expansion_steps` order.
- Assert snapshot contents are cumulative and stable.

### Server
- Preserve legacy event assertions.
- Add assertions for new event sequence and `delay_ms` payloads.

### Front-End Export
- Assert presence of new CSS classes, playback controller hooks, replay helpers, evidence timeline container, and new event listeners.

### QA Answer
- Assert the answer contains a retrieval path report plus the existing summary semantics.

## Acceptance Mapping
- Graph auto-focus and stepwise highlighting: handled by `PlaybackController` using `trace_anchor`/`trace_expand`.
- Non-relevant areas dimmed: `.trace-dimmed`.
- Evidence click replay: timeline buttons + snapshot replay.
- Regression safety: keep old SSE protocol and verify both paths in tests.
