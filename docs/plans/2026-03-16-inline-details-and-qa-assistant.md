# Inline Detail Cards and Ontology QA Assistant Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the ontology graph page so node details appear beside the clicked node instead of in a fixed side panel, and add a constrained smart QA assistant that retrieves evidence from the ontology graph, highlights the retrieval path on the graph, and produces answer plus evidence chain.

**Architecture:** Keep the current markdown-to-ontology build pipeline intact and extend the generated HTML page with two new front-end subsystems: (1) an anchored floating detail card that renders only non-empty sections, and (2) a QA assistant panel backed by a small graph-retrieval layer plus an OpenAI-compatible answer endpoint that is explicitly restricted to retrieved ontology evidence. Retrieval state will be visualized directly on the graph through staged highlighting and preserved as a structured evidence chain shown alongside the answer.

**Tech Stack:** Python 3, `argparse`, `json`, `pathlib`, `http.server` or lightweight stdlib HTTP endpoint, existing `OntologyGraph` JSON payload, Cytoscape.js front-end, OpenAI-compatible chat completion API, `pytest`

---

### Task 1: Add floating inline detail-card behavior and hide empty sections

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/export/graph_export.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_uses_inline_floating_detail_card_and_hides_empty_sections(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2'})
    graph.add_object(
        OntologyObject(
            id='object_type:Project',
            type='ObjectType',
            name='Project',
            attributes={
                'group': '4.1 ??????',
                'semantic_definition': '',
                'key_properties': [{'name': 'project_id', 'description': '??ID'}],
                'notes': [],
            },
        )
    )
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')
    assert 'floating-detail-card' in text
    assert 'showInlineDetailCard' in text
    assert 'if (!hasContent) return' in text
    assert '????' not in text or 'renderRelationSummarySection' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py::test_exported_html_uses_inline_floating_detail_card_and_hides_empty_sections" -v`
Expected: FAIL because the page still uses the fixed right-side detail panel and always renders section shells.

**Step 3: Write minimal implementation**

Implement in `export/graph_export.py`:
- replace the fixed detail panel with a floating detail card anchored near the clicked node
- add a helper like `renderSection(title, htmlValue, hasContent)` that skips empty sections
- keep relation summary logic, but suppress the section when both in-edge and out-edge counts are zero
- close the card on blank-canvas click and switch it when another node is clicked

Example front-end shape:

```javascript
function renderSection(title, bodyHtml, hasContent) {
  if (!hasContent) return '';
  return `<div class="detail-card-section"><div class="section-title">${title}</div>${bodyHtml}</div>`;
}

function showInlineDetailCard(node, htmlContent) {
  const position = node.renderedPosition();
  // compute left/right placement from viewport bounds
}
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py::test_exported_html_uses_inline_floating_detail_card_and_hides_empty_sections" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/export/graph_export.py" "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py"
git commit -m "feat: add inline floating ontology detail cards"
```

If git is still unavailable in this workspace, skip the commit and record that fact.

### Task 2: Add front-end QA assistant shell with futuristic UI

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/export/graph_export.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_contains_qa_assistant_shell(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')
    assert '??????' in text
    assert '???????????' in text
    assert 'qa-assistant-toggle' in text
    assert 'qa-answer-panel' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py::test_exported_html_contains_qa_assistant_shell" -v`
Expected: FAIL because no QA assistant UI exists.

**Step 3: Write minimal implementation**

Extend the exported HTML with:
- a bottom-right floating assistant launcher button
- an expandable assistant panel
- title/subtitle enforcing the retrieval-only constraint
- question input, ask button, loading state area, answer card, evidence-chain card
- visual styling with subtle neon/gradient accents, not a noisy cyberpunk theme

Example structure:

```html
<button id="qa-assistant-toggle">??????</button>
<section id="qa-answer-panel" class="qa-panel hidden">
  <header>...</header>
  <textarea id="qa-question"></textarea>
  <button id="qa-submit">??</button>
  <div id="qa-status"></div>
  <div id="qa-answer"></div>
  <div id="qa-evidence"></div>
</section>
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py::test_exported_html_contains_qa_assistant_shell" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/export/graph_export.py" "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py"
git commit -m "feat: add ontology qa assistant shell"
```

### Task 3: Build deterministic ontology graph retrieval and evidence-chain models

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/search/ontology_query_models.py`
- Create: `D:/????/AI?????/??????/palantir_mvp/search/ontology_query_engine.py`
- Modify: `D:/????/AI?????/??????/palantir_mvp/schema.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/search/test_ontology_query_engine.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation
from cloud_delivery_ontology_palantir.search.ontology_query_engine import retrieve_ontology_evidence


def test_retrieve_ontology_evidence_returns_seed_nodes_relations_and_chain():
    graph = OntologyGraph()
    graph.add_object(OntologyObject(id='object_type:PoD', type='ObjectType', name='PoD', attributes={'key_properties': [{'name': 'pod_id', 'description': 'PoD ID'}]}))
    graph.add_object(OntologyObject(id='object_type:ArrivalPlan', type='ObjectType', name='ArrivalPlan', attributes={}))
    graph.add_relation(OntologyRelation(source_id='object_type:ArrivalPlan', target_id='object_type:PoD', relation='APPLIES_TO'))
    result = retrieve_ontology_evidence(graph, 'PoD ???????')
    assert result.seed_node_ids
    assert result.evidence_chain
    assert any(step['type'] == 'relation' for step in result.evidence_chain)
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/search/test_ontology_query_engine.py" -v`
Expected: FAIL because the retrieval engine and models do not exist.

**Step 3: Write minimal implementation**

Create a retrieval system that:
- tokenizes the question
- scores node names, aliases, group labels, property names, property descriptions, and relation labels
- chooses seed nodes
- expands across a limited number of adjacent relations
- produces a structured `evidence_chain` list, e.g. `[{type: 'seed', ...}, {type: 'relation', ...}, {type: 'node', ...}]`
- returns both the final evidence bundle and the animation-ready steps

Suggested result shape:

```python
@dataclass(slots=True)
class OntologyEvidenceBundle:
    seed_node_ids: list[str]
    expanded_node_ids: list[str]
    relation_ids: list[str]
    evidence_chain: list[dict[str, object]]
    answer_context: dict[str, object]
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/search/test_ontology_query_engine.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/search/ontology_query_models.py" "D:/????/AI?????/??????/palantir_mvp/search/ontology_query_engine.py" "D:/????/AI?????/??????/palantir_mvp/tests/search/test_ontology_query_engine.py" "D:/????/AI?????/??????/palantir_mvp/schema.py"
git commit -m "feat: add ontology evidence retrieval engine"
```

### Task 4: Add constrained LLM answering that only uses retrieved ontology evidence

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/qa/answer_models.py`
- Create: `D:/????/AI?????/??????/palantir_mvp/qa/llm_client.py`
- Create: `D:/????/AI?????/??????/palantir_mvp/qa/answer_service.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/qa/test_answer_service.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.qa.answer_service import build_answer_prompt


def test_answer_prompt_forbids_external_knowledge():
    system_prompt, user_prompt = build_answer_prompt(
        question='PoD ????????',
        answer_context={'nodes': ['PoD'], 'relations': ['APPLIES_TO']},
    )
    assert 'Only use the provided ontology evidence' in system_prompt
    assert 'If the evidence is insufficient' in system_prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/qa/test_answer_service.py" -v`
Expected: FAIL because the QA service does not exist.

**Step 3: Write minimal implementation**

Implement:
- an OpenAI-compatible chat client loaded from env vars
- a prompt builder that explicitly forbids external knowledge
- an answer service that takes `question + answer_context + evidence_chain`
- output shape containing `answer`, `confidence_note`, `evidence_chain`, and `insufficient_evidence`

Prompt rule example:

```text
Only use the provided ontology evidence.
Do not add any external knowledge.
If the evidence is insufficient, say so clearly.
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/qa/test_answer_service.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/qa/answer_models.py" "D:/????/AI?????/??????/palantir_mvp/qa/llm_client.py" "D:/????/AI?????/??????/palantir_mvp/qa/answer_service.py" "D:/????/AI?????/??????/palantir_mvp/tests/qa/test_answer_service.py"
git commit -m "feat: add constrained llm ontology answer service"
```

### Task 5: Add an HTTP QA endpoint that serves answer plus evidence chain

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/server/qa_server.py`
- Modify: `D:/????/AI?????/??????/palantir_mvp/cli.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/integration/test_qa_server.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.server.qa_server import build_qa_response


def test_build_qa_response_contains_answer_and_evidence_chain():
    payload = build_qa_response(
        question='PoD ????????',
        graph_payload={'objects': [], 'relations': []},
    )
    assert 'answer' in payload
    assert 'evidence_chain' in payload
    assert 'highlight_steps' in payload
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_qa_server.py" -v`
Expected: FAIL because no server helper exists.

**Step 3: Write minimal implementation**

Implement a lightweight local endpoint/helper that:
- receives the question and current graph payload or file path
- reconstructs/reuses the ontology graph
- runs retrieval
- calls the constrained answer service
- returns JSON containing:
  - `answer`
  - `evidence_chain`
  - `highlight_steps`
  - `seed_node_ids`
  - `expanded_node_ids`
  - `relation_ids`

Also add a CLI subcommand to serve or test the local QA endpoint, for example `serve-qa`.

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_qa_server.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/server/qa_server.py" "D:/????/AI?????/??????/palantir_mvp/cli.py" "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_qa_server.py"
git commit -m "feat: add ontology qa endpoint"
```

### Task 6: Add graph retrieval animation and persistent evidence-chain rendering to the page

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/export/graph_export.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python

def test_exported_html_contains_retrieval_highlight_animation_hooks(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')
    assert 'playRetrievalSteps' in text
    assert 'highlight_steps' in text
    assert 'qa-evidence-chain' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py::test_exported_html_contains_retrieval_highlight_animation_hooks" -v`
Expected: FAIL because the page has no retrieval animation logic.

**Step 3: Write minimal implementation**

In `graph_export.py`, add front-end logic to:
- submit the question to the QA endpoint
- receive `highlight_steps`
- animate those steps in sequence on the graph
- leave the final evidence subgraph highlighted
- render the evidence chain text alongside the answer

Suggested front-end functions:

```javascript
async function askOntologyQuestion() { ... }
async function playRetrievalSteps(steps) { ... }
function renderEvidenceChain(chain) { ... }
function persistFinalEvidence(result) { ... }
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py::test_exported_html_contains_retrieval_highlight_animation_hooks" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/export/graph_export.py" "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py"
git commit -m "feat: animate ontology retrieval evidence on graph"
```

### Task 7: Integrate QA endpoint details into the build/serve workflow and verify end-to-end

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/pipelines/build_ontology_pipeline.py`
- Modify: `D:/????/AI?????/??????/palantir_mvp/export/graph_export.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/integration/test_build_ontology_cli.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/integration/test_qa_server.py`

**Step 1: Write the failing integration test**

```python

def test_build_ontology_cli_outputs_page_with_inline_details_and_qa_hooks(tmp_path: Path):
    input_file = Path(...)
    output_dir = tmp_path / 'output'
    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    html_text = (output_dir / 'ontology.html').read_text(encoding='utf-8')
    assert 'floating-detail-card' in html_text
    assert '??????' in html_text
    assert 'qa-answer-panel' in html_text
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_build_ontology_cli.py" -v`
Expected: FAIL until the generated page includes the new UX and QA hooks.

**Step 3: Write minimal implementation**

Ensure the build pipeline either:
- embeds enough graph payload for the front-end QA flow, or
- writes references the QA endpoint can use directly

Update the generated HTML so it knows where to send QA requests and how to render the response cards.

**Step 4: Run the focused verification suite**

Run:

```bash
pytest   "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py"   "D:/????/AI?????/??????/palantir_mvp/tests/search/test_ontology_query_engine.py"   "D:/????/AI?????/??????/palantir_mvp/tests/qa/test_answer_service.py"   "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_qa_server.py"   "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_build_ontology_cli.py"   -v
```

Expected: all PASS

**Step 5: Run a real build and manual smoke check**

Run:

```bash
python -m cloud_delivery_ontology_palantir.cli build-ontology --input-file "D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md" --output-dir "D:/????/AI?????/??????/palantir_mvp/output"
```

Then manually verify:
- clicking a node shows a nearby floating detail card
- empty sections are omitted
- the assistant opens from the floating button
- asking a question plays a retrieval animation on the graph
- the answer includes evidence chain text
- the final evidence subgraph remains highlighted

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add inline ontology details and constrained qa assistant"
```

If git still is unavailable, skip the commit and document that limitation.
