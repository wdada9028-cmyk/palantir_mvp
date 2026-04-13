# Session Log

## Current State
- Agent: Codex
- Branch: codex/llm-question-router
- Last session: 2026-04-10 16:39
- Active work: cleaned QA playback/status copy, removed raw ** entity emphasis in the answer panel, and fixed attribute-lookup fallback wording so POD status answers and trace replay stay customer-readable
- Blockers: None
- Next steps:
  - Browser-smoke POD-001??????? and L1-A??????????????
  - If the live browser is clean, commit the router + playback UX changes together

## Session History


### 2026-04-10 16:39 - Codex
**What was done:**
- Fixed instance-QA SSE trace copy so `trace_anchor`, `trace_expand`, and `evidence_final` now emit readable Chinese instead of placeholder question marks
- Cleaned `build_instance_template_answer(...)` so attribute lookups return natural sentences like `POD-001 ????? Installing?`
- Updated instance answer style guidance to discourage Markdown emphasis and added front-end formatting that converts accidental `**...**` inline emphasis into a styled pill instead of raw asterisks
- Added regression tests for clean trace copy, clean attribute fallback wording, and answer-panel formatting; re-ran targeted suites plus the full suite successfully

**Decisions made:**
- Keep the router/playback behavior unchanged; only repair customer-visible wording and answer rendering
- Handle stray Markdown emphasis defensively in the front end while also steering the LLM away from `**...**` in prompts

**Open questions:**
- Whether to do one final manual browser smoke before commit


### 2026-04-10 15:58 - Codex
**What was done:**
- Changed instance QA schema playback so `anchor_only` queries build a seed-only schema bundle instead of reusing the old expanding schema retrieval path
- Added regression coverage proving `POD-001???????` emits `trace_anchor` only and no `trace_expand` events
- Revalidated the service behavior manually: POD status queries now highlight only `PoD`, while impact analysis still uses schema-entity expansion
- Re-ran targeted suites and the full test suite successfully

**Decisions made:**
- Playback must follow router scope, not independently re-run broad schema retrieval for attribute lookups
- Even for `expand_graph`, playback remains schema-entity-only; instance rows stay answer-side only

**Open questions:**
- Whether to expose the chosen router scope directly in the front-end debug panel

### 2026-04-10 15:27 - Codex
**What was done:**
- Verified `typedb_schema_v4.converted.md` was not empty and isolated the real router failure to prompt corruption plus a 5-second router timeout
- Rewrote instance_qa/question_router.py so the prompt is readable again, embeds full converted schema markdown, and defaults the router model to qwen3.6-plus
- Updated instance_qa/orchestrator.py to pass resolved schema markdown into the router before falling back to legacy parsing
- Added router timeout coverage, schema-markdown prompt coverage, and an autouse test fixture that clears QWEN env vars so tests stay hermetic
- Re-ran targeted suites and the full test suite successfully

**Decisions made:**
- Use `typedb_schema_v4.converted.md` directly in the router prompt instead of raw TQL or a hand-written schema summary
- Increase the router timeout to 30 seconds to avoid silent fallback into the legacy Project-based anchor path
- Keep legacy parsing as fallback, but isolate tests from real external LLM settings by default

**Open questions:**
- Whether to add explicit router event/debug output into SSE so front-end can show the chosen route directly

### 2026-04-09 14:52 - Codex
**What was done:**
- Added a new plan for streaming existing schema retrieval trace through the instance QA SSE path
- Reused `retrieve_ontology_evidence(...)` inside `instance_qa/orchestrator.py` and attached the schema retrieval bundle to `InstanceQAResult`
- Updated `server/ontology_http_service.py` to emit `trace_anchor`, `trace_expand`, and `evidence_final` before TypeDB query stages
- Guarded the front-end so live trace events take priority over the synthetic schema playback fallback
- Re-ran stream/export/server integration tests and the full suite

**Decisions made:**
- Do not introduce a second schema retrieval pass; reuse the existing retrieval result only
- Keep the current front-end trace protocol and make the back-end instance QA stream conform to it

**Open questions:**
- Whether to do a quick browser smoke before commit or commit directly after tests

### 2026-04-09 11:45 - Codex
**What was done:**
- Added a new plan for schema-only playback in the QA focus tab
- Reworked `export/graph_export.py` so instance QA stage events only update status/summary, while graph playback is now built from schema retrieval data (`question_dsl` + `evidence_bundle`)
- Added focused regression tests proving the focus playback no longer uses TypeDB/result/reasoning stages as graph steps
- Re-ran export tests, server/integration tests, and the full suite

**Decisions made:**
- The ontology graph should visualize only entity/schema retrieval, not instance query or reasoning phases
- For instance QA, playback is built after schema evidence is ready and defaults to a non-realtime replayable sequence

**Open questions:**
- Whether to do a live browser smoke before commit or commit directly after tests

### 2026-04-09 11:22 - Codex
**What was done:**
- Added a new implementation plan file for live retrieval playback in the QA focus tab
- Added RED tests for playback controls and auto-play hooks, then updated `export/graph_export.py`
- Made instance QA stage snapshots auto-drive `replayFromSnapshot(...)` so the ontology graph now animates during retrieval
- Added focus playback controls (prev / replay / next) and kept them inside the graph focus tab only
- Re-ran export tests, server/integration tests, and the full test suite

