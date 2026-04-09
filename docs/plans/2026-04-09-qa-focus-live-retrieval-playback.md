# QA Focus Live Retrieval Playback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让实例 QA 链路在问答进行中真实驱动本体结构图高亮回放，并在“图谱定位”页保留可重播的步骤列表与控制。

**Architecture:** 继续复用现有 SSE 事件、`PlaybackController`、`replayFromSnapshot(...)`、`evidenceSnapshots`，不新增后端协议。前端只在 `export/graph_export.py` 中补一层 focus-playback 状态：阶段事件产生 snapshot 时立即驱动图谱；同时把这些 snapshot 组织成可重播步骤和简洁控制区。

**Tech Stack:** Python 3.11, inline browser JavaScript in `export/graph_export.py`, pytest, node `--check`

---

### Task 1: 锁定图谱定位页的动态回放 UI 外壳

**Files:**
- Modify: `tests/integration/test_definition_graph_export.py`
- Modify: `export/graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_contains_focus_playback_controls(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-playback-prev' in text
    assert 'qa-playback-next' in text
    assert 'qa-playback-replay' in text
    assert 'qa-playback-current' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_focus_playback_controls -q`
Expected: FAIL because playback controls do not exist yet.

**Step 3: Write minimal implementation**

- 在 `图谱定位` 的 `qa-focus-playback` 卡片中加入播放控制按钮和当前步骤提示
- 只保留简洁控制，不恢复调试台式文本

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_contains_focus_playback_controls -q`
Expected: PASS

### Task 2: 锁定实例 QA 阶段事件会驱动图谱动态回放

**Files:**
- Modify: `tests/integration/test_definition_graph_export.py`
- Modify: `export/graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_autoplays_instance_qa_snapshots_into_graph_focus(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'setFocusPlaybackIndex' in text
    assert 'findIndex(item => item.evidence_id === evidence.evidence_id)' in text
    assert 'replayFromSnapshot(snapshot' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_autoplays_instance_qa_snapshots_into_graph_focus -q`
Expected: FAIL because stage snapshots are stored but not auto-played yet.

**Step 3: Write minimal implementation**

- 为 focus playback 增加当前步骤状态
- 在 `upsertEvidenceItem(...)` 中，当阶段事件带 snapshot 时立即切到对应 playback step 并驱动 `replayFromSnapshot(...)`
- 手动点击上一步/下一步/重播时也走同一套函数

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_autoplays_instance_qa_snapshots_into_graph_focus -q`
Expected: PASS

### Task 3: 收紧图谱定位页文案并保持旧检索协议兼容

**Files:**
- Modify: `tests/integration/test_definition_graph_export.py`
- Modify: `export/graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_keeps_focus_playback_customer_facing(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert '动态检索过程' in text or '检索回放' in text
    assert 'query plan' not in text.lower()
    assert 'stack trace' not in text.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_keeps_focus_playback_customer_facing -q`
Expected: FAIL if the focus playback shell or wording is still incomplete.

**Step 3: Write minimal implementation**

- 保持 `trace_anchor / trace_expand / evidence_final` 旧协议兼容
- 新增的控制区和步骤提示使用客户可读文案
- 不暴露底层 TypeQL / 调试信息

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_keeps_focus_playback_customer_facing -q`
Expected: PASS

### Task 4: Full verification

**Files:**
- Modify only if follow-up fixes are required.

**Step 1: Run focused export tests**

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
