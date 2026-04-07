# Evidence-Driven TypeDB Instance QA Design

**Date:** 2026-04-07

## Goal
Upgrade the current TypeDB-backed instance QA path from count-style summaries into an evidence-driven QA system that answers from concrete instance rows, aligned schema fragments, and relation paths, with the LLM doing the final reasoning under explicit evidence constraints.

## Scope
This design covers the next iteration of instance QA:
- keep `/api/qa/stream` as the single user-facing entrypoint
- keep TypeDB as the read-only single data backend
- keep backend-generated TypeQL and schema-constrained traversal
- replace impact-specific backend reasoning as the primary answer path with a generic evidence-bundle + LLM reasoning path
- pass full matched instance rows with attribute names to the LLM
- preserve empty / unrelated / omitted evidence categories so the LLM can reason conservatively

## Non-goals
- No LLM-generated TypeQL
- No backend-maintained event-specific business inference rules as the main reasoning layer
- No unrestricted whole-database expansion
- No attribute-level hard filtering before the LLM sees a matched row
- No write operations against TypeDB

## Architectural Decision
The system will keep deterministic query planning and TypeDB access in the backend, but move answer reasoning to a generic evidence-driven LLM stage.

Final path:

```text
User question
-> query normalization / anchor detection / schema grounding
-> Fact Query DSL planning
-> backend-generated TypeQL
-> TypeDB read-only execution
-> evidence subgraph construction
-> schema-instance alignment
-> evidence bundle construction
-> LLM answer context construction
-> constrained LLM reasoning + answer generation
-> SSE response
```

## Core Principle
The backend is responsible for gathering and structuring evidence. The LLM is responsible for interpreting the evidence and answering the user question. The backend should not decide which matched attribute is business-relevant; it should preserve the full matched row with attribute names and let the LLM decide relevance under prompt constraints.

## Evidence Model
### Positive evidence
Matched instances that are actually connected to the current anchor-centric evidence subgraph.

Each matched instance must preserve:
- entity name
- TypeDB iid
- full attribute row with attribute names
- business key candidates when available
- the minimal schema fragment needed to understand the entity and its relations
- one or more relation paths showing why the instance is in scope

Example shape:

```json
{
  "entity": "Floor",
  "iid": "0x1e00020000000000000005",
  "business_keys": {"floor-id": "L1"},
  "attributes": {
    "floor-id": "L1",
    "floor-no": 1,
    "install-sequence": 1
  },
  "schema_context": {
    "entity_name": "Floor",
    "entity_zh": "??",
    "key_attributes": ["floor-id"],
    "relevant_relations": ["building-floor", "floor-room"]
  },
  "paths": [
    "Room(L1-A) <- floor-room - Floor(L1)"
  ]
}
```

### Empty entities
Schema entities that were queried but have no instance data for the current query. These must not be treated as positive facts.

### Unrelated entities
Schema entities that have instances in the database, but none of those instances are connected to the current evidence subgraph. These must not be treated as direct evidence for the current answer.

### Omitted entities / instances
Entities or instances truncated due to token or breadth limits. These must be surfaced explicitly so the LLM can describe possible incompleteness.

## Schema Usage
The LLM should not receive the entire ontology. It should receive only schema fragments aligned to matched instances:
- entity label / Chinese name when available
- key attributes
- current query-relevant relations
- optional attribute labels if already available in the graph

This keeps the context grounded and small while still helping the model understand field semantics.

## Instance Data Policy
The backend must not decide which fields are important at the attribute level. For every matched instance included in evidence:
- preserve the full row
- preserve attribute names exactly
- preserve iid
- keep relation context separate from the attribute payload

The model will determine which fields are business-relevant for the question.

## LLM Responsibilities
The LLM is allowed to:
- infer which matched instances matter most to the user question
- infer which attributes are relevant
- synthesize evidence across relation paths
- distinguish between direct facts, evidence-based inference, and unknowns

The LLM is not allowed to:
- invent instances, relations, or data not present in the bundle
- treat empty entities as matched evidence
- treat unrelated entities as direct evidence
- answer beyond the provided evidence without clearly marking uncertainty

## Prompt Contract
The LLM prompt must explicitly enforce:
- evidence-only answering
- preference for instance-level explanation over entity counts
- explicit use of attribute names and values when relevant
- distinction between positive evidence, empty entities, unrelated entities, and omitted entities
- explanation of uncertainty boundaries when evidence is incomplete

## New Backend Modules
### `instance_qa/evidence_models.py`
Dataclasses / typed payloads for evidence nodes, edges, paths, groups, and bundle.

### `instance_qa/evidence_subgraph_builder.py`
Builds a deduplicated anchor-centric evidence subgraph from TypeDB rows and links.

### `instance_qa/schema_instance_aligner.py`
Aligns matched instances to minimal schema fragments from the ontology graph / schema registry.

### `instance_qa/evidence_bundle_builder.py`
Builds the final evidence bundle with positive, empty, unrelated, and omitted sections.

### `instance_qa/llm_answer_context_builder.py`
Converts the evidence bundle into a token-controlled prompt payload for the answer model.

### `instance_qa/prompts.py`
Stores the system/task/evidence/style prompts for evidence-driven answer generation.

## Existing Module Changes
### `instance_qa/orchestrator.py`
Must shift from `fact_pack + reasoning -> fallback answer` to `fact_pack -> evidence bundle -> llm answer context -> generator`.

### `instance_qa/typeql_builder.py`
Must ensure matched entities can project full row data for included entities.

### `instance_qa/typedb_result_mapper.py`
Must preserve iid, full attribute rows, and enough link metadata to reconstruct paths.

### `qa/generator.py`
Must consume the new evidence-driven prompt contract rather than only counts + example rows.

### `qa/template_answering.py`
Must remain a fallback path only.

### `server/ontology_http_service.py`
Must stream the new evidence-building stages and the final LLM answer.

## SSE / Trace Changes
Add or repurpose stages to expose:
- evidence subgraph built
- schema-instance aligned
- evidence bundle ready
- LLM context ready
- answer generation done

The trace should continue to show TypeQL execution, but the answer path should explain how evidence was assembled.

## First-Version Limits
- keep current anchor-centric retrieval style
- keep bounded propagation depth
- include all fields for included rows, but still cap total instance count per entity / bundle
- no attempt to solve arbitrary huge graph exploration in one turn

## Acceptance Criteria
The iteration is complete when:
1. Each included matched instance is passed to the LLM with full attributes and attribute names.
2. The answer generator receives aligned schema fragments rather than raw global schema lists.
3. Empty and unrelated entities are preserved as negative evidence, not deleted silently.
4. Final answers can reference concrete instances and their attributes instead of only entity counts.
5. The fallback template remains available when the model or evidence packaging is unavailable.