**Decisions made:**
- Keep dynamic retrieval playback in the graph focus tab rather than polluting the answer tab
- Reuse existing SSE snapshots and playback infrastructure instead of adding new backend events

**Open questions:**
- Whether the next step should be a manual browser smoke only, or direct commit after a quick live check

### 2026-04-09 11:05 - Codex
**What was done:**
- Tightened the QA panel so Answer / Evidence / Focus each own a single job
- Removed the large customer-facing trace block from the answer tab and kept only answer text, answer mode, reasoning basis, and data gaps
- Switched the evidence tab to instance cards and kept retrieval playback under the graph focus tab
- Updated export integration tests and re-ran export, server/integration, and full-suite verification

**Decisions made:**
- Do not duplicate the same content across answer, evidence, and focus views
- Keep retrieval playback visible, but only from the graph focus tab

**Open questions:**
- Whether to commit the current branch diff as-is or split the already-pending unrelated changes first

### 2026-04-09 09:29 - Codex
**What was done:**
- Added front-end QA tabs in `export/graph_export.py`: ???? / ???? / ????
- Reworked the right panel so answer text stays in the answer tab, trace summary stays customer-readable, and key evidence / focus targets get dedicated renderers
- Added regression coverage in `tests/integration/test_definition_graph_export.py` for tab shell, answer routing, evidence cards, focus handlers, and clean trace output
- Re-ran focused export tests, server/integration tests, and the full suite

**Decisions made:**
- Keep the existing SSE contract and graph replay logic; only reorganize the front-end presentation layer
- Continue hiding TypeQL / query-plan style debug content from the customer-facing panel

**Open questions:**
- None

### 2026-04-08 11:17 - Codex
**What was done:**
- Changed config behavior so `search/intent_resolver.py` and `qa/generator.py` both use shared `QWEN_API_BASE` / `QWEN_API_KEY`
- Kept only model split: `QWEN_INTENT_MODEL` for seed selection and `QWEN_ANSWER_MODEL` for final answer generation
- Updated tests to prove intent/answer-specific base/key are ignored and re-ran focused plus full-suite verification

**Decisions made:**
- Base URL and API key stay single-source; only model names are split by task

**Open questions:**
- None

### 2026-04-08 11:07 - Codex
**What was done:**
- Added dual-model env support: `search/intent_resolver.py` now prefers `QWEN_INTENT_*`, `qa/generator.py` now prefers `QWEN_ANSWER_*`, both still fallback to shared `QWEN_*`
- Added RED/GREEN regression tests for intent-specific and answer-specific env precedence
- Re-ran focused search/generator tests and the full suite

**Decisions made:**
- Keep backward compatibility with existing `QWEN_*` env vars while enabling separate models for intent routing and final answer generation

**Open questions:**
- Which exact answer model to pin in env for production

### 2026-04-08 10:36 - Codex
**What was done:**
- Reworked `instance_qa/trace_summary_builder.py` to output compact/expanded customer-facing summaries with Chinese business labels, data gaps, miss explanations, and reasoning basis
- Extended `InstanceQAResult`, wired `trace_summary_ready` in SSE, and included `trace_summary` in `answer_done`
- Reworked `export/graph_export.py` so the QA panel renders trace summaries instead of raw query-log text while preserving playback/status hooks
- Added/updated trace-summary coverage in instance/server/integration tests and re-ran targeted plus full-suite verification

**Decisions made:**
- Keep compact trace visible by default and put detailed sections behind a single expanded details block
- Stop using raw TypeQL/debug text as the customer-facing trace source; keep stage events only for status/playback needs

**Open questions:**
- Whether to commit the current trace-summary/UI changes now or do one more live browser smoke with a real dataset first

### %s - Codex
**What was done:**
- Reviewed Task 2 code quality for instance_qa/trace_summary_builder.py and tests/instance_qa/test_trace_summary_builder.py
- Re-ran pytest tests/instance_qa/test_trace_summary_builder.py -q and confirmed 6 passed
- Verified compact evidence selection drops useful attributes for realistic business_keys-only inputs
- Verified compact totals ignore omitted_entities overflow and can undercount true hits

**Decisions made:**
- Review result: CHANGES_REQUESTED for Task 2 code quality

**Open questions:**
- None

### 2026-04-07 21:04 - Codex
**What was done:**
- Reviewed Task 2 spec compliance for instance_qa/trace_summary_builder.py and tests/instance_qa/test_trace_summary_builder.py
- Verified compact key evidence now caps item lists, preserves total counts, and limits per-instance fields
- Ran pytest tests/instance_qa/test_trace_summary_builder.py -q and confirmed 6 passed

**Decisions made:**
- Review result: PASS for Task 2 spec compliance

**Open questions:**
- None

### 2026-04-07 20:43 - Codex
**What was done:**
- Re-reviewed Task 1 spec compliance for instance_qa/trace_summary_builder.py and tests/instance_qa/test_trace_summary_builder.py
- Verified updated trace summary output uses business-facing labels and compact/expanded-only sections
- Ran pytest tests/instance_qa/test_trace_summary_builder.py -q and confirmed 2 passed
- Printed a sample build_trace_summary(...) result to confirm the serialized output no longer exposes raw enum/debug values for the covered case

