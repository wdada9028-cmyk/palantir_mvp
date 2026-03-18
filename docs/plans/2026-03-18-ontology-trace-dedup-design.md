# Ontology Trace Simplification and Dedup Design

**Date:** 2026-03-18

## Goal
Reduce ontology path report verbosity by rendering only concise `中文名(ID)` entity labels, deduping repeated logical edges in the rendered report, and making the relation summary compact and scan-friendly.

## Chosen Approach
Apply the simplification in the answer-rendering layer so retrieval and SSE trace payloads remain unchanged. The search layer will continue returning the full ordered `SearchTrace`, while `qa/template_answering.py` will be responsible for:
- rendering only `中文名(ID)` labels
- rendering relation predicates as bracketed labels like `[引用]`
- deduping repeated `(from_node_id, relation, to_node_id)` hops before building text
- producing a compact bullet-style relation summary instead of repeating the same prose

## Why This Approach
Keeping dedupe in the template layer avoids changing retrieval behavior, trace event payloads, and front-end replay assumptions. It also localizes the change to user-facing text, which is where the problem exists.

## Data Handling
- `display_name_map` remains the source of truth for entity labels, but path rendering will only use the concise label string and never append long semantic descriptions.
- `relation_name_map` will store bracketed forms such as `[包含]`, `[引用]`, `[作用于]` so long sentences remain visually scannable.
- A local `visited_edges` set in the template layer will filter repeated `(from, relation, to)` tuples for both the path report and the final relation summary.

## Testing Strategy
Add regression tests that prove:
- path text uses only `中文名(ID)` labels
- repeated logical edges appear only once in the report
- relation summary is rendered as a deduped list
- bracketed relation labels are used consistently
- no raw verbose semantic-description text leaks into the answer
