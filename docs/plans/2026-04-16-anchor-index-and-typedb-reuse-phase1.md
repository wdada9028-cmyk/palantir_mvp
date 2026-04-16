# Anchor Index + TypeDB Connection Reuse Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 只做两个高收益低风险优化：外部锚点索引召回、TypeDB 请求级连接复用。

**Architecture:** 第一部分把“每个实体扫 1000 条候选实例”的召回方式改成“按 surface text 从外部锚点索引召回 top-k 候选，再复用现有规则/LLM 精排”。第二部分把 TypeDB 从“每条 Query connect/close”改成“单次 run_instance_qa 请求级复用一个已连接 client”。本阶段不做查询并发，不做大查询合并。

**Tech Stack:** Python 3.11、SQLite（标准库 sqlite3）、TypeDB 3.8 driver、pytest。

---

## 范围约束
本阶段**只做**：

1. 锚点候选全量预加载 → 外部锚点索引召回
2. TypeDB 请求级连接复用

本阶段**不做**：

- 阶段耗时埋点
- 同轮独立查询并发
- 大查询合并
- Answer 阶段优化

---

### Task 1: 外部锚点索引召回

**Files:**
- Create: `instance_qa/anchor_search_index.py`
- Modify: `instance_qa/orchestrator.py:347-407, 521-554`
- Modify: `instance_qa/anchor_locator_registry.py`
- Modify: `instance_qa/anchor_candidate_context_builder.py`（仅在候选字段变化时）
- Test: `tests/instance_qa/test_anchor_search_index.py`
- Test: `tests/integration/test_instance_qa_stream.py`

**Step 1: Write the failing test**

创建 `tests/instance_qa/test_anchor_search_index.py`，至少覆盖：

```python
from pathlib import Path

from cloud_delivery_ontology_palantir.instance_qa.anchor_search_index import (
    build_anchor_search_index,
    search_anchor_candidates,
)


def test_anchor_search_index_prefers_exact_raw_value_match(tmp_path: Path):
    db_path = tmp_path / 'anchor.sqlite3'
    build_anchor_search_index(
        [
            {
                'entity': 'PoD',
                'attribute': 'pod_id',
                'raw_value': 'POD-001',
                'iid': 'iid-1',
                'payload': {'pod_id': 'POD-001'},
            },
            {
                'entity': 'PoD',
                'attribute': 'pod_id',
                'raw_value': 'Pod-001',
                'iid': 'iid-2',
                'payload': {'pod_id': 'Pod-001'},
            },
        ],
        db_path=db_path,
    )

    hits = search_anchor_candidates(db_path, 'POD-001', top_k=5)

    assert hits[0]['iid'] == 'iid-1'


def test_anchor_search_index_limits_top_k(tmp_path: Path):
    db_path = tmp_path / 'anchor.sqlite3'
    rows = [
        {
            'entity': 'PoD',
            'attribute': 'pod_id',
            'raw_value': f'POD-{i:03d}',
            'iid': f'iid-{i}',
            'payload': {'pod_id': f'POD-{i:03d}'},
        }
        for i in range(20)
    ]
    build_anchor_search_index(rows, db_path=db_path)

    hits = search_anchor_candidates(db_path, 'POD', top_k=5)

    assert len(hits) <= 5
```

补一个集成测试，验证 `run_instance_qa()` 不再对每个实体执行 `limit 1000` 候选扫库。

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/instance_qa/test_anchor_search_index.py -q
```

Expected: FAIL

**Step 3: Write minimal implementation**

创建 `instance_qa/anchor_search_index.py`，最小接口：

```python
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def normalize_anchor_value(value: str) -> str:
    return ''.join(ch for ch in str(value or '').casefold() if ch.isalnum())


def build_anchor_search_index(rows: list[dict[str, object]], *, db_path: Path) -> Path:
    ...


def search_anchor_candidates(db_path: Path, raw_anchor_text: str, *, top_k: int = 20) -> list[dict[str, object]]:
    ...