**Decisions made:**
- Review result: PASS for Task 1 spec compliance after fixes

**Open questions:**
- None

### 2026-04-07 20:38 - Codex
**What was done:**
- Reviewed Task 1 spec compliance for instance_qa/trace_summary_builder.py and tests/instance_qa/test_trace_summary_builder.py
- Checked plan requirements for deterministic builder, compact/expanded-only structure, business-facing fields, and TDD coverage
- Ran pytest tests/instance_qa/test_trace_summary_builder.py -q and confirmed 1 passed

**Decisions made:**
- Review result: CHANGES_REQUESTED for Task 1 spec compliance

**Open questions:**
- None

### 2026-04-07 18:44 - Codex
**What was done:**
- Added evidence models, evidence subgraph builder, schema-instance aligner, evidence bundle builder, prompts, and LLM answer context builder
- Integrated the instance generator with evidence-driven prompts and wired orchestrator/service to emit `evidence_bundle_ready` and `llm_answer_context_ready`
- Added and updated instance/server/integration/generator tests for the new evidence-driven path
- Ran `pytest tests/instance_qa -q`, `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`, and `pytest tests -q`

**Decisions made:**
- Keep backend responsibility focused on evidence collection/structuring and let the LLM do final reasoning under prompt constraints
- Preserve full matched instance rows with attribute names and iid in evidence payloads rather than pre-filtering attributes in the backend
- Keep the old template answer as fallback while moving the main instance-answer path to evidence-driven prompts

**Open questions:**
- Whether to commit the full evidence-driven diff now or continue with more UX/prompt refinements first

### 2026-04-07 14:29 - Codex
**What was done:**
- Reproduced the backend `????` summary issue and rewrote `build_instance_template_answer(...)` with clean Chinese fallback text
- Added PoDPosition propagation rules so Room event impact analysis can expand through `PoDPosition -> PoD` and `PoDPosition -> WorkAssignment`
- Added planner/server regression coverage for the PoDPosition bridge and updated answer-summary assertions
- Ran `pytest tests/qa/test_template_answering.py -q`, `pytest tests/instance_qa -q`, `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`, and `pytest tests -q`

**Decisions made:**
- Treat the `????` output as a backend template corruption issue, not a frontend rendering issue
- Keep propagation controlled by backend-maintained event profiles and extend the MVP with the PoDPosition bridge instead of free-form query expansion

**Open questions:**
- Whether to commit the current branch diff now or continue with more real-dataset smoke checks first

### 2026-04-03 09:17 - Codex
**What was done:**
- Finished Task 8 integration fixes for the instance QA stream path, including orchestrator, generator fallback text, and stream tests
- Added front-end handlers for `question_parsed` / `question_dsl` / `fact_query_planned` / `typedb_query` / `typedb_result` / `reasoning_done`
- Added graph export regression coverage for instance QA stage handlers
- Repaired `qa/template_answering.py` trace wording regression found by full-suite verification
- Ran `pytest tests/instance_qa -q`, `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`, and `pytest tests -q`

**Decisions made:**
- Keep the existing `/api/qa/stream` entrypoint and replace its backend with the TypeDB-backed instance QA orchestrator
- Surface instance QA stages in the existing UI via status/evidence/trace updates instead of creating a separate panel
- Preserve controlled backend-generated TypeQL and keep LLM limited to summarization

**Open questions:**
- Whether to split the current working tree changes into separate Task 8 / Task 9 commits now or squash them later

### 2026-03-24 21:01 - Codex
**What was done:**
- Read SESSION_LOG and repo structure to restore context
- Inspected CLI, pipeline, parser, graph builder/exporter, server, search, QA modules, tests, and docs plans
- Ran `python -m cloud_delivery_ontology_palantir.cli --help`
- Ran `pytest tests -q` and got `80 passed`
- Verified the main sample `typedb_schema_v4.tql` currently resolves to `ttypedb_schema_v4.converted.md` with `21` object types and `41` relations

**Decisions made:**
- Treat the repo's current center as deterministic ontology-definition graph build/serve, with optional Qwen-backed intent resolution and answer generation layered on top
- Use `typedb_schema_v4.tql` or `ttypedb_schema_v4.converted.md` as the primary local sanity input pair

**Open questions:**
- None

### 2026-03-24 20:44 - Codex
**What was done:**
- Fast-forward merged worktree `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp` commit `6ca862a` into `codex/main2`
- Brought over the deterministic `.tql -> .md` conversion pipeline, renderer/test updates, skill files, sample schema files, and graph UI changes
- Ran `pytest tests -q` in `D:/????/AI?????/??????/palantir_mvp` and got `80 passed`

**Decisions made:**
- Kept editor metadata directories (`.idea/`) out of the merge
- Merged into the local main worktree without deleting the source worktree

**Open questions:**
- None

### 2026-03-24 19:46 - Codex
**What was done:**
- Added RED coverage in `tests/integration/test_definition_graph_export.py` for ungrouped object types so node labels and detail popups no longer expose fallback group text
- Updated `export/graph_export.py` so ungrouped object nodes render with name-only labels and omit the group chip in the floating detail card
- Preserved grouped-object behavior and internal layout grouping logic for grouped nodes
- Ran `pytest tests/integration/test_definition_graph_export.py -q` and got `13 passed`
- Ran `pytest tests -q` and got `80 passed`

