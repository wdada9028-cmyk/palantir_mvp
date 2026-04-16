# Trace Summary Simplification Design

**Date:** 2026-04-07

## Goal
Replace the current debug-heavy logic trace with a customer-facing two-level trace summary that stays concise while still explaining why the answer was produced.

## Decision
The product will expose only two trace levels:
1. compact trace summary (default)
2. expanded trace summary (on demand)

The system will no longer expose TypeQL text, query-plan rows, raw row-count logs, or technical errors in the normal customer UI.

## Compact Trace Summary
The default view contains exactly four sections:
- question_understanding
- key_evidence
- data_gaps
- reasoning_basis

Design rules:
- prefer instance IDs over entity counts when the list is short
- if many instances exist, show first N plus total count
- show only business-meaningful attributes
- do not show technical relation labels unless needed for interpretation

## Expanded Trace Summary
The expanded view contains exactly four sections:
- detailed_evidence
- key_paths
- miss_explanations
- detailed_reasoning_basis

Design rules:
- still no TypeQL or raw query logs
- include concrete instances and a small set of useful attributes
- include only key relation paths, not every path in the graph
- explain why entities were not included in the answer when applicable

## Data Source
The trace summary should be built from the evidence-driven pipeline outputs already present in the backend:
- question_dsl
- fact_pack
- evidence_bundle
- reasoning_result

The summary builder should be deterministic and should not call the LLM.

## New Backend Contract
Add a dedicated trace summary object:

```json
{
  "trace_summary": {
    "compact": {
      "question_understanding": {...},
      "key_evidence": {...},
      "data_gaps": [...],
      "reasoning_basis": [...]
    },
    "expanded": {
      "detailed_evidence": [...],
      "key_paths": [...],
      "miss_explanations": [...],
      "detailed_reasoning_basis": [...]
    }
  }
}
```

## Backend Changes
### New module
- `instance_qa/trace_summary_builder.py`

Responsibilities:
- build compact and expanded summaries from deterministic evidence inputs
- compress instance lists for display
- select a few useful attributes per instance
- map negative evidence into customer-readable miss explanations
- generate short reasoning basis bullets

### Orchestrator
- build `trace_summary` after `evidence_bundle` and `reasoning`
- store it in `InstanceQAResult`

### SSE service
- emit `trace_summary_ready`
- include `trace_summary` in `answer_done`
- stop exposing TypeQL-heavy trace information for the user-facing panel

## Frontend Changes
The QA panel should:
- use `trace_summary.compact` as the default logic trace
- expose a single expand interaction to reveal `trace_summary.expanded`
- stop rendering raw query-plan / TypeQL sections in the normal logic trace area

## Acceptance Criteria
- default trace is noticeably shorter than today
- expanded trace remains customer-readable
- no TypeQL or raw query logs appear in the normal UI
- customer can still see concrete matched instances, key paths, gaps, and why the answer was produced