```

索引表建议结构：

```sql
CREATE TABLE anchor_index (
  entity TEXT NOT NULL,
  attribute TEXT NOT NULL,
  raw_value TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  iid TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE INDEX idx_anchor_norm ON anchor_index(normalized_value);
CREATE INDEX idx_anchor_entity_norm ON anchor_index(entity, normalized_value);
```

在 `instance_qa/orchestrator.py` 中替换：

- 删除 `_load_anchor_candidate_rows(locator_registry)` 这条“每个实体扫一遍实例”的路径
- 改成：
  1. 从 `locator_registry` 计算需要入索引的 locator 属性
  2. 生成 / 读取锚点索引
  3. 按 `_extract_anchor_surface_candidates(question)` 结果做 top-k 候选召回
  4. 把召回结果组装成现有 resolver / ranker 可以继续消费的候选结构

在 `instance_qa/anchor_locator_registry.py` 中收紧索引字段来源：

- 只把 locator 属性进索引
- 不把所有 attributes 全部纳入索引

**Step 4: Run tests to verify it passes**

Run:
```bash
pytest tests/instance_qa/test_anchor_search_index.py tests/integration/test_instance_qa_stream.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/anchor_search_index.py instance_qa/orchestrator.py instance_qa/anchor_locator_registry.py instance_qa/anchor_candidate_context_builder.py tests/instance_qa/test_anchor_search_index.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: use external anchor index for candidate recall"
```

**预期效果：**
- 锚点候选阶段延时下降：70% ~ 95%
- 整链路总时延下降：20% ~ 50%

---

### Task 2: TypeDB 请求级连接复用

**Files:**
- Modify: `instance_qa/typedb_client.py`
- Modify: `instance_qa/orchestrator.py:226-250, 557-570`
- Test: `tests/instance_qa/test_typedb_client.py`
- Test: `tests/integration/test_instance_qa_stream.py`

**Step 1: Write the failing test**

在 `tests/instance_qa/test_typedb_client.py` 增加：

```python
def test_execute_multiple_queries_reuses_connected_driver(monkeypatch):
    connect_calls = {'count': 0}

    class FakeClient(TypeDBClient):
        def connect(self):
            connect_calls['count'] += 1
            self._driver = object()

    client = FakeClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery'))
    client.connect()
    client._driver = object()

    # 这里配合 fake execute 路径断言同一个 client 能跑多次查询
    assert connect_calls['count'] == 1
```

再补 orchestrator 层测试，验证单个 `run_instance_qa()` 请求只 connect 一次、close 一次。

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/instance_qa/test_typedb_client.py -q
```

Expected: FAIL

**Step 3: Write minimal implementation**

在 `instance_qa/typedb_client.py` 增加上下文接口：

```python
class TypeDBClient:
    ...

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
```

在 `instance_qa/orchestrator.py` 中：

- 把 `_execute_fact_queries(...)` 改成接收一个已连接的 `typedb_client`
- 把 `_run_typeql_readonly(...)` 改成基于该 client 执行，而不是自己内部新建 client
- 在 `run_instance_qa()` 内：

```python
config = load_typedb_config()
if config is None:
    ...
else:
    with TypeDBClient(config) as typedb_client:
        initial_rows = _execute_fact_queries(initial_queries, schema_registry, fact_query_records, typedb_client)
        ...
```

注意：
- propagation queries 也复用同一个 client
- 只在整个请求结束时统一 close

**Step 4: Run tests to verify it passes**

Run:
```bash
pytest tests/instance_qa/test_typedb_client.py tests/integration/test_instance_qa_stream.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/typedb_client.py instance_qa/orchestrator.py tests/instance_qa/test_typedb_client.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: reuse typedb client within instance qa request"
```

**预期效果：**
- TypeDB 查询阶段延时下降：20% ~ 40%
- 整链路总时延下降：10% ~ 25%

---

## 推荐执行顺序
1. Task 1：外部锚点索引召回
2. Task 2：TypeDB 请求级连接复用

---

## 验收标准
### 功能正确性
- `POD-001的状态是什么？` 仍能稳定命中正确实例
- `L1-A机房断电一周，会有哪些影响？` 仍能稳定产出正确实例链路
- 锚点精排、router、后续 reasoner 行为不退化

### 性能结果
- 锚点候选阶段显著快于“每个实体扫 1000 条”旧方案
- TypeDB 查询阶段 connect/close 次数明显下降
- 端到端平均时延下降

### 稳定性
- 无新增 router failure
- 无 TypeDB 连接泄漏
- 失败时仍能走现有 fallback 路径