**Decisions made:**
- Handle the requirement purely in the export/render layer instead of changing parser or graph-model semantics
- Keep no-group objects internally layoutable while removing no-group display text from the UI

**Open questions:**
- None

### 2026-03-24 19:17 - Codex
**What was done:**
- Added RED regression coverage for attribute terminology drift between entity labels and key-property labels in `tests/pipelines/test_input_file_resolver.py`
- Updated `pipelines/tql_schema_renderer.py` attribute business translations so building / PoDPosition / shipment / activity / crew / work-assignment / placement-plan properties now align with the updated entity wording
- Updated fallback token translations for the same business vocabulary to reduce future drift in deterministic rendering
- Ran `pytest tests/pipelines/test_input_file_resolver.py -q` and got `10 passed`
- Ran `pytest tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `12 passed`
- Ran `pytest tests -q` and got `78 passed`

**Decisions made:**
- Keep entity and attribute terminology synchronized in renderer code instead of patching generated markdown by hand
- Preserve the zero-LLM deterministic `.tql -> .md` conversion path while tightening business vocabulary consistency

**Open questions:**
- Whether `plan_status` should stay generic as `????` or also become entity-specific for plan entities

### 2026-03-24 18:04 - Codex
**What was done:**
- Rewrote `tests/pipelines/test_input_file_resolver.py` corrupted assertion strings with parser-safe UTF-8 escape literals
- Re-verified deterministic `.tql -> .converted.md` rendering expectations for Object Types headings, Link Types business descriptions, and updated object labels
- Ran `pytest tests/pipelines/test_input_file_resolver.py -q` and got `9 passed`
- Ran `pytest tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `12 passed`
- Ran `pytest tests -q` and got `77 passed`

**Decisions made:**
- Keep the runtime `.tql -> .md` path deterministic with zero LLM participation
- Use escaped assertion literals in tests to avoid Windows terminal encoding corruption

**Open questions:**
- Whether to further slim leftover legacy docs/tests now that the deterministic conversion path is stable

### 2026-03-24 17:41 - Codex
**What was done:**
- Removed `enhance_tql_markdown(...)` from the active `.tql -> .converted.md` conversion path so runtime conversion is now fully deterministic and does not call the LLM
- Updated renderer reference descriptions so `REFERENCES` now uses business wording (`??`) for `PlacementPlan`, `DecisionRecommendation`, and `ConstraintViolation`
- Added and passed regression tests proving deterministic conversion no longer calls the enhancer and that updated object type business labels render correctly
- Re-ran `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `23 passed`
- Re-ran `pytest tests -q` and got `85 passed`
- Verified real conversion now emits `PlacementPlan REFERENCES Building???????????`, `ConstraintViolation REFERENCES PoD???????PoD`, and `DecisionRecommendation REFERENCES PlacementPlan?????????????`

**Decisions made:**
- The runtime `.tql -> .md` path now has zero LLM participation; only deterministic extractor/renderer code is used
- `REFERENCES` is the only verb allowed to vary by business semantics; other verbs remain fixed-template descriptions

**Open questions:**
- Whether `ConstraintViolation REFERENCES ...` should stay as `??` or be adjusted to `??` for some targets

### 2026-03-24 17:28 - Codex
**What was done:**
- Added RED coverage for updated object type business labels in the real `typedb_schema_v4.tql` conversion path
- Updated `pipelines/tql_schema_renderer.py` entity Chinese labels to use: `??`, `PoD??`, `???`, `????`, `??????`, `????`, `??SLA`, `???`, `????`, `??????`
- Verified the new labels also flow through Link Types business descriptions automatically where those object types are referenced
- Re-ran `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `23 passed`
- Re-ran `pytest tests -q` and got `85 passed`
- Verified real `ttypedb_schema_v4.converted.md` contains all requested updated labels

**Decisions made:**
- Object type naming is still controlled deterministically in the renderer mapping table, not by prompt
- Activity-related object labels now consistently use `??` rather than `??`

**Open questions:**
- Whether to align some attribute labels (for example `activity_*`) from `??` to `??` as well

