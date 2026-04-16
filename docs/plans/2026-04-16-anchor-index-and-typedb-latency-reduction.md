# Anchor Index + TypeDB Latency Reduction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不明显牺牲实例问答准确率的前提下，优先缩短锚点候选解析与 TypeDB 查询阶段的总时延。

**Architecture:** 本方案分三层推进。第一层先把“每问一次就全量扫实体候选”改造成“外部锚点索引召回 + 现有规则/LLM 精排复用”；第二层把 TypeDB 从“每条 Query 单独 connect/close”改成“单次 run_instance_qa 请求级复用连接/driver”；第三层仅对同一轮中的独立查询做受控并发，不提前做高风险的大查询合并。

**Tech Stack:** Python 3.11、TypeDB 3.8 driver、现有 Instance QA pipeline、SQLite（标准库 `sqlite3`，作为轻量外部锚点索引存储）、pytest。

---

## 实施优先级总览

### P0：先补可观测性与回归护栏
**目标：** 改造前先把阶段耗时打出来，避免后面只能靠体感判断优化是否有效。

**Files:**
- Modify: `instance_qa/orchestrator.py`
- Modify: `server/ontology_http_service.py`
- Test: `tests/integration/test_instance_qa_stream.py`

**Step 1: Write the failing test**

在 `tests/integration/test_instance_qa_stream.py` 增加一个断言，要求 `typedb_result` 或 `answer_done` payload 中包含阶段耗时字段，例如：

```python
def test_instance_qa_stream_includes_stage_timings(tmp_path: Path):
    response = _call_stream(...)
    answer_payload = _event_payloads(response.text, 'answer_done')[0]
    assert 'stage_timings' in answer_payload
    assert 'anchor_resolution_ms' in answer_payload['stage_timings']
    assert 'typedb_query_ms' in answer_payload['stage_timings']
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_stream_includes_stage_timings -q
```

Expected: FAIL，因为当前 payload 里没有 `stage_timings`。

**Step 3: Write minimal implementation**

在 `instance_qa/orchestrator.py` 中为以下阶段记录耗时：
- anchor candidate recall
- anchor ranker
- router
- initial TypeDB queries
- propagation TypeDB queries
- reasoning
- answer generation context build

将结果挂到 `fact_pack['metadata']['stage_timings']`，并在 `server/ontology_http_service.py` 的 `answer_done` 中带出：

```python
'stage_timings': result.fact_pack.get('metadata', {}).get('stage_timings', {})
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/integration/test_instance_qa_stream.py::test_instance_qa_stream_includes_stage_timings -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/orchestrator.py server/ontology_http_service.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: add instance qa stage timing diagnostics"
```

---

### P1：外部锚点索引召回（最高优先级）
**目标：** 去掉“每个实体扫 1000 行实例”的候选召回方式，改成“按 surface text 从外部索引召回 top-k 候选”。

**Files:**
- Create: `instance_qa/anchor_search_index.py`
- Modify: `instance_qa/orchestrator.py:347-407, 521-554`
- Modify: `instance_qa/anchor_locator_registry.py`
- Modify: `instance_qa/anchor_candidate_context_builder.py`（仅在候选字段变化时）
- Test: `tests/instance_qa/test_anchor_search_index.py`
- Test: `tests/integration/test_instance_qa_stream.py`

#### 设计约束
- 外部索引不替代 TypeDB，只负责“字符串 → 候选实例”召回。
- 最终决策仍然复用现有：
  - 规则候选解析
  - LLM 精排
  - `apply_anchor_resolution_policy(...)`
- 索引字段只纳入 locator 属性，不做整表镜像。

#### 索引建议结构
使用 SQLite 建一个轻量表，例如：

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

其中 `payload_json` 保存后续候选上下文所需最小行数据。

#### 召回策略
按下面顺序召回：
1. 原值完全匹配
2. casefold 匹配
3. 轻度归一化匹配（例如去掉 `-` / `_`）
4. 前缀匹配 / contains（仅作为低优先级补充）

返回 top-k 候选，不再返回“每个实体 1000 条”的大列表。

**Step 1: Write the failing tests**

新增 `tests/instance_qa/test_anchor_search_index.py`：

```python
def test_anchor_search_index_returns_exact_match_before_normalized_match(tmp_path: Path):
    index = build_anchor_search_index([
        {'entity': 'PoD', 'attribute': 'pod_id', 'raw_value': 'POD-001', 'iid': 'iid-1', 'payload': {'pod_id': 'POD-001'}},
        {'entity': 'PoD', 'attribute': 'pod_id', 'raw_value': 'Pod-001', 'iid': 'iid-2', 'payload': {'pod_id': 'Pod-001'}},
    ], db_path=tmp_path / 'anchor.sqlite3')

    hits = search_anchor_candidates(index, 'POD-001', top_k=5)

    assert hits[0]['iid'] == 'iid-1'
```

