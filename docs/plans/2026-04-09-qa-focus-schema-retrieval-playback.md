# QA Focus Schema Retrieval Playback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让“图谱定位”只回放实体/schema 检索过程，不再把 TypeDB 实例查询和推理阶段强行映射到本体结构图上。

**Architecture:** 保持 `答案摘要 / 关键证据 / 图谱定位` 三分工不变。`图谱定位` 只消费 schema retrieval 轨迹：`seed_node_ids`、`expansion_steps`、最终 schema 命中子图。实例命中与推理阶段仍保留在证据/答案区，但不驱动图谱动画。

**Tech Stack:** Python 3.11, inline browser JavaScript in `export/graph_export.py`, pytest, node `--check`

---

### Task 1: 锁定图谱定位只绑定 schema 检索轨迹

**Files:**
- Modify: `tests/integration/test_definition_graph_export.py`
- Modify: `export/graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_focus_playback_uses_schema_retrieval_only(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'buildSchemaRetrievalPlaybackSteps' in text
    assert 'typedb_result' not in text.split('function buildSchemaRetrievalPlaybackSteps', 1)[1][:1200]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_focus_playback_uses_schema_retrieval_only -q`
Expected: FAIL because current focus playback still absorbs instance QA stage events.

**Step 3: Write minimal implementation**

- 新增 schema retrieval playback builder，只从 `search_trace` / `trace_anchor` / `trace_expand` / `evidence_final` 组织回放步骤
- 移除 `question_dsl / typedb_result / reasoning_done` 对图谱 playback 的直接驱动

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_focus_playback_uses_schema_retrieval_only -q`
Expected: PASS

### Task 2: 锁定实例 QA 阶段事件只更新文案，不驱动图谱动画

**Files:**
- Modify: `tests/integration/test_definition_graph_export.py`
- Modify: `export/graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_instance_qa_stage_events_do_not_auto_play_graph_focus(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'upsertEvidenceItem({' in text
    assert 'setFocusPlaybackIndex(playbackIndex' not in text.split('function handleInstanceQaStageEvent', 1)[1][:2600]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_instance_qa_stage_events_do_not_auto_play_graph_focus -q`
Expected: FAIL because current `upsertEvidenceItem(...)` path会自动推动 focus playback。

**Step 3: Write minimal implementation**

- 把图谱自动播放入口收敛到 schema retrieval playback 构建完成后的统一函数
- 实例 QA 阶段事件仅更新状态/证据，不再推进图谱播放下标

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_instance_qa_stage_events_do_not_auto_play_graph_focus -q`
Expected: PASS

### Task 3: 补最终 schema 子图回放与控制区文案

**Files:**
- Modify: `tests/integration/test_definition_graph_export.py`
- Modify: `export/graph_export.py`

**Step 1: Write the failing test**

```python
def test_exported_html_focus_playback_keeps_entity_retrieval_wording(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'schema retrieval' not in text.lower()
    assert 'qa-playback-current' in text
    assert 'trace_anchor' in text
    assert 'trace_expand' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_focus_playback_keeps_entity_retrieval_wording -q`
Expected: FAIL if wording/control reuse still混着实例阶段语义。

**Step 3: Write minimal implementation**

- `图谱定位` 的当前步骤说明改成实体检索语义
- 控制区继续保留上一步/重播/下一步，但步骤内容来源变成 schema retrieval steps
- 最终步骤落到 schema 子图，而不是实例/推理阶段

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_definition_graph_export.py::test_exported_html_focus_playback_keeps_entity_retrieval_wording -q`
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