### 2026-03-24 17:12 - Codex
**What was done:**
- Added RED coverage for `template-dependency-link` semantic rendering and Link Types business-description formatting
- Updated `pipelines/tql_schema_renderer.py` so `template-dependency-link` now emits fixed semantic triples `ActivityDependencyTemplate DEFINES ActivityInstance` and `ActivityInstance DEPENDS_ON ActivityInstance`
- Replaced Link Types descriptions with deterministic business Chinese phrasing in the form `??????????`
- Aligned `pod-schedule` wording from `PoD??` to `PoD??`
- Verified real conversion now emits `RoomMilestone CONSTRAINS Room??????????`, `ActivityDependencyTemplate DEFINES ActivityInstance?????????????`, and `PoDSchedule APPLIES_TO PoD?PoD?????PoD`
- Re-ran `pytest tests/ontology/test_definition_markdown_parser.py tests/pipelines/test_input_file_resolver.py tests/pipelines/test_tql_markdown_enhancer.py -q` and got `21 passed`
- Re-ran `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `22 passed`
- Re-ran `pytest tests -q` and got `84 passed`

**Decisions made:**
- `template-dependency-link` is rendered by fixed semantic triples instead of raw predecessor/successor template references
- Link Types descriptions no longer expose raw TypeDB relation metadata; they now use deterministic Chinese business phrases

**Open questions:**
- Whether to continue adding more relation-specific Chinese wording overrides beyond the current generic verb-based phrasing

### 2026-03-24 16:07 - Codex
**What was done:**
- Added a regression test locking business-semantic relation direction for `room-milestone-constraint` and `floor-room-milestone-aggregation`
- Updated `pipelines/tql_schema_renderer.py` so relation rendering now resolves direction via explicit relation-role overrides first, then role-prefix semantic rules, then declared-order fallback
- Verified real conversion now emits `RoomMilestone CONSTRAINS Room`, `FloorMilestone CONSTRAINS Floor`, and `FloorMilestone AGGREGATES RoomMilestone`
- Re-ran `pytest tests/ontology/test_definition_markdown_parser.py tests/pipelines/test_input_file_resolver.py tests/pipelines/test_tql_markdown_enhancer.py -q` and got `20 passed`
- Re-ran `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `21 passed`
- Re-ran `pytest tests -q` and got `83 passed`

**Decisions made:**
- Constraint and aggregation relations are no longer rendered by raw declaration order when business semantics imply the opposite direction
- Relation rendering order now prioritizes explicit relation-specific rules over generic prefix heuristics

**Open questions:**
- Whether to add more explicit relation-direction overrides beyond the current constraint and aggregation cases

### 2026-03-24 15:58 - Codex
**What was done:**
- Wrote `docs/plans/2026-03-24-object-types-hard-constraint.md`
- Added RED tests for the new flat Object Types markdown contract and new parser format
- Reworked `pipelines/tql_schema_extractor.py` to use source-file stem titles, preserve the first `define` boundary correctly, and carry optional structured metadata (`group` / `zh` / `semantic`)
- Reworked `pipelines/tql_schema_models.py` and `pipelines/tql_schema_renderer.py` so TQL conversion now emits deterministic hard-constrained Object Types markdown with `# typedb_schema_v4`, `## Object Types????`, `## Link Types????`, flat entity output by default, no synthetic grouping, omitted semantic sections by default, and strict `?????` key-property lines
- Reworked `ontology/definition_markdown_parser.py` to parse both legacy markdown and the new flat format
- Updated `pipelines/tql_markdown_enhancer.py` so Object Types are no longer LLM-enhanced; only Link Types are enhanced in the new format
- Updated pipeline/parser/enhancer tests to match the new contract
- Verified `pytest tests/ontology/test_definition_markdown_parser.py tests/pipelines/test_input_file_resolver.py tests/pipelines/test_tql_markdown_enhancer.py -q` -> `19 passed`
- Verified `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` -> `20 passed`
- Verified `pytest tests -q` -> `82 passed`
- Verified real `typedb_schema_v4.tql -> ttypedb_schema_v4.converted.md` now starts with the new headings and parses successfully with `21` objects / `42` relations
- Verified live `serve-ontology --input-file typedb_schema_v4.tql` smoke on port `8772`; `/api/graph` returned `200` with `63` elements

**Decisions made:**
- Object Types formatting is now enforced deterministically in code rather than by prompt
- Abstract entities are treated as grouping metadata and are not rendered as standalone object types in the new output
- Link Types enhancement remains available, but Object Types enhancement is disabled to preserve hard constraints

**Open questions:**
- Whether to add another deterministic pass for Link Types wording, or leave Link Types enhancement prompt-driven for now

### 2026-03-24 14:12 - Codex
**What was done:**
- Reproduced the chunked enhancement failure and traced it to LLM wrapper text plus schema-drifting chunk output
- Added regression tests for fenced-markdown extraction and deterministic projection of object/relation chunks back onto the skeleton shape
- Updated `pipelines/tql_markdown_enhancer.py` to strip fenced markdown from explanatory responses and to project enhanced chunks back onto the parser-safe skeleton before validation
- Re-ran `pytest tests/pipelines/test_tql_markdown_enhancer.py -v` and got `6 passed`
- Re-ran focused regression tests and got `19 passed`
- Re-ran `pytest tests -q` and got `80 passed`
- Verified real `typedb_schema_v4.tql -> ttypedb_schema_v4.converted.md` now uses enhancement (`same_as_skeleton=False`) and still parses with `22` object types and `42` relations
- Verified live `serve-ontology --input-file typedb_schema_v4.tql` smoke on port `8771`; `/api/graph` returned `200` with `64` elements

**Decisions made:**
- Kept the runtime flow as deterministic skeleton + chunked LLM enhancement, but added deterministic post-projection so the LLM can improve wording without being allowed to break parser shape
- Preserved exact object names, key property keys, and relation triples from the skeleton while allowing descriptions to be enhanced

**Open questions:**
- Whether the current enhanced wording quality is good enough to keep, or needs another prompt pass

