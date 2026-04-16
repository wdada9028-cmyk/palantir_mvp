# TypeDB Instance QA Design

**Date:** 2026-04-02

## Goal
Replace the current schema-only ontology QA path with an instance-aware TypeDB-backed QA path that keeps the existing `/api/qa/stream` entrypoint, reuses the current ontology/schema grounding assets, and answers business questions from real TypeDB instance data rather than only schema relations.

## Scope
This design covers the first production-oriented iteration of instance QA:
- use TypeDB as the single read backend for instance facts
- keep current ontology/schema parsing and graph building as the schema grounding layer
- preserve the current HTTP + SSE entrypoint and front-end QA shell
- replace the current schema-only middle path with a controlled instance-query pipeline
- support both factual instance lookup and scenario-based impact/risk questions

## Non-goals
- No LLM-generated TypeQL
- No arbitrary free-form graph reasoning without backend constraints
- No write/update/delete operations against TypeDB
- No multi-database routing in the first version
- No unrestricted deep graph search

## Architectural Decision
The system will keep the current user-facing entrypoint and query normalization layer, but replace the core QA orchestration path with a new controlled TypeDB instance QA orchestrator.

Final path:

```text
User question
-> query normalization / alias matching / basic intent parsing
-> Question DSL extraction
-> Question DSL validation against schema registry
-> Fact Query DSL planning
-> Fact Query DSL validation
-> TypeQL generation by backend
-> read-only TypeDB execution
-> instance result mapping
-> schema-driven reasoning + event overrides
-> final LLM summarization
-> SSE response
```

## Current System Reuse
### Keep
- `search/query_parser/*` for surface normalization, aliases, basic intent hints
- ontology/schema graph build path based on markdown/TQL conversion
- `/api/qa/stream` as the serving entrypoint
- current graph HTML / QA panel shell

### Replace as primary orchestration path
- `search/ontology_query_engine.py` as the main QA engine
- `search/ontology_query_models.py` as the main answer bundle contract
- `qa/template_answering.py` schema-only fallback assumptions
- `qa/generator.py` schema-only fact summarization assumptions
- `server/ontology_http_service.py` schema-only event semantics

## TypeDB Integration Constraints
First version assumptions:
- single TypeDB database
- read-only query access
- connection information provided via environment variables
- runtime failure must degrade gracefully with explicit user-facing fallback rather than guessed answers

Suggested environment variables:
- `TYPEDB_ADDRESS`
- `TYPEDB_DATABASE`
- `TYPEDB_USERNAME`
- `TYPEDB_PASSWORD`
- optional transport/session tuning variables only if later needed

## Query Understanding Model
The system should not bucket user questions into a tiny public set of query types. Instead it should parse every question into a controlled internal Question DSL that captures:
- anchor entity
- anchor instance identifier or filters
- scenario/event if present
- target goal if present
- constraints such as deadline, time window, statuses, limit

### Question DSL
```python
{
  "mode": "fact_lookup | impact_analysis | deadline_risk_check",
  "anchor": {
    "entity": "Room",
    "identifier": {
      "attribute": "room_id",
      "value": "01"
    },
    "surface": "01机房"
  },
  "scenario": {
    "event_type": "power_outage | fire | delay | capacity_loss | access_blocked | generic_incident",
    "duration": {
      "value": 7,
      "unit": "day"
    },
    "start_time": null,
    "severity": null,
    "raw_event": "断电"
  },
  "goal": {
    "type": "list_impacts | yes_no_risk | explain_risk | instance_lookup | count",
    "target_entity": "ProjectMilestone",
    "target_metric": "delivery",
    "deadline": "2026-04-10"
  },
  "constraints": {
    "statuses": [],
    "time_window": null,
    "limit": 20
  }
}
```

### Why Question DSL exists
The Question DSL is the single structured contract between natural-language understanding and backend planning. LLM is allowed to produce this DSL, but not any database query language.

## Schema Registry
A schema registry will be built from the current `OntologyGraph` so the system has a runtime source of truth for:
- entity names
- key attributes
- legal attributes
- legal relations
- adjacency graph by entity + direction
- relation-to-entity pair compatibility

### Registry responsibilities
- constrain Question DSL extraction prompt options
- validate Question DSL fields
- validate Fact Query DSL fields
- drive TypeQL generation
- drive generic propagation over legal graph edges

## Fact Query DSL
Question DSL is not executed directly. It is expanded into one or more controlled Fact Query DSL objects.

```python
{
  "purpose": "resolve_anchor | collect_neighbors | collect_related_instances | collect_deadline_targets | collect_constraints",
  "root": {
    "entity": "Room",
    "identifier": {
      "attribute": "room_id",
      "value": "01"
    }
  },
  "filters": [
    {
      "entity": "Room",
      "attribute": "room_status",
      "op": "eq",
      "value": "active"
    }
  ],
  "traversals": [
    {
      "from_entity": "Room",
      "relation": "OCCURS_IN",
      "direction": "in",
      "to_entity": "WorkAssignment",
      "required": true
    },
    {
      "from_entity": "WorkAssignment",
      "relation": "ASSIGNS",
      "direction": "out",
      "to_entity": "PoD",
      "required": false
    }
  ],
  "projection": {
    "Room": ["room_id", "room_status"],
    "WorkAssignment": ["assignment_id", "assignment_status", "assignment_date"],
    "PoD": ["pod_id", "pod_code", "planned_handover_time"]
  },
  "aggregate": null,
  "sort": [
    {
      "entity": "WorkAssignment",
      "attribute": "assignment_date",
      "direction": "asc"
    }
  ],
  "limit": 100
}
```

