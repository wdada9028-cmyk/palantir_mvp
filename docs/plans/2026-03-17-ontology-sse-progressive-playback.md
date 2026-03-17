# Ontology SSE Progressive Playback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the ontology HTTP/SSE QA experience from instant final-state rendering to true progressive retrieval playback with automatic pacing, incremental evidence reveal, and manual replay controls.

**Architecture:** The backend keeps emitting SSE, but now each retrieval step carries stable playback metadata (`step_title`, incremental highlight sets, focus sets) and is paced with real delays inside the stream generator. The front end adds a snapshot-based `PlaybackController` that consumes live SSE events, auto-plays them with progressive dimming and camera follow, queues them while paused, and supports previous/next/replay without recomputing graph state.

**Tech Stack:** Python 3.11+, FastAPI, `StreamingResponse`, deterministic ontology retrieval, Cytoscape.js, inline browser JavaScript in `export/graph_export.py`, `pytest`, `fastapi.testclient`, no LLM.

**Repository note:** This workspace has no `.git` directory. Replace normal commit steps with a `SESSION_LOG.md` checkpoint update after each completed task.

---

### Task 1: Extend retrieval step models for progressive playback metadata

**Files:**
- Modify: `search/ontology_query_models.py`
- Modify: `search/ontology_query_engine.py`
- Test: `tests/search/test_ontology_query_engine.py`

**Step 1: Write the failing test**

Add this test to `tests/search/test_ontology_query_engine.py`:

```python
def test_retrieve_ontology_evidence_includes_progressive_playback_fields():
    graph = OntologyGraph(metadata={'title': '??'})
    graph.add_object(
        OntologyObject(
            id='object_type:PoD',
            type='ObjectType',
            name='PoD',
            attributes={'group': '4.3 ??????', 'chinese_description': '?????'},
        )
    )
    graph.add_object(
        OntologyObject(
            id='object_type:ArrivalPlan',
            type='ObjectType',
            name='ArrivalPlan',
            attributes={'group': '4.6 ??????', 'chinese_description': '????'},
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id='object_type:ArrivalPlan',
            target_id='object_type:PoD',
            relation='APPLIES_TO',
            attributes={'description': '??????? PoD'},
        )
    )

    result = retrieve_ontology_evidence(graph, 'PoD ?????')
    anchor_step = next(step for step in result.highlight_steps if step.action == 'anchor_node')
    expand_step = next(step for step in result.highlight_steps if step.action == 'expand_neighbors')

    assert anchor_step.step_title == '??????'
    assert anchor_step.new_node_ids == ['object_type:PoD']
    assert anchor_step.focus_node_ids == ['object_type:PoD']
    assert 'object_type:ArrivalPlan' in expand_step.new_node_ids
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/search/test_ontology_query_engine.py::test_retrieve_ontology_evidence_includes_progressive_playback_fields -v`
Expected: FAIL because `RetrievalStep` does not yet expose playback metadata.

**Step 3: Write minimal implementation**

In `search/ontology_query_models.py`, extend `RetrievalStep` to include:

```python
@dataclass(slots=True)
class RetrievalStep:
    action: str
    message: str
    step_title: str = ''
    node_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    new_node_ids: list[str] = field(default_factory=list)
    new_edge_ids: list[str] = field(default_factory=list)
    focus_node_ids: list[str] = field(default_factory=list)
    focus_edge_ids: list[str] = field(default_factory=list)
```

In `search/ontology_query_engine.py`:
- compute cumulative active node/edge sets per step
- compute incremental `new_node_ids` / `new_edge_ids`
- set stable Chinese step titles:
  - `anchor_node` ? `??????`
  - `expand_neighbors` ? `??????`
  - `filter_nodes` ? `??????`
  - `focus_subgraph` ? `??????`
- set `focus_node_ids` / `focus_edge_ids` to the step's newly relevant region

**Step 4: Run test to verify it passes**

