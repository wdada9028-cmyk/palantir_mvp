# TQL Input To Markdown Conversion Design

**Date:** 2026-03-23

## Goal
让现有 `--input-file` 同时支持 `.md` 和 `.tql`：`.md` 继续直接走当前构图流程，`.tql` 先用大模型转换成兼容当前 parser 的 markdown，并把生成出的 markdown 文件落盘保存后再继续走现有流程。

## Existing Context
当前系统所有主入口都默认输入是 markdown：
- `pipelines/build_ontology_pipeline.py` 直接 `read_text()` 再调用 `parse_definition_markdown(...)`
- `server/ontology_http_app.py` 也直接把 `input_file` 当 markdown 读取
- `cli.py` 的 `build-ontology` / `serve-ontology` 都把 `--input-file` 传给上述逻辑

这意味着如果输入是 `.tql`，当前流程会直接失败，而且 `serve-ontology` 与 `build-ontology` 的行为也会不一致地各自复制输入处理逻辑。

## Chosen Approach
新增一个独立的“输入解析适配层”：
- `.md`：直接返回原始文件路径
- `.tql`：调用 OpenAI-compatible / Qwen 接口，把 TQL 转成当前 markdown DSL，然后保存为同目录下的 `<stem>.converted.md`
- 之后无论原始输入是什么，后续构图与 HTTP 流程都只消费 markdown 路径

这样现有 parser / graph builder / writer / export 基本不动，只在入口前加一层格式解析与转换。

## File Output Policy
对于 `.tql` 输入，转换结果固定落盘到原文件同目录：
- `ontology.tql` -> `ontology.converted.md`

规则：
- 每次运行都覆盖同名 `.converted.md`
- 不写入 `output/`，避免把“输入转换产物”和“构图输出产物”混在一起
- `.md` 输入不新增任何文件

## Components

### 1. `pipelines/tql_to_markdown.py`
职责：
- 读取 `.tql` 文本
- 调用 Qwen/OpenAI-compatible chat completion
- 返回纯 markdown 内容

约束：
- 复用现有环境变量风格：`QWEN_API_BASE` / `QWEN_API_KEY` / `QWEN_MODEL`
- 输出必须是当前 `parse_definition_markdown(...)` 可消费的 markdown
- 不允许返回解释性文字、代码围栏或前后缀说明
- LLM 失败、配置缺失、空输出时直接报错

建议 API：
```python
def convert_tql_to_markdown(tql_text: str, *, source_file: str, timeout_s: float = 30.0) -> str:
    ...
```

### 2. `pipelines/input_file_resolver.py`
职责：
- 统一判断输入文件类型
- `.md` 直接透传
- `.tql` 调用 converter 并写出 `<stem>.converted.md`
- 返回后续应读取的 markdown 文件路径

建议 API：
```python
def resolve_input_to_markdown(input_file: str | Path) -> Path:
    ...
```

### 3. `pipelines/build_ontology_pipeline.py`
改造点：
- 在读取输入文件前先调用 `resolve_input_to_markdown(...)`
- 后续继续用现有 markdown parser / graph builder / writer
- 返回值中建议增加：
  - `resolved_input_file`
  - 若原始输入是 `.tql`，再增加 `converted_markdown_file`

这样调用方能明确知道本次实际消费的是哪个 markdown 文件。

### 4. `server/ontology_http_app.py`
改造点：
- `create_app(input_file=...)` 也先走 `resolve_input_to_markdown(...)`
- 这样 `serve-ontology --input-file xxx.tql` 会和 `build-ontology` 行为一致

### 5. `cli.py`
改造点：
- 主要更新 help 文案，把 “ontology definition markdown file” 改成 “markdown or TQL ontology definition file”
- CLI 逻辑本身可不做格式判断，继续依赖 pipeline / server 统一处理

## Prompt Contract For TQL Conversion
System prompt 必须强约束：
- 你要把 TQL 转成当前项目的 ontology markdown definition format
- 只输出 markdown 正文
- 不输出解释、注释、代码围栏
- 如果信息不足，尽量生成最接近 parser 约束的结构化 markdown，而不是自然语言说明

User prompt 应包含：
- 原始 `.tql` 文本
- 最小 markdown 结构说明
- 明确要求输出可直接被 parser 消费

## Error Handling
- `.md` 输入：完全不触发 LLM，也不依赖 Qwen 配置
- `.tql` 输入：
  - 缺少 `QWEN_API_BASE` / `QWEN_API_KEY` -> 直接抛错
  - LLM 超时 / HTTP 错误 / 空输出 -> 直接抛错
  - 生成出的 markdown 若 parser 后续失败 -> 保留 `.converted.md`，并继续抛 parser 错误，便于人工排查
- 不做静默 fallback

## Testing Strategy

### Build flow tests
- `.md` 输入时不调用 converter，直接产出 ontology artifacts
- `.tql` 输入时调用 converter，写出 `<stem>.converted.md`，再产出 ontology artifacts
- `.tql` 且配置缺失 / converter 失败时直接报错

### HTTP flow tests
- `create_app(input_file=*.tql)` 时使用转换后的 markdown 构建 app
- `.converted.md` 文件被创建
- `/ontology` 与 `/api/graph` 正常可用

### Unit tests
- `resolve_input_to_markdown()`：覆盖 `.md` passthrough 与 `.tql` conversion path
- `convert_tql_to_markdown()`：覆盖请求 payload、错误处理、纯文本输出清洗

## Why This Approach
- 现有 markdown pipeline 不被打散
- `build-ontology` 和 `serve-ontology` 共享一套输入适配逻辑
- `.tql` 的新增复杂度被隔离在独立模块中
- 后续如果再支持 `.json` / `.yaml` 等输入，只需继续扩展 resolver