First version limits:
- single root entity
- identifier or direct root filters
- at most 2 traversals
- simple comparison operators only
- count/list/detail style aggregates only
- limit always enforced

## LLM Responsibilities
### Allowed
- normalize user problem into Question DSL
- summarize final answer using validated facts and reasoning output

### Forbidden
- generate TypeQL
- invent entities/attributes/relations not in schema registry
- decide legal graph traversals independently of backend policy
- invent unsupported risk conclusions without evidence

## TypeQL Generation
TypeQL must be generated only by backend code from validated Fact Query DSL.

The builder must:
- use schema registry to bind entity, attribute, and relation names
- generate deterministic read-only match/fetch/count patterns
- reject unsupported traversal shapes
- apply projection, limit, and sorting safely
- preserve enough structural metadata so result mapping can recover entity identity and relation context

## TypeDB Execution
A dedicated TypeDB client module will:
- establish read-only sessions/transactions
- execute backend-generated TypeQL
- map raw result rows into neutral dictionaries
- expose explicit error categories: connection/config/query/runtime
- never execute text produced directly by the model

## Result Mapping
Raw TypeDB rows are not appropriate LLM context. A result mapper will convert them into a Fact Pack containing:
- resolved anchor instance
- related instances by entity type
- relevant time fields
- relevant status fields
- explicit evidence chains
- query metadata (limits hit, result counts, degraded modes)

## Reasoning Model
The first version does not use unrestricted free-form reasoning. It uses controlled backend reasoning.

### Generic propagation
All anchor entities are supported by default through schema-driven propagation:
- legal neighbor expansion comes from schema registry adjacency
- traversal depth is limited
- only legal entity-relation-direction triples are allowed

### Event override layer
A small event profile layer improves precision for known event families:
- `power_outage`
- `fire`
- `delay`
- `capacity_loss`
- `access_blocked`
- fallback `generic_incident`

Event overrides do not replace the generic graph propagation model. They modify it by:
- boosting/reducing relation priority
- adding event-family heuristics
- adjusting baseline risk/confidence
- supplying deadline heuristics

### Unknown event handling
Questions outside the small curated override list must still be answered.
Behavior:
- normalize to nearest event family if possible
- otherwise use `generic_incident`
- run generic schema-driven propagation
- downgrade confidence and avoid over-strong yes/no claims if evidence is weak

### Deadline risk logic
Deadline questions such as “是否影响 4/10 交付” should be determined by backend logic over instance facts, not by LLM intuition.

Primary date-bearing evidence fields for first version:
- `PoD.planned_handover_time`
- `PoD.actual_handover_time`
- `WorkAssignment.assignment_date`
- `ActivityInstance.planned_start_time`
- `ActivityInstance.planned_finish_time`
- `ActivityInstance.latest_finish_time`
- `RoomMilestone.due_time`
- `FloorMilestone.due_time`

Backend reasoning output should be structured:
```python
{
  "summary": {
    "answer_type": "impact_list | deadline_risk",
    "risk_level": "high | medium | low | unknown",
    "confidence": "high | medium | low"
  },
  "affected_entities": [
    {"entity": "WorkAssignment", "id": "WA-001", "reason": "发生于01机房"}
  ],
  "deadline_assessment": {
    "deadline": "2026-04-10",
    "at_risk": true,
    "reason_codes": ["affected_work_assignment_before_deadline"],
    "supporting_facts": ["assignment_date overlaps deadline window"]
  },
  "evidence_chains": [
    [
      "Room(01)",
      "WorkAssignment(WA-001) --OCCURS_IN--> Room(01)",
      "WorkAssignment(WA-001) --ASSIGNS--> PoD(POD-009)"
    ]
  ]
}
```

LLM only verbalizes this output.

## SSE / UX Contract
The HTTP entrypoint stays the same, but the streamed steps change to reflect the new pipeline:
- `question_parsed`
- `question_dsl`
- `fact_query_planned`
- `typedb_query`
- `typedb_result`
- `reasoning_done`
- `answer_delta`
- `answer_done`

The front-end QA panel should surface:
- recognized anchor + event
- the validated structured interpretation
- the fact query summary
- instance result summary
- reasoning summary and confidence
- final answer

## Package Layout
New package:
- `instance_qa/question_models.py`
- `instance_qa/question_extractor.py`
- `instance_qa/schema_registry.py`
- `instance_qa/fact_query_models.py`
- `instance_qa/fact_query_planner.py`
- `instance_qa/fact_query_validator.py`
- `instance_qa/typeql_builder.py`
- `instance_qa/typedb_client.py`
- `instance_qa/typedb_result_mapper.py`
- `instance_qa/reasoner.py`
- `instance_qa/result_formatter.py`
- `instance_qa/orchestrator.py`
- `instance_qa/event_profiles.yaml`

## File-level migration
### Keep
- `search/query_parser/*`
- `ontology/*`
- `server/ontology_http_app.py` route shape
- `export/graph_export.py` shell and graph visual layer

### Replace primary role
- `search/ontology_query_engine.py`
- `search/ontology_query_models.py`
- `qa/template_answering.py`
- `qa/generator.py`
- `server/ontology_http_service.py`

## Verification Goals
The finished implementation should prove:
1. `/api/qa/stream` answers from TypeDB instance facts rather than only schema relationships.
2. Anchor instance lookup is constrained by the ontology-derived schema registry.
3. TypeQL is backend-generated only.
4. Unknown event expressions still return a controlled generic-impact answer.
5. Deadline-risk answers are supported by explicit time-bearing instance evidence.
6. The system remains explainable through streamed structured steps and evidence chains.