Run: `pytest tests/search/test_ontology_query_engine.py::test_retrieve_ontology_evidence_includes_progressive_playback_fields -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 1 completion.

### Task 2: Make the SSE generator emit true paced progressive events

**Files:**
- Modify: `server/ontology_http_service.py`
- Modify: `server/ontology_http_app.py`
- Test: `tests/server/test_ontology_http_app.py`

**Step 1: Write the failing test**

Add this to `tests/server/test_ontology_http_app.py`:

```python
from cloud_delivery_ontology_palantir.qa.template_answering import build_template_answer
from cloud_delivery_ontology_palantir.search.ontology_query_engine import retrieve_ontology_evidence
from cloud_delivery_ontology_palantir.server.ontology_http_service import iter_qa_events


def test_iter_qa_events_applies_progressive_sleep_schedule(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)
    app = create_app(input_file=input_file)
    bundle = retrieve_ontology_evidence(app.state.graph, 'PoD ?????')
    answer = build_template_answer(bundle)
    sleeps: list[float] = []

    events = list(iter_qa_events(bundle, answer, sleep_fn=sleeps.append))

    assert 'event: anchor_node' in events[0]
    assert any('step_title' in event for event in events)
    assert sleeps[:3] == [0.5, 0.5, 0.5]
    assert 0.7 in sleeps
    assert 'event: answer_done' in events[-1]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py::test_iter_qa_events_applies_progressive_sleep_schedule -v`
Expected: FAIL because `iter_qa_events()` does not pace events or accept `sleep_fn`.

**Step 3: Write minimal implementation**

In `server/ontology_http_service.py`:
- change `iter_qa_events()` signature to accept `sleep_fn: Callable[[float], None] | None = None`
- default `sleep_fn` to `time.sleep`
- emit step payloads with the new fields:
  - `step_title`
  - `new_node_ids`
  - `new_edge_ids`
  - `focus_node_ids`
  - `focus_edge_ids`
- call `sleep_fn(0.5)` after each non-final non-evidence step
- call `sleep_fn(0.7)` after each `evidence` event
- emit `answer_done` only after all prior sleeps/steps have completed

Keep `server/ontology_http_app.py` routing minimal; it should continue using `StreamingResponse(iter_qa_events(...), media_type='text/event-stream')`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py::test_iter_qa_events_applies_progressive_sleep_schedule -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 2 completion.

### Task 3: Add playback controls and a front-end PlaybackController shell

**Files:**
- Modify: `export/graph_export.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

Add this to `tests/integration/test_definition_graph_export.py`:

```python
def test_exported_html_contains_progressive_playback_controls_and_controller(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-playback-pause' in text
    assert 'qa-playback-prev' in text
    assert 'qa-playback-next' in text
    assert 'qa-playback-replay' in text
    assert 'PlaybackController' in text
    assert 'playNextQueuedEvent' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_progressive_playback_controls_and_controller -v`
Expected: FAIL because the HTML has no playback controls or controller object.

**Step 3: Write minimal implementation**

In `export/graph_export.py`:
- add control buttons into the QA panel:
  - `id="qa-playback-pause"`
  - `id="qa-playback-prev"`
  - `id="qa-playback-next"`
  - `id="qa-playback-replay"`
- add a visible step title/status slot
- define a `PlaybackController` object with state fields:
  - `receivedEvents`
  - `pendingQueue`
  - `snapshots`
  - `currentSnapshotIndex`
  - `isPaused`
  - `isFinished`
- stub methods:
  - `enqueueEvent(eventType, payload)`
  - `playNextQueuedEvent()`
  - `pause()` / `resume()`
  - `goToPreviousStep()`
  - `goToNextStep()`
  - `replay()`

Wire button listeners to those methods.

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_progressive_playback_controls_and_controller -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 3 completion.

### Task 4: Implement snapshot-based progressive dimming, camera follow, and delayed final answer