```python
def test_anchor_search_index_limits_candidates_without_entity_full_scan(tmp_path: Path):
    ...
    assert len(hits) <= 5
```

再补一个集成测试，证明 `run_instance_qa()` 不再调用 `_build_anchor_candidate_query()` N 次扫实体。

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/instance_qa/test_anchor_search_index.py -q
```

Expected: FAIL，因为模块与行为都不存在。

**Step 3: Write minimal implementation**

新增 `instance_qa/anchor_search_index.py`，至少包含：

```python
from dataclasses import dataclass
from pathlib import Path
import sqlite3

@dataclass(slots=True)
class AnchorSearchHit:
    entity: str
    attribute: str
    raw_value: str
    normalized_value: str
    iid: str
    payload: dict[str, object]
    match_stage: str


def normalize_anchor_value(value: str) -> str:
    return ''.join(ch for ch in value.casefold() if ch.isalnum())


def build_anchor_search_index(rows: list[dict[str, object]], *, db_path: Path) -> Path:
    ...


def search_anchor_candidates(db_path: Path, raw_anchor_text: str, *, top_k: int = 20) -> list[dict[str, object]]:
    ...
```

在 `instance_qa/orchestrator.py` 中：
- 删除 `_load_anchor_candidate_rows(locator_registry)` 的全实体扫描调用
- 改成：
  1. 从外部索引中按 `surface_candidates` 做 top-k 召回
  2. 将返回的 hits 组装成与现有 resolver 兼容的 candidate rows / context

在 `instance_qa/anchor_locator_registry.py` 中：
- 给每个实体显式声明哪些属性进入索引
- 不把所有 attributes 全塞进去

**Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/instance_qa/test_anchor_search_index.py tests/integration/test_instance_qa_stream.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/anchor_search_index.py instance_qa/orchestrator.py instance_qa/anchor_locator_registry.py tests/instance_qa/test_anchor_search_index.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: replace full entity scan with external anchor index recall"
```

#### 预期效果
- 锚点候选阶段延时预计下降：70% ~ 95%
- 整链路总时延预计下降：20% ~ 50%
- 对“明确实例属性问答”收益最大

---

### P2：TypeDB 请求级连接复用（高优先级）
**目标：** 把“每条 Query 都 connect/close”改成“单次 run_instance_qa 请求级复用一个已连接 client / driver”。

**Files:**
- Modify: `instance_qa/typedb_client.py`
- Modify: `instance_qa/orchestrator.py:226-250, 557-570`
- Test: `tests/instance_qa/test_typedb_client.py`
- Test: `tests/integration/test_instance_qa_stream.py`

#### 设计约束
- 不先上全局连接池。
- 第一阶段只做“单请求级复用”。
- driver 生命周期限定在一次 `run_instance_qa()` 内。

**Step 1: Write the failing test**

在 `tests/instance_qa/test_typedb_client.py` 增加：

```python
def test_execute_multiple_queries_reuses_connected_driver(monkeypatch):
    client = TypeDBClient(...)
    client.connect()

    client.execute_readonly('match ...; get $root;')
    client.execute_readonly('match ...; get $root;')

    assert client._driver is not None
    # 再配合 fake driver 断言 connect 仅发生一次
```

再补一个 orchestrator 层测试，要求单个请求只 connect/close 一次。

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/instance_qa/test_typedb_client.py -q
```

Expected: FAIL，因为 orchestrator 还在每条 query 自己建 client。

**Step 3: Write minimal implementation**

在 `instance_qa/typedb_client.py` 中给 `TypeDBClient` 增加上下文能力：

```python
class TypeDBClient:
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False
```

在 `instance_qa/orchestrator.py` 中改为：

```python
config = load_typedb_config()
with TypeDBClient(config) as typedb_client:
    initial_rows = _execute_fact_queries(initial_queries, schema_registry, fact_query_records, typedb_client)
    ...