### 2026-03-23 22:04 - Codex
**What was done:**
- Executed the tql-md-reviser skill plan in this worktree and added the new skill files under `.agents/skills/tql-md-reviser/`
- Added `tests/skills/test_tql_md_reviser.py` and expanded it to 12 passing tests covering structure anchors, parser-compatible revision output, note-label preservation, report correctness, and minimal repair scope
- Implemented `scripts/revise_tql_markdown.py` with structure anchors, traceback extraction, revision report output, and parser-safe repair behavior
- Verified `pytest tests/skills/test_tql_md_reviser.py -v` -> `12 passed`
- Verified `pytest tests -q` -> `71 passed`
- Verified real sample execution: `python .agents/skills/tql-md-reviser/scripts/revise_tql_markdown.py --tql typedb_schema_v4.tql --markdown <real-md>` -> `status=success`
- Verified `[????] ????2?????v2.revised.md` parses successfully with `22` object types, `44` relations, `18` derived metrics

**Decisions made:**
- Kept the skill as a development-assist workflow, not a runtime production dependency
- Preserved original markdown files by always writing `.revised.md` plus `.revision-report.md`

**Open questions:**
- None

### 2026-03-23 21:38 - Codex
**What was done:**
- Performed a read-only code quality review of `.agents/skills/tql-md-reviser/` and `tests/skills/test_tql_md_reviser.py`
- Ran `pytest tests/skills/test_tql_md_reviser.py -q` and confirmed `7 passed`
- Verified blocking issues: corrupted/brittle tests, invalid fallback object-group heading rendering, report credibility gap after repaired success, and label-collapsing round-trip loss

**Decisions made:**
- Review result is `CHANGES_REQUESTED`
- No repository code was modified as part of the review itself

**Open questions:**
- None

### 2026-03-23 21:27 - Codex
**What was done:**
- Added `.agents/skills/tql-md-reviser/` with `SKILL.md`, `agents/openai.yaml`, `references/parser-contract.md`, and `scripts/revise_tql_markdown.py`
- Added `tests/skills/test_tql_md_reviser.py` and extended it with regression coverage for inverse-relation pollution and non-parser repair suppression
- Implemented structure anchors, revision report generation, parser error extraction, traceback-aware minimal repair gating, and conservative relation normalization/merge logic
- Generated and verified `typedb_schema_v4.revised.md` plus `typedb_schema_v4.revision-report.md`
- Ran `pytest tests/skills/test_tql_md_reviser.py -v` and got `7 passed`
- Ran `pytest tests -q` and got `66 passed`
- Ran the real-sample skill flow on `typedb_schema_v4.tql` + `[????] ????2?????v2.md` and confirmed success (`22` objects, `44` relations)

**Decisions made:**
- Kept the skill as a development assistant only; production build/serve flow remains code-driven
- Prevented inverse duplicate relation pollution by normalizing generated relations and skipping inverse duplicates during merge
- Restricted minimal repair to parser-like syntax errors instead of mutating on arbitrary structure-anchor failures

**Open questions:**
- None

### 2026-03-23 21:14 - Codex
**What was done:**
- Executed the tql-md-reviser skill implementation plan in-session
- Added RED tests in `tests/skills/test_tql_md_reviser.py`
- Added `.agents/skills/tql-md-reviser/` with `SKILL.md`, `agents/openai.yaml`, `references/parser-contract.md`, and `scripts/revise_tql_markdown.py`
- Implemented structure-anchor scanning, parser error extraction, deterministic markdown revision, validation, and revision report output
- Verified `pytest tests/skills/test_tql_md_reviser.py -v` -> `5 passed`
- Verified real CLI run of `python .agents/skills/tql-md-reviser/scripts/revise_tql_markdown.py --tql typedb_schema_v4.tql --markdown [real md] ...` returned success and wrote `typedb_schema_v4.revised.md` plus `typedb_schema_v4.revision-report.md`
- Verified `parse_definition_markdown('typedb_schema_v4.revised.md')` succeeds with `22` object types, `66` relations, `18` derived metrics
- Ran `pytest tests -q` and got `64 passed`

**Decisions made:**
- Kept the skill as a development-assist path that produces a new `.revised.md` instead of overwriting the source markdown
- Used structure anchors plus parser validation as hard gates

**Open questions:**
- Whether to commit the new skill and the related deterministic TQL conversion work now

### 2026-03-23 20:03 - Codex
**What was done:**
- Wrote and saved `docs/plans/2026-03-23-parser-compatible-tql-conversion.md`
- Added RED/GREEN tests proving `.tql` conversion can work without Qwen env vars and still feed the existing markdown parser/build pipeline
- Added deterministic TQL schema extraction and fixed markdown rendering modules: `pipelines/tql_schema_models.py`, `pipelines/tql_schema_extractor.py`, `pipelines/tql_schema_renderer.py`
- Updated `pipelines/tql_to_markdown.py` so `convert_tql_file_to_markdown_file(...)` now renders parser-compatible markdown locally and validates it with `parse_definition_markdown(...)` before writing
- Verified real `typedb_schema_v4.tql` now converts successfully into `ttypedb_schema_v4.converted.md` with `22` object types and `42` relations
- Verified live `serve-ontology --input-file typedb_schema_v4.tql` smoke on port `8771` and `/api/graph` returned successfully with `64` elements
- Ran `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `16 passed`
- Ran `pytest tests -q` and got `59 passed`

**Decisions made:**
- Kept the Qwen API helper for direct/raw text conversion tests, but moved `.tql` file conversion onto a deterministic local extractor/renderer path
- Used parser validation as a hard gate before writing `.converted.md`

**Open questions:**
- None

### 2026-03-23 19:47 - Codex
**What was done:**
- Added a RED/GREEN regression test locking TQL conversion default timeout at `120.0` seconds
- Updated `pipelines/tql_to_markdown.py` to use `_DEFAULT_TIMEOUT_S = 120.0`
- Updated the stale CLI integration test to match the current `.md`/`.tql` serve help contract
- Ran `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `14 passed`
- Ran `pytest tests -q` and got `57 passed`
- Verified real `typedb_schema_v4.tql` conversion now completes and writes `ttypedb_schema_v4.converted.md`
- Verified direct `serve-ontology --input-file typedb_schema_v4.tql` no longer fails on HTTP timeout; it now fails later because the generated markdown does not match parser-required structure

