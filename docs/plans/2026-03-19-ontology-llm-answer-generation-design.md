# Ontology LLM Answer Generation Design

**Date:** 2026-03-19

## Goal
Add a Qwen2.5-32B generation layer on top of the existing ontology retrieval pipeline so the system can turn retrieved graph facts into a concise, business-readable answer while preserving deterministic traceability and fallback behavior.

## Existing Context
The current QA flow already does three important things well:
1. `OntologyQueryEngine` retrieves structured graph evidence and `SearchTrace`.
2. `qa/template_answering.py` produces a deterministic fallback answer plus a concise `trace_report`-style path summary.
3. `/api/qa/stream` already streams retrieval events to the front end, and the front end already knows how to animate them.

The new design must preserve those strengths. Retrieval remains the source of truth. LLM generation is an interpretation layer, not a new fact source.

## Chosen Approach
Use a retrieval-then-generation architecture:
- retrieval continues to produce `OntologyEvidenceBundle`
- a new `qa/generator.py` converts deduped trace edges into compact factual lines
- Qwen2.5-32B consumes only those factual lines plus the user question
- the server streams model output as `answer_delta` events after the existing retrieval events
- `answer_done` carries both the final LLM answer and the local deterministic `trace_report`
- if generation is disabled or fails, the system falls back to the existing template answer with no blank state

## Why This Approach
This is the lowest-risk upgrade because it keeps retrieval, graph playback, and provenance intact. The model is only allowed to summarize retrieved facts. It does not decide what the ontology contains.

## Data Flow
1. User asks a question.
2. `retrieve_ontology_evidence()` resolves seeds and traverses the graph.
3. `build_template_answer()` builds the deterministic fallback answer and the trace-oriented support text.
4. `qa/generator.py` formats deduped fact lines such as:
   - `项目(Project) [包含] 机房里程碑(RoomMilestone)`
   - `约束冲突(ConstraintViolation) [引用] 落位方案(PlacementPlan)`
5. If Qwen config is present, the generator sends those facts to the OpenAI-compatible streaming API.
6. The server emits existing retrieval SSE events first, then emits `answer_delta` as chunks arrive, then emits `answer_done` with:
   - legacy `answer`
   - new `answer_text`
   - new `trace_report`
   - `used_fallback`
7. The front end shows the streaming answer in the main answer card and reveals `trace_report` under a "逻辑溯源" section.

## Prompt Design
### Role
The model is instructed to act as a senior cloud-delivery planning expert and ontology reasoning assistant.

### Context Contract
Only the following are sent:
- user question
- deduped fact list derived from retrieval edges
- explicit instructions to preserve entity strings exactly as provided

### Guardrails
- do not invent relations
- if facts do not support a conclusion, say so
- explain the causal chain only from the supplied facts
- keep answer under 200 Chinese characters when possible
- preserve all entity names exactly in `中文名(ID)` format

### Provenance Rule
`trace_report` remains fully local and deterministic. The model never rewrites it. This preserves an objective support trail even if the natural-language summary is imperfect.

## Generator Module Design
Create `D:/学习资料/AI应用使能组/本体检索代码/palantir_mvp/qa/generator.py`.

### Responsibilities
- detect whether Qwen config is available
- derive deduped factual lines from `OntologyEvidenceBundle`
- stream answer chunks from the OpenAI-compatible endpoint
- accumulate the final `answer_text`
- fall back to the existing template answer on configuration absence, timeout, API failure, or empty fact list

### Suggested API
- `GeneratorConfig`
- `GeneratorChunk`
- `GeneratorResult`
- `iter_generated_answer(question, bundle, fallback_answer) -> Iterator[GeneratorChunk | GeneratorResult]`

The exact shapes may vary, but the generator must expose a stream-friendly contract so the SSE layer can forward chunks directly without buffering the whole answer first.

## Server Integration Design
### `server/ontology_http_app.py`
Keep retrieval first:
- compute `bundle`
- compute `fallback_answer`
- pass both into the SSE service layer

### `server/ontology_http_service.py`
Extend the SSE protocol:
- existing retrieval events stay unchanged
- new `answer_delta` carries:
  - `delta`
  - `answer_text_so_far`
- `answer_done` carries:
  - legacy `answer`
  - new `answer_text`
  - new `trace_report`
  - `used_fallback`
  - existing evidence metadata

This is a no-loss upgrade. Old clients can still read `answer`. New clients can prefer `answer_text`.

## Front-End Rendering Design
### Main Answer Card
The existing answer card becomes the prominent answer surface. It should update incrementally as `answer_delta` events arrive.

### Logic Trace Section
Below the answer card, add a collapsible "逻辑溯源" section populated from `trace_report` after `answer_done` arrives.

### Compatibility
- if only `answer` exists, render it
- if `answer_text` exists, prefer it
- evidence timeline and graph highlight logic remain untouched

## Testing Strategy
### Unit: `tests/qa/test_generator.py`
Must cover:
- streaming success path with mocked OpenAI chunks
- no-facts path returning deterministic fallback or fixed no-association sentence
- missing config path returning fallback
- mid-stream exception path returning fallback
- **entity-name protection**: assert `answer_text` contains the exact `中文名(ID)` strings supplied by the bundle/facts

### Server: `tests/server/test_ontology_http_app.py`
Mock the OpenAI stream with `AsyncMock` or an equivalent async iterator wrapper. Assert:
- retrieval event order remains unchanged
- `answer_delta` appears after retrieval events
- `answer_done` includes `answer`, `answer_text`, `trace_report`, `used_fallback`

### Front End: `tests/integration/test_definition_graph_export.py`
Assert exported HTML contains:
- answer streaming handler for `answer_delta`
- prominent answer area
- collapsible "逻辑溯源" area
- `answer_done` handling that renders `trace_report`

## Performance Strategy
The design optimizes perceived latency rather than pretending the model is instantaneous:
- graph retrieval events appear first (visual first byte)
- model output starts streaming as soon as the first chunk arrives
- if the model is slow, the user still sees the graph and evidence pipeline already moving

The 3-second requirement is treated as a best-effort streaming-start target, not a hard guarantee, because external model latency is not fully under local control.

## Dependencies
The environment currently has `httpx` and `fastapi`, but not `openai`. The implementation must install and pin `openai` in the project dependency surface used by this repo.

## Risks and Controls
1. **Model rewrites entity labels**
   - control: prompt explicitly forbids rewrites
   - control: tests assert entity-name preservation
2. **Model unavailable or slow**
   - control: deterministic fallback answer remains available
3. **Streaming protocol breaks old UI**
   - control: keep existing retrieval events and legacy `answer` field
4. **LLM output drifts away from evidence**
   - control: send only deduped fact lines, not raw prose
   - control: keep local `trace_report` as the authoritative support artifact