```

并把：
- `_execute_fact_queries(...)`
- `_run_typeql_readonly(...)`

都改成接收已连接的 `typedb_client`。

**Step 4: Run tests to verify they pass**

Run:
```bash
pytest tests/instance_qa/test_typedb_client.py tests/integration/test_instance_qa_stream.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/typedb_client.py instance_qa/orchestrator.py tests/instance_qa/test_typedb_client.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: reuse typedb client per instance qa request"
```

#### 预期效果
- TypeDB 查询阶段延时预计下降：20% ~ 40%
- 整链路总时延预计下降：10% ~ 25%
- 对 `expand_graph` 和 propagation 场景收益更明显

---

### P3：同轮独立查询受控并发（中优先级）
**目标：** 不改 propagation 轮次逻辑，只在“同一轮内部”的独立 neighbor queries 上做受控并发。

**Files:**
- Modify: `instance_qa/orchestrator.py:226-250`
- Modify: `instance_qa/typedb_client.py`（若需要增加按 driver 开新 transaction 的安全接口）
- Test: `tests/integration/test_instance_qa_stream.py`

#### 设计约束
- `resolve_anchor` 先串行。
- `collect_neighbors` 同轮可并发。
- propagation 的轮与轮之间保持串行依赖。
- 并发度必须可配置，例如：`INSTANCE_QA_QUERY_CONCURRENCY=4`。
- 如果 driver / transaction 并发安全性不明确，则每个 worker 使用独立 transaction，不共享 transaction 对象。

**Step 1: Write the failing test**

新增一个调度层测试，例如用 fake `_run_typeql_readonly(...)` 验证：

```python
def test_execute_fact_queries_runs_neighbor_queries_in_parallel(monkeypatch):
    ...
    assert max_in_flight > 1
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/integration/test_instance_qa_stream.py::test_execute_fact_queries_runs_neighbor_queries_in_parallel -q
```

Expected: FAIL，因为当前实现完全串行。

**Step 3: Write minimal implementation**

在 `instance_qa/orchestrator.py` 中把 `_execute_fact_queries(...)` 拆成：

```python
def _execute_fact_queries(...):
    anchor_queries = [q for q in queries if q.purpose == 'resolve_anchor']
    neighbor_queries = [q for q in queries if q.purpose != 'resolve_anchor']
    ...
```

对 `neighbor_queries` 使用小并发线程池：

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=query_concurrency) as pool:
    ...
```

注意：
- 单个 query 内仍保持只读事务
- 结果回填时保持 deterministic 排序

**Step 4: Run tests to verify it passes**

Run:
```bash
pytest tests/integration/test_instance_qa_stream.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/orchestrator.py instance_qa/typedb_client.py tests/integration/test_instance_qa_stream.py
git commit -m "feat: parallelize independent typedb queries per wave"
```

#### 预期效果
- 对 `expand_graph` 场景的 TypeDB 检索阶段再下降：10% ~ 30%
- 对整链路总时延再下降：5% ~ 15%
- 对 `anchor_only` 场景帮助较小

---

### P4：明确暂不优先做的大查询合并
**目标：** 把“不做什么”写清楚，避免实现时走偏。

**不建议当前优先做：**
- 把多个 neighbor queries 合成一个超级大 TypeQL
- 提前重写 `typedb_client.py` 的 query shape parser / mapper 去适配复杂多形态合并结果

**原因：**
- 当前 `typedb_client.py` 的 `_parse_query_shape / _build_fetch_query / _map_concept_documents` 是按单查询形态设计的
- 大查询合并会显著提高 mapper 复杂度
- 回归风险高，收益不一定先于 P1 / P2 / P3 体现

更合理的替代是：
- 先做连接复用
- 再做同轮受控并发
- 如仍不够，再评估“单事务执行多条 query”

---

## 推荐实施顺序
1. P0 可观测性与回归护栏
2. P1 外部锚点索引召回
3. P2 TypeDB 请求级连接复用
4. P3 同轮独立查询受控并发
5. P4 暂不做大查询合并

---

## 预期总体收益
如果 P1 + P2 都完成，保守预期：

- 整条实例问答链路总时延下降：30% ~ 60%

其中：
- 明确实例属性问答收益最大
- 复杂影响分析问答也会明显受益，但还会受 propagation 和 answer 生成阶段影响

---

## 验收标准
### 功能正确性
- `POD-001的状态是什么？` 仍能稳定命中正确实例
- `L1-A机房断电一周，会有哪些影响？` 仍能稳定扩展出正确实例链路
- router / ranker / answer 行为不退化

### 性能结果
- 阶段耗时中：
  - `anchor_resolution_ms` 显著下降
  - `typedb_query_ms` 显著下降
- 端到端平均时延较现状下降

### 稳定性
- 无新增 router failure
- 无 TypeDB 连接泄漏
- 并发执行下结果顺序和内容保持稳定