**Decisions made:**
- Increased the default Qwen conversion timeout from `30s` to `120s`
- Kept the fix minimal: timeout only, no prompt/parser behavior change in this step

**Open questions:**
- Whether to harden TQL->Markdown generation so real schema outputs consistently satisfy `parse_definition_markdown`

### 2026-03-23 18:45 - Codex
**What was done:**
- Ran live `serve-ontology` smoke startup checks in subprocesses against temporary markdown inputs on ports `8767` and `8768`
- Verified `/ontology` and `/api/graph` both returned `200`
- Verified graph payload was non-empty for the minimal ontology smoke input (`element_count=3`, `relation_legend_count=1`)
- Verified `/api/qa/stream` emitted the full event sequence through `answer_done`
- Identified a Windows shell encoding issue when passing the repo's Chinese-named markdown file directly; switched the smoke test to ASCII temp filenames

**Decisions made:**
- Use ASCII temporary input filenames for live Windows smoke verification to avoid false negatives from shell/path encoding
- Treat the service startup smoke test as PASS based on live HTTP and SSE checks

**Open questions:**
- None

### 2026-03-23 18:41 - Codex
**What was done:**
- Reviewed commit `d4e5c83476108819c8ce827e0e6c2d84b74f5aef` for Task 4 spec compliance and code quality
- Verified `server/ontology_http_app.py` now resolves `.tql` input before parsing while preserving both original and resolved paths in app state
- Verified `cli.py` now advertises `.md or .tql` for `serve-ontology --input-file`
- Ran `pytest tests/server/test_ontology_http_app.py -v` and confirmed `8 passed`
- Ran `python -m cloud_delivery_ontology_palantir.cli serve-ontology --help` to confirm the user-facing help text

**Decisions made:**
- Marked Task 4 spec review as PASS
- Marked Task 4 code quality review as APPROVED

**Open questions:**
- None

### 2026-03-23 18:33 - Codex
**What was done:**
- Reviewed commit `8c51808d86a98a0d466333c9e6a4e35c7a56b4ff` for Task 3 spec compliance without modifying repository code
- Verified current commit state still satisfies the required `pipelines/build_ontology_pipeline.py` integration and does not modify server files
- Checked `cli.py` and confirmed build-side help still advertises markdown/TQL while CLI keeps format handling delegated to the pipeline
- Ran `pytest tests/integration/test_build_ontology_cli.py -v` in an isolated snapshot of commit `8c51808d86a98a0d466333c9e6a4e35c7a56b4ff`
- Confirmed PASS result: 3 passed

**Decisions made:**
- Marked Task 3 as PASS because the required pipeline changes remain intact, focused build CLI tests pass, and no server files were changed

**Open questions:**
- None

### 2026-03-23 18:32 - Codex
**What was done:**
- Reviewed latest commit `8c51808d86a98a0d466333c9e6a4e35c7a56b4ff` for Task 3 code quality
- Inspected `cli.py`, `pipelines/build_ontology_pipeline.py`, and the updated CLI integration tests
- Ran `pytest tests/integration/test_build_ontology_cli.py tests/pipelines/test_input_file_resolver.py -q` and got `5 passed`
- Verified the prior `serve-ontology` help-text regression is fixed while build pipeline wiring remains clean and stable

**Decisions made:**
- Review result is `APPROVED`
- No remaining blocking quality issues were found for Task 3

**Open questions:**
- None

### 2026-03-23 18:28 - Codex
**What was done:**
- Reviewed commit `cacb7fb8c71beecd1946d5ed4d8a50960bacf8bc` for Task 3 spec compliance without modifying repository code
- Verified the commit changes only `pipelines/build_ontology_pipeline.py` and `cli.py`, with no server-file modifications
- Confirmed pipeline now resolves input to markdown, reads/parses the resolved path, and returns `resolved_input_file` plus conditional `converted_markdown_file`
- Confirmed CLI help text now says markdown or TQL and CLI still delegates format handling to the pipeline
- Ran `pytest tests/integration/test_build_ontology_cli.py -v` in an isolated snapshot of commit `cacb7fb8c71beecd1946d5ed4d8a50960bacf8bc`
- Confirmed PASS result: 2 passed

