# Ontology Visual Reset Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add explicit recovery from trace/focus mode, restore background-click reset, and shrink/reposition the floating detail card so it follows clicked nodes.

**Architecture:** Keep the current generated Cytoscape front-end but centralize reset state in a single exploration-mode function, drive dimming from a parent state class, and reuse the existing floating detail card with lighter styling and node-relative positioning.

**Tech Stack:** Python 3.11, string-built HTML/CSS/JS templates, Cytoscape.js, pytest

---

### Task 1: Add failing HTML regression tests for reset-mode hooks

**Files:**
- Modify: `D:\????\AI?????\??????\palantir_mvp	ests\integration	est_definition_graph_export.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp\export\graph_export.py`

**Step 1: Write the failing test**
Add assertions for generated HTML containing:
- `filtering-active`
- `resetToExplorationMode`
- reset button hook (for example `trace-reset-button`)
- `currentSnapshot`
- `event.target === cy`
- `max-width: 280px`
- `font-size: 12px`

Suggested test shape:
```python
def test_exported_html_contains_trace_reset_mode_controls(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'filtering-active' in text
    assert 'resetToExplorationMode' in text
    assert 'trace-reset-button' in text
    assert 'currentSnapshot' in text
    assert 'event.target === cy' in text
    assert 'max-width: 280px' in text
    assert 'font-size: 12px' in text
```

**Step 2: Run test to verify it fails**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_trace_reset_mode_controls -v
```
Expected: FAIL.

**Step 3: Write minimal implementation**
Update `D:\????\AI?????\??????\palantir_mvp\export\graph_export.py` to emit the required markup, CSS, and JS hooks.

**Step 4: Run test to verify it passes**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add tests/integration/test_definition_graph_export.py export/graph_export.py
git commit -m "feat: add ontology trace reset controls"
```

### Task 2: Implement exploration-mode reset and background click recovery

**Files:**
- Modify: `D:\????\AI?????\??????\palantir_mvp\export\graph_export.py`
- Test: `D:\????\AI?????\??????\palantir_mvp	ests\integration	est_definition_graph_export.py`

**Step 1: Add the minimal failing assertion if still missing**
Ensure HTML explicitly contains the reset function and background-click logic.

**Step 2: Implement the reset behavior**
Add:
- `resetToExplorationMode()`
- parent state class toggling (`filtering-active`)
- reset button show/hide helpers
- `PlaybackController.currentSnapshot`
- background tap branch calling `resetToExplorationMode()` when `event.target === cy`
- `reset-view` reusing the same reset path

**Step 3: Run focused verification**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: PASS.

**Step 4: Smoke the served page**
Run:
```bash
python -m cloud_delivery_ontology_palantir.cli serve-ontology --input-file "D:\????\AI?????\??????\palantir_mvp\[????] ????2?????v2.md" --host 127.0.0.1 --port 8000
```
Manual check:
- submit a query
- click background
- graph returns to full-bright exploration mode
- reset button disappears

**Step 5: Commit**
```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "fix: restore ontology exploration mode reset"
```

### Task 3: Shrink and re-anchor the floating detail panel

**Files:**
- Modify: `D:\????\AI?????\??????\palantir_mvp\export\graph_export.py`
- Test: `D:\????\AI?????\??????\palantir_mvp	ests\integration	est_definition_graph_export.py`

**Step 1: Add failing assertions for panel sizing/position logic**
Confirm exported HTML contains:
- `max-width: 280px`
- `font-size: 12px`
- `node.renderedPosition()`
- clamped left/top calculations

**Step 2: Implement minimal CSS/JS changes**
- reduce panel width/fonts
- preserve absolute positioning
- compute `left = pos.x + 20`, `top = pos.y - 20`
- clamp within graph-stage bounds
- keep background click hiding the panel

**Step 3: Run focused verification**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
```
Expected: PASS.

**Step 4: Manual smoke check**
Verify different node clicks place the panel near the node and keep it on-screen.

**Step 5: Commit**
```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: slim ontology detail card"
```

### Task 4: Full verification

**Files:**
- Reference: `D:\????\AI?????\??????\palantir_mvp\export\graph_export.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp	ests\integration	est_definition_graph_export.py`
- Reference: `D:\????\AI?????\??????\palantir_mvp	ests\server	est_ontology_http_app.py`

**Step 1: Run focused suites**
Run:
```bash
pytest tests/integration/test_definition_graph_export.py -v
pytest tests/server/test_ontology_http_app.py -v
```
Expected: PASS.

**Step 2: Run full regression**
Run:
```bash
pytest tests -q
```
Expected: PASS.

**Step 3: Commit**
```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py docs/plans/2026-03-18-ontology-visual-reset-design.md docs/plans/2026-03-18-ontology-visual-reset.md
git commit -m "feat: refine ontology exploration reset"
```
