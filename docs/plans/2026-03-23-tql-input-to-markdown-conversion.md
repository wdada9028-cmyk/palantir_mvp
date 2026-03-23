# TQL Input To Markdown Conversion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 `build-ontology` 和 `serve-ontology` 同时支持 `.md` 与 `.tql` 输入，并在 `.tql` 场景下先用大模型生成并落盘 `.converted.md` 再复用现有 markdown 构图流程。

**Architecture:** 新增 `pipelines/tql_to_markdown.py` 与 `pipelines/input_file_resolver.py` 两层适配：converter 负责调用 Qwen/OpenAI-compatible 接口把 TQL 转成 parser 可消费的 markdown，resolver 负责判断输入类型、落盘保存 `<stem>.converted.md`、并把统一后的 markdown 路径交给现有 build/server 流程。`build_ontology_pipeline.py` 与 `server/ontology_http_app.py` 只接入 resolver，不重写现有 parser / graph builder。

**Tech Stack:** Python 3.11, pathlib, httpx, argparse, FastAPI, pytest

---

### Task 1: 为输入适配层先写失败测试

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/pipelines/test_input_file_resolver.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/integration/test_build_ontology_cli.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/server/test_ontology_http_app.py`

**Step 1: Write the failing tests**

在 `tests/pipelines/test_input_file_resolver.py` 新增：
```python
from pathlib import Path

from cloud_delivery_ontology_palantir.pipelines.input_file_resolver import resolve_input_to_markdown


def test_resolve_input_to_markdown_returns_md_path_without_conversion(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.md'
    input_file.write_text('# ontology', encoding='utf-8')

    called = {'value': False}
    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.pipelines.input_file_resolver.convert_tql_file_to_markdown_file',
        lambda *args, **kwargs: called.__setitem__('value', True),
    )

    resolved = resolve_input_to_markdown(input_file)

    assert resolved == input_file
    assert called['value'] is False


def test_resolve_input_to_markdown_converts_tql_and_writes_converted_md(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.tql'
    input_file.write_text('define entity Project;', encoding='utf-8')

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.pipelines.input_file_resolver.convert_tql_file_to_markdown_file',
        lambda path: tmp_path / 'ontology.converted.md',
    )

    resolved = resolve_input_to_markdown(input_file)

    assert resolved.name == 'ontology.converted.md'
```

在 `tests/integration/test_build_ontology_cli.py` 新增：
```python
def test_build_ontology_cli_converts_tql_input_before_build(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.tql'
    input_file.write_text('define entity Project;', encoding='utf-8')

    converted_md = tmp_path / 'ontology.converted.md'
    converted_md.write_text(MINIMAL_MARKDOWN, encoding='utf-8')

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.pipelines.build_ontology_pipeline.resolve_input_to_markdown',
        lambda path: converted_md,
    )

    output_dir = tmp_path / 'output'
    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert (output_dir / 'ontology.json').exists()
```

在 `tests/server/test_ontology_http_app.py` 新增：
```python
def test_create_app_converts_tql_input_before_loading_graph(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.tql'
    input_file.write_text('define entity Project;', encoding='utf-8')

    converted_md = tmp_path / 'ontology.converted.md'
    _write_minimal_ontology(converted_md)

    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.server.ontology_http_app.resolve_input_to_markdown',
        lambda path: converted_md,
    )

    app = create_app(input_file=input_file)
    client = TestClient(app)

    assert client.get('/ontology').status_code == 200
```

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -v
```
Expected: FAIL，报缺少 resolver 模块或导入路径不存在。

**Step 3: Commit**

```bash
git add tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py
git commit -m "test: cover tql input resolution"
```

### Task 2: 实现 TQL -> Markdown 转换器与输入解析层

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/tql_to_markdown.py`
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/input_file_resolver.py`
- Test: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/pipelines/test_input_file_resolver.py`

**Step 1: Write minimal converter implementation**

在 `pipelines/tql_to_markdown.py` 实现：
```python
from __future__ import annotations

import os
from pathlib import Path

import httpx

_DEFAULT_MODEL = 'qwen2.5-32b-instruct'


def convert_tql_to_markdown(tql_text: str, *, source_file: str, timeout_s: float = 30.0) -> str:
    api_base = os.getenv('QWEN_API_BASE', '').strip()
    api_key = os.getenv('QWEN_API_KEY', '').strip()
    if not api_base or not api_key:
        raise RuntimeError('Missing QWEN_API_BASE or QWEN_API_KEY for TQL conversion.')

    payload = {
        'model': os.getenv('QWEN_MODEL', _DEFAULT_MODEL).strip() or _DEFAULT_MODEL,
        'temperature': 0.1,
        'messages': [
            {
                'role': 'system',
                'content': (
                    'Convert the provided TQL into ontology definition markdown. '
                    'Return markdown only. No explanation. No code fences.'
                ),
            },
            {
                'role': 'user',
                'content': f'Source file: {source_file}\n\nTQL:\n{tql_text}',
            },
        ],
    }
    response = httpx.post(
        f'{api_base.rstrip("/")}/chat/completions',
        headers={'Authorization': f'Bearer {api_key}'},
        json=payload,
        timeout=timeout_s,
    )
    response.raise_for_status()
    content = response.json()['choices'][0]['message']['content']
    markdown = str(content or '').strip()
    if not markdown:
        raise RuntimeError('TQL conversion returned empty markdown.')
    return markdown.removeprefix('```markdown').removeprefix('```').removesuffix('```').strip()