**Decisions made:**
- Marked Task 3 as PASS because the commit satisfies the required pipeline/CLI changes, leaves server files untouched, and passes the focused integration tests

**Open questions:**
- None

### 2026-03-23 18:28 - Codex
**What was done:**
- Reviewed commit `cacb7fb8c71beecd1946d5ed4d8a50960bacf8bc` for Task 3 code quality
- Inspected `pipelines/build_ontology_pipeline.py`, `cli.py`, and related CLI tests
- Ran `pytest tests/integration/test_build_ontology_cli.py tests/pipelines/test_input_file_resolver.py -q` and got `4 passed`
- Verified build pipeline wiring to `resolve_input_to_markdown(...)` is clean and stable
- Verified `serve-ontology` still reads markdown directly in `server/ontology_http_app.py`, so the new `.tql` CLI help overstates current support

**Decisions made:**
- Review result is `CHANGES_REQUESTED`
- The only blocking issue is the user-facing CLI help regression for `serve-ontology`

**Open questions:**
- None

### 2026-03-23 18:03 - Codex
**What was done:**
- Reviewed commit `27e02b0df488efe7fc18a35775238c9aa5203f82` for Task 2 spec compliance without modifying repository code
- Verified the commit only adds `pipelines/tql_to_markdown.py` and `pipelines/input_file_resolver.py`, with no `build/server/cli` changes
- Ran `pytest tests/pipelines/test_input_file_resolver.py -v` in an isolated snapshot of commit `27e02b0df488efe7fc18a35775238c9aa5203f82`
- Confirmed focused tests pass: 2 passed

**Decisions made:**
- Marked Task 2 as FAIL because `pipelines/tql_to_markdown.py` falls back to a default model instead of requiring `QWEN_MODEL`, so missing configuration does not fully raise the required clear error

**Open questions:**
- None

### 2026-03-23 18:02 - Codex
**What was done:**
- Reviewed latest commit `27e02b0df488efe7fc18a35775238c9aa5203f82` for Task 2 code quality
- Re-ran `pytest tests/pipelines/test_input_file_resolver.py -q` and got `2 passed`
- Verified `QWEN_MODEL` now falls back to the default model instead of being mandatory
- Spot-checked the converter path and default-model behavior for obvious regression risk

**Decisions made:**
- Review result is `APPROVED`
- No remaining blocking quality issues were found in the Task 2 converter/resolver implementation

**Open questions:**
- None

### 2026-03-23 17:59 - Codex
**What was done:**
- Reviewed commit `d54bda9bcea5796ff037fd989a799449c9635225` for Task 2 spec compliance without modifying repository code
- Verified the commit only adds `pipelines/tql_to_markdown.py` and `pipelines/input_file_resolver.py`, with no `build/server/cli` changes
- Checked the new TQL conversion and input resolver implementations against the Task 2 contract
- Ran `pytest tests/pipelines/test_input_file_resolver.py -v` in an isolated snapshot of commit `d54bda9bcea5796ff037fd989a799449c9635225`
- Confirmed PASS result: 2 passed

**Decisions made:**
- Marked Task 2 as PASS because the commit satisfies the required new modules, behaviors, file output contract, and focused test pass without touching forbidden areas

**Open questions:**
- None

### 2026-03-23 17:58 - Codex
**What was done:**
- Reviewed commit `d54bda9bcea5796ff037fd989a799449c9635225` for Task 2 code quality
- Inspected `pipelines/input_file_resolver.py` and `pipelines/tql_to_markdown.py`
- Ran `pytest tests/pipelines/test_input_file_resolver.py -q` and got `2 passed`
- Verified the converter currently raises `RuntimeError: Missing required environment variable: QWEN_MODEL` when only `QWEN_API_BASE` and `QWEN_API_KEY` are configured

**Decisions made:**
- Review result is `CHANGES_REQUESTED`
- The main blocking issue is the unnecessary required-`QWEN_MODEL` constraint

**Open questions:**
- None

### 2026-03-23 17:51 - Codex
**What was done:**
- Reviewed latest commit `75697a27599a92f738969e039bdfd43ae734dc0f` for Task 1 code quality
- Re-ran `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q` and got `4 failed, 8 passed`
- Verified the CLI RED fixture now reuses parser-valid markdown from the real repo sample so the remaining failure is due to missing resolver wiring, not bad test data
- Confirmed no new overcoupling or missing-rule issues in the current Task 1 tests

**Decisions made:**
- Review result is `APPROVED`
- Current Task 1 tests are minimal enough and fail for the intended RED reasons

**Open questions:**
- None

### 2026-03-23 17:51 - Codex
**What was done:**
- Reviewed commit `75697a27599a92f738969e039bdfd43ae734dc0f` for Task 1 spec compliance without modifying code
- Verified the latest commit only changes `tests/integration/test_build_ontology_cli.py`; current HEAD still keeps Task 1 tests within the allowlist of three files
- Confirmed current HEAD still covers markdown passthrough, tql-to-converted-md resolution, CLI pipeline-level resolution before build, and app-level resolution before graph load
- Ran `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -v`
- Confirmed RED result: 4 failed, 8 passed

**Decisions made:**
- Marked Task 1 as PASS because the test-only state remains within allowed files, preserves all four required RED coverage points, and does not touch production code

**Open questions:**
- None

