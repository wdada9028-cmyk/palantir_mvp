# Markdown Ontology Definition Graph Design

**Date:** 2026-03-16  
**Target markdown:** `D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md`

## Goal
Rebuild the project so the markdown ontology definition document itself is the single source of truth and is converted directly into the final ontology graph, without any LLM extraction, instance graph construction, retrieval pipeline, or scheduler.

## Decision summary
- Keep a small reusable graph model foundation.
- Remove the old LLM-driven ingestion / retrieval / scheduling workflow.
- Parse the markdown deterministically with rule-based section parsing.
- Build the final graph directly from document-defined object types, link types, and derived metrics.
- Render the result as `ontology.json`, `schema_summary.json`, and an interactive HTML prototype page.

## Non-goals
- No business instance graph generation.
- No semantic chunking, embeddings, or question answering.
- No project scheduling or critical-path computation.
- No inferred relations that are not explicitly defined in the markdown.

## Final graph shape
### Nodes
1. `ObjectType` nodes from `## 4. Object Types`
2. `DerivedMetric` nodes from `## 6. ??????`

### Edges
- Only relations explicitly defined in `## 5. Link Types`

### Node attributes
Each `ObjectType` node stores:
- `group`
- `chinese_description`
- `semantic_definition`
- `key_properties`
- `status_values`
- `rules`
- `notes`
- `suggested_violation_types`
- `source_lines`

Each `DerivedMetric` node stores:
- `group`
- `description`
- `source_lines`

### Graph metadata
The final graph stores:
- `graph_kind = ontology_definition_graph`
- document title
- source file path
- modeling boundaries from `## 2`
- mainline from `## 3`
- optional properties and notes from `## 4.7`
- counts for object types, derived metrics, relations, and total nodes

## UI / prototype behavior
### Main layout
- Left: interactive ontology graph
- Right: detail panel for the selected node
- Top: search, relation filter, group view toggle, derived-metric toggle, reset

### Detail panel
The detail panel shows:
- node name
- node kind
- group
- Chinese description / semantic definition
- key properties
- statuses / rules / notes where present
- relation summary only by default
- expandable relation details on demand

### Relation display rule
- Do not dump all in-edges/out-edges into the panel by default.
- Show counts and relation labels first.
- Allow expand/collapse for full relation detail.

### Derived metric display rule
- Show derived metrics as a collapsible group in the graph.
- Do not infer ownership edges unless explicitly added to the source markdown later.

## Parsing strategy
The markdown is treated as a constrained DSL, not as free-form prose.

### Supported high-level sections
- `## 2. ??????`
- `## 3. ????`
- `## 4. Object Types`
- `## 4.7 MVP ?????????`
- `## 5. Link Types`
- `## 6. ??????`

### Object type parsing rules
- `### \`EntityName\`` starts a new object type.
- `?????...` fills `chinese_description`.
- `?????...` fills `semantic_definition`.
- `?????` enters a property-list mode.
- `?????` enters a named-value mode.
- `?????` enters a free-text list mode.
- `????????` enters a named-value mode.
- `???` / `?????` / `?????` append to notes.

### Property item parsing
- Expected form: `- \`property_name\`?????`
- Store both the property name and its description.

### Relation parsing
- Expected form: `- \`Source RELATION Target\`???`
- Relation direction is taken exactly from the markdown.
- No reverse edges are auto-generated.

### Derived metric parsing
- Expected form: `- \`metric_name\`?????`
- Each metric becomes a `DerivedMetric` node.

## Validation rules
The parser / builder must fail fast with line-numbered errors for:
- duplicate object type names
- duplicate property names inside the same object type
- malformed relation triples
- relations referencing undefined object types
- duplicate relation triples
- missing required content in `Object Types` or `Link Types`

## Output files
### Required
- `D:/????/AI?????/??????/palantir_mvp/output/ontology.json`
- `D:/????/AI?????/??????/palantir_mvp/output/schema_summary.json`

### Visualization
- `D:/????/AI?????/??????/palantir_mvp/output/ontology.html`
- `D:/????/AI?????/??????/palantir_mvp/output/ontology.pdf` (optional)

## File-level redesign
### Keep and adapt
- `D:/????/AI?????/??????/palantir_mvp/models/ontology.py`
- `D:/????/AI?????/??????/palantir_mvp/schema.py`
- `D:/????/AI?????/??????/palantir_mvp/export/graph_export.py`
- `D:/????/AI?????/??????/palantir_mvp/cli.py`

### Add
- `D:/????/AI?????/??????/palantir_mvp/ontology/definition_models.py`
- `D:/????/AI?????/??????/palantir_mvp/ontology/definition_markdown_parser.py`
- `D:/????/AI?????/??????/palantir_mvp/ontology/definition_graph_builder.py`
- `D:/????/AI?????/??????/palantir_mvp/ontology/definition_writer.py`
- `D:/????/AI?????/??????/palantir_mvp/pipelines/build_ontology_pipeline.py`

### Remove after cutover
- LLM, extraction, retrieval, scheduling, and sample-data paths:
  - `D:/????/AI?????/??????/palantir_mvp/prompts.py`
  - `D:/????/AI?????/??????/palantir_mvp/extractor.py`
  - `D:/????/AI?????/??????/palantir_mvp/pipeline.py`
  - `D:/????/AI?????/??????/palantir_mvp/retriever.py`
  - `D:/????/AI?????/??????/palantir_mvp/sample_data.py`
  - `D:/????/AI?????/??????/palantir_mvp/ask_three_questions.py`
  - `D:/????/AI?????/??????/palantir_mvp/answering/*`
  - `D:/????/AI?????/??????/palantir_mvp/ingestion/*`
  - `D:/????/AI?????/??????/palantir_mvp/planning/*`
  - `D:/????/AI?????/??????/palantir_mvp/search/*`
  - `D:/????/AI?????/??????/palantir_mvp/ontology/builder.py`
  - `D:/????/AI?????/??????/palantir_mvp/ontology/mapper.py`
  - `D:/????/AI?????/??????/palantir_mvp/ontology/registry.py`

## Risks and mitigations
### Risk: markdown format drift
Mitigation: strict parser validation with clear line-numbered errors and narrow supported syntax.

### Risk: graph exporter still assumes schedule/task semantics
Mitigation: rewrite exporter around dynamic node attributes and runtime-derived relation filters.

### Risk: leftover legacy tests create noise
Mitigation: replace old LLM / retrieval / scheduling tests with parser, builder, and CLI integration tests.

## Verification targets
The completed redesign should satisfy:
1. Running one CLI command against the markdown generates `ontology.json`, `schema_summary.json`, and `ontology.html`.
2. The generated graph contains every object type defined in section 4.
3. The generated graph contains every relation defined in section 5.
4. Clicking a node in the HTML view shows that node's property list and definition details.
5. The UI shows relation summary by default and only expands full edge detail on demand.

## Git note
This workspace currently does not contain a `.git` directory, so the design document cannot be committed here unless the repository is initialized or opened from the actual git root.
