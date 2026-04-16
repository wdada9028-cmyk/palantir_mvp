# QA Panel Tabs and Clean Trace Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将当前右侧 QA 面板改成 `答案摘要 / 关键证据 / 图谱定位` 三个 tab，并继续保持用户态 trace 简洁。

**Architecture:** 保持现有 `/api/qa/stream`、`trace_summary`、evidence timeline、graph replay 能力不变，只在 `export/graph_export.py` 中重组前端视图状态和渲染函数。优先复用现有 trace summary 数据，不新增后端接口。

**Tech Stack:** Python 3.11, FastAPI SSE, inline browser JavaScript in `export/graph_export.py`, pytest, node `--check`

---

### Task 1: 为 QA 面板增加 tab 外壳与默认状态

**Files:**
- Modify: `export/graph_export.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_contains_qa_tabs_and_defaults_to_answer_summary(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-tab-answer' in text
    assert 'qa-tab-evidence' in text
    assert 'qa-tab-focus' in text
    assert 'qa-panel-answer' in text
    assert 'qa-panel-evidence' in text
    assert 'qa-panel-focus' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_qa_tabs_and_defaults_to_answer_summary -q`
Expected: FAIL because the tab shell does not exist yet.

**Step 3: Write minimal implementation**

- 在 `export/graph_export.py` 的 QA 面板 HTML 中加入三 tab 按钮
- 加入三个 panel 容器
- 默认激活 `答案摘要`
- 加入最小 tab 状态 class

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_qa_tabs_and_defaults_to_answer_summary -q`
Expected: PASS

**Step 5: Commit**

```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: add qa panel tabs shell"
```

### Task 2: 将答案摘要区与旧 trace 主展示解耦

**Files:**
- Modify: `export/graph_export.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_routes_answer_text_to_answer_tab_only(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-panel-answer' in text
    assert 'setQaAnswerTabState' in text
    assert 'used_fallback' in text
```
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_routes_answer_text_to_answer_tab_only -q`
Expected: FAIL because tab-specific answer routing does not exist yet.

**Step 3: Write minimal implementation**

- 增加 answer tab 专属内容区
- 将 `answer_done` / `answer_delta` 的文本渲染定向到 `答案摘要`
- 增加 `AI总结 / 基础回答` 状态标记
- 旧 `逻辑溯源` 不再承担主回答展示职责

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_routes_answer_text_to_answer_tab_only -q`
Expected: PASS

**Step 5: Commit**

```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: route answer summary into answer tab"
```

### Task 3: 增加关键证据卡片渲染

**Files:**
- Modify: `export/graph_export.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_renders_evidence_cards_from_trace_summary(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'renderEvidenceCards' in text
    assert 'qa-evidence-cards' in text
    assert 'evidence-card' in text
```
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_renders_evidence_cards_from_trace_summary -q`
Expected: FAIL because evidence cards do not exist yet.

**Step 3: Write minimal implementation**

- 新增 `renderEvidenceCards(...)`
- 从 `trace_summary.compact.key_evidence` 和 `trace_summary.expanded.detailed_evidence` 提取卡片数据
- 每张卡片仅展示：实体、实例ID、少量关键属性、标签
- 有 overflow 时展示“其余 N 条已折叠”

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_renders_evidence_cards_from_trace_summary -q`
Expected: PASS

**Step 5: Commit**

```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: render evidence cards in qa panel"
```

### Task 4: 增加图谱定位 tab 与点击聚焦

**Files:**
- Modify: `export/graph_export.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_contains_focus_tab_and_graph_focus_handlers(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-focus-list' in text
    assert 'renderFocusTargets' in text
    assert 'focusTraceTarget' in text
```
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_focus_tab_and_graph_focus_handlers -q`
Expected: FAIL because focus tab does not exist yet.

**Step 3: Write minimal implementation**

- 新增 `图谱定位` tab
- 从 `trace_summary.expanded.key_paths` / evidence timeline 中构建可点击项
- 点击后调用现有 `replayFromSnapshot(...)` 或节点级聚焦函数
- 状态栏提示当前已定位的对象/路径

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_focus_tab_and_graph_focus_handlers -q`
Expected: PASS

**Step 5: Commit**

```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: add graph focus tab for qa"
```

### Task 5: 继续收紧用户态 clean trace

**Files:**
- Modify: `export/graph_export.py`
- Test: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_keeps_user_trace_clean_without_debug_payload_sections(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'typeql:' not in text
    assert 'row_count' not in text
    assert 'stack trace' not in text.lower()
    assert 'query plan' not in text.lower()
```
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_keeps_user_trace_clean_without_debug_payload_sections -q`
Expected: FAIL if any old debug-oriented rendering path still leaks into the panel.

**Step 3: Write minimal implementation**

- 删除剩余用户态调试字眼
- 仅保留：问题理解 / 关键证据 / 数据缺口 / 结论依据 / 详细证据对象 / 关键路径
- 不暴露 `typedb_query` 原文内容给用户区域

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_keeps_user_trace_clean_without_debug_payload_sections -q`
Expected: PASS

**Step 5: Commit**

```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: keep qa trace customer-clean"
```

### Task 6: Full verification

**Files:**
- Modify only if follow-up fixes are required.

**Step 1: Run focused front-end export tests**

Run: `pytest tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 2: Run server/integration regression**

Run: `pytest tests/server/test_ontology_http_app.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 3: Run full suite**

Run: `pytest tests -q`
Expected: PASS

**Step 4: Check JS syntax**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_embeds_javascript_without_syntax_error -q`
Expected: PASS

**Step 5: Review working tree**

Run: `git status --short --branch`
Expected: only intended QA panel / trace UI files changed.

**Step 6: Commit final fixups if needed**

```bash
git add export/graph_export.py tests/integration/test_definition_graph_export.py
git commit -m "feat: finalize qa tabs and clean trace ui"
```