**Files:**
- Modify: `export/graph_export.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

Add this to `tests/integration/test_definition_graph_export.py`:

```python
def test_exported_html_contains_snapshot_replay_and_delayed_answer_logic(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'applyPlaybackSnapshot' in text
    assert 'replayFromSnapshot' in text
    assert 'computeDimmedElements' in text
    assert 'renderFinalAnswer' in text
    assert 'answer_done' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_snapshot_replay_and_delayed_answer_logic -v`
Expected: FAIL because snapshot replay helpers and delayed-answer logic do not exist.

**Step 3: Write minimal implementation**

In `export/graph_export.py`, implement:
- `computeDimmedElements(activeNodeIds, activeEdgeIds)`
  - dim all visible non-active graph elements
- `applyPlaybackSnapshot(snapshot)`
  - restore highlight/dim/focus state from cached snapshot
- `replayFromSnapshot(index)`
  - jump backward/forward to any cached step
- `appendEvidenceIncrementally(evidence)`
  - append one evidence item without rendering final answer yet
- `renderFinalAnswer(answerPayload)`
  - show the final answer only after `answer_done`
- `PlaybackController.playNextQueuedEvent()`
  - apply current event, cache snapshot, update step title, and optionally auto-schedule the next queued step if not paused

Keep `evidence` events as graph flash + evidence append only; do not render the final answer there.

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_snapshot_replay_and_delayed_answer_logic -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 4 completion.

### Task 5: Wire the live SSE stream into PlaybackController and verify end-to-end playback ordering

**Files:**
- Modify: `export/graph_export.py`
- Modify: `tests/server/test_ontology_http_app.py`
- Modify: `tests/integration/test_definition_graph_export.py`
- Optional smoke helper output: `output/_smoke_stdout.log`, `output/_smoke_stderr.log`

**Step 1: Write the failing test**

Add this server-side test to `tests/server/test_ontology_http_app.py`:

```python
def test_qa_stream_emits_progressive_step_titles_in_order(tmp_path: Path):
    input_file = tmp_path / 'ontology.md'
    _write_relation_ontology(input_file)

    app = create_app(input_file=input_file)
    client = TestClient(app)
    response = client.get('/api/qa/stream', params={'q': 'PoD ?????'})
    text = response.text

    assert text.index('event: anchor_node') < text.index('event: expand_neighbors')
    assert text.index('event: expand_neighbors') < text.index('event: filter_nodes')
    assert text.index('event: filter_nodes') < text.index('event: evidence')
    assert text.index('event: evidence') < text.index('event: focus_subgraph')
    assert text.index('event: focus_subgraph') < text.index('event: answer_done')
    assert 'step_title' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_progressive_step_titles_in_order -v`
Expected: FAIL if ordering/fields are still incomplete.

**Step 3: Write minimal implementation**

In `export/graph_export.py`:
- update `startQaStream(question)` to send incoming SSE events into `PlaybackController.enqueueEvent(...)`
- let controller auto-play only one step at a time
- if paused, keep queueing without applying
- on `answer_done`, mark playback finished but keep final snapshot visible

Do not recompute graph state from scratch on `prev/next/replay`; use the stored snapshots.

**Step 4: Run test to verify it passes**

Run: `pytest tests/server/test_ontology_http_app.py::test_qa_stream_emits_progressive_step_titles_in_order -v`
Expected: PASS

**Step 5: Checkpoint**

Update `SESSION_LOG.md` with Task 5 completion.

### Task 6: Run complete verification and progressive-playback smoke test

**Files:**
- Modify if needed: `SESSION_LOG.md`
- Smoke-test target: `[????] ????2?????v2.md`

**Step 1: Run focused tests**

Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
pytest tests/search/test_ontology_query_engine.py -v
pytest tests/qa/test_template_answering.py -v
pytest tests/integration/test_definition_graph_export.py -v
pytest tests/integration/test_ontology_http_cli.py -v
```

Expected: all PASS.

**Step 2: Run full suite**

Run: `pytest tests -q`
Expected: PASS with zero failures.

**Step 3: Run manual smoke test**

Run:
```bash
python -m cloud_delivery_ontology_palantir.cli serve-ontology --input-file "D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md" --host 127.0.0.1 --port 8000
```

Open: `http://127.0.0.1:8000/ontology`

Verify manually:
- ????????????????????/??/??
- ????????????????????????
- ???????
- ????????????
- ??/????????????????
- ???????????

**Step 4: Final checkpoint**

Update `SESSION_LOG.md` with:
- verification commands used
- test results
- manual smoke result
- remaining gaps (if any)