def convert_tql_file_to_markdown_file(input_file: str | Path) -> Path:
    input_path = Path(input_file)
    markdown_text = convert_tql_to_markdown(input_path.read_text(encoding='utf-8'), source_file=str(input_path))
    output_path = input_path.with_suffix('.converted.md')
    output_path.write_text(markdown_text, encoding='utf-8')
    return output_path
```

**Step 2: Write minimal resolver implementation**

在 `pipelines/input_file_resolver.py` 实现：
```python
from __future__ import annotations

from pathlib import Path

from .tql_to_markdown import convert_tql_file_to_markdown_file


def resolve_input_to_markdown(input_file: str | Path) -> Path:
    input_path = Path(input_file)
    suffix = input_path.suffix.lower()
    if suffix == '.md':
        return input_path
    if suffix == '.tql':
        return convert_tql_file_to_markdown_file(input_path)
    raise ValueError(f'Unsupported input file type: {input_path.suffix}')
```

**Step 3: Run tests to verify they pass**

Run:
```bash
pytest tests/pipelines/test_input_file_resolver.py -v
```
Expected: PASS。

**Step 4: Commit**

```bash
git add pipelines/tql_to_markdown.py pipelines/input_file_resolver.py tests/pipelines/test_input_file_resolver.py
git commit -m "feat: add tql input resolver"
```

### Task 3: 接入 build pipeline 与 CLI 文案

**Files:**
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/build_ontology_pipeline.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/cli.py`
- Test: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/integration/test_build_ontology_cli.py`

**Step 1: Wire the resolver into the build pipeline**

更新 `pipelines/build_ontology_pipeline.py`：
```python
from .input_file_resolver import resolve_input_to_markdown


def build_ontology_from_markdown(...):
    input_path = Path(input_file)
    resolved_input_path = resolve_input_to_markdown(input_path)
    text = resolved_input_path.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(resolved_input_path))
    ...
    result = {
        'graph': graph,
        'resolved_input_file': resolved_input_path,
        **paths,
    }
    if resolved_input_path != input_path:
        result['converted_markdown_file'] = resolved_input_path
    return result
```

**Step 2: Update CLI help text**

在 `cli.py` 中把两个 `--input-file` help 改成：
```python
help='Path to the ontology definition markdown or TQL file'
```

**Step 3: Run tests to verify they pass**

Run:
```bash
pytest tests/integration/test_build_ontology_cli.py -v
```
Expected: PASS。

**Step 4: Commit**

```bash
git add pipelines/build_ontology_pipeline.py cli.py tests/integration/test_build_ontology_cli.py
git commit -m "feat: support tql build input"
```

### Task 4: 接入 HTTP 服务入口

**Files:**
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/server/ontology_http_app.py`
- Test: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/server/test_ontology_http_app.py`

**Step 1: Reuse the resolver in `create_app()`**

更新 `server/ontology_http_app.py`：
```python
from ..pipelines.input_file_resolver import resolve_input_to_markdown


def create_app(*, input_file: Path) -> FastAPI:
    input_path = Path(input_file)
    resolved_input_path = resolve_input_to_markdown(input_path)
    text = resolved_input_path.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(resolved_input_path))
    ...
    app.state.input_file = input_path
    app.state.resolved_input_file = resolved_input_path
```

**Step 2: Run tests to verify they pass**

Run:
```bash
pytest tests/server/test_ontology_http_app.py -v
```
Expected: PASS。

**Step 3: Commit**

```bash
git add server/ontology_http_app.py tests/server/test_ontology_http_app.py
git commit -m "feat: support tql serve input"
```

### Task 5: 补 converter 错误路径测试并做聚焦验证

**Files:**
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/pipelines/test_input_file_resolver.py`
- Modify if needed: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/tql_to_markdown.py`

**Step 1: Add failing tests for error handling**

补充：
```python
def test_convert_tql_to_markdown_raises_when_qwen_config_missing(monkeypatch):
    monkeypatch.delenv('QWEN_API_BASE', raising=False)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)
    with pytest.raises(RuntimeError, match='Missing QWEN_API_BASE or QWEN_API_KEY'):
        convert_tql_to_markdown('define entity Project;', source_file='ontology.tql')


def test_convert_tql_to_markdown_raises_when_model_returns_empty(monkeypatch):
    ...
```

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/pipelines/test_input_file_resolver.py -v
```
Expected: FAIL。

**Step 3: Implement minimal fixes if needed**

只补最小错误处理，不扩展功能。

**Step 4: Run focused verification**

Run:
```bash
pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q
```
Expected: PASS。

**Step 5: Run full verification**

Run:
```bash
pytest tests -q
```
Expected: PASS。

**Step 6: Commit**

```bash
git add pipelines/tql_to_markdown.py tests/pipelines/test_input_file_resolver.py
git commit -m "test: cover tql conversion failures"
```

仅当本步有新修改时提交。
