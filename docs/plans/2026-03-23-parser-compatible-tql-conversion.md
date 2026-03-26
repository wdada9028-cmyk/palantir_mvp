# Parser-Compatible TQL Conversion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** ? `.tql` ????????? `parse_definition_markdown()` ???????? markdown ??????? TypeDB schema ? build/serve ??????????

**Architecture:** ????????????? markdown ?????????????? TQL schema ?? + ?????? markdown ?? + parser ????LLM ??????????????????????????? `.tql -> .converted.md -> parse_definition_markdown()` ?????

**Tech Stack:** Python 3.11, pathlib, dataclasses, regex, pytest

---

### Task 1: ??? TQL ? parser ?? markdown ?? RED ??

**Files:**
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/pipelines/test_input_file_resolver.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/integration/test_build_ontology_cli.py`

**Step 1: Write the failing tests**

? `tests/pipelines/test_input_file_resolver.py` ???
```python
def test_convert_tql_file_to_markdown_file_renders_parser_compatible_markdown_for_real_schema(tmp_path: Path):
    from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file

    root = Path(__file__).resolve().parents[2]
    input_file = root / 'typedb_schema_v4.tql'

    output_file = convert_tql_file_to_markdown_file(input_file)
    text = output_file.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(output_file))

    names = {item.name for item in spec.object_types}
    triples = {(rel.source_type, rel.relation, rel.target_type) for rel in spec.relations}
    assert 'Project' in names
    assert 'PoD' in names
    assert ('Project', 'HAS', 'Building') in triples
```

? `tests/integration/test_build_ontology_cli.py` ???
```python
def test_build_ontology_cli_accepts_real_tql_schema_file(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    input_file = root / 'typedb_schema_v4.tql'
    output_dir = tmp_path / 'output'

    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert (output_dir / 'ontology.json').exists()
```

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/pipelines/test_input_file_resolver.py::test_convert_tql_file_to_markdown_file_renders_parser_compatible_markdown_for_real_schema -v
pytest tests/integration/test_build_ontology_cli.py::test_build_ontology_cli_accepts_real_tql_schema_file -v
```
Expected: FAIL??? `.converted.md` ?????? parser?

**Step 3: Commit**

```bash
git add tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py
git commit -m "test: cover parser compatible tql conversion"
```

### Task 2: ?? TQL schema ??????? markdown

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/tql_schema_models.py`
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/tql_schema_extractor.py`
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/tql_schema_renderer.py`
- Modify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/tql_to_markdown.py`
- Test: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/pipelines/test_input_file_resolver.py`

**Step 1: Add TQL schema models**

? `pipelines/tql_schema_models.py` ???
```python
@dataclass(slots=True)
class TqlAttributeSpec:
    name: str
    value_type: str

@dataclass(slots=True)
class TqlRelationTypeSpec:
    name: str
    roles: list[str]

@dataclass(slots=True)
class TqlEntityTypeSpec:
    name: str
    parent: str | None
    attributes: list[str]

@dataclass(slots=True)
class TqlSchemaSpec:
    title: str
    attributes: dict[str, TqlAttributeSpec]
    relations: dict[str, TqlRelationTypeSpec]
    entities: list[TqlEntityTypeSpec]
```

**Step 2: Extract schema from TQL**

? `pipelines/tql_schema_extractor.py` ???
- ?? `attribute ... value ...;`
- ???? `relation ... relates ...;`
- ???? `entity ... owns ... plays ...;`
- ?? `sub` ????
- ?? `owns` ?????? entity attributes
- ???????

?????
```python
def extract_tql_schema(text: str, *, source_file: str) -> TqlSchemaSpec:
    ...
```

**Step 3: Render parser-compatible markdown**

? `pipelines/tql_schema_renderer.py` ?????????
- `# <title>`
- `## 4. Object Types`
- `## 4.1 Imported TypeDB Schema`
- ?? entity:
  - `### `Name``
  - `?????...`
  - `?????...`??????? `TypeDB entity, subtype of ...`?
  - `?????`
  - `- `prop_name`?TypeDB attribute <attr-name> (<value-type>)`
- `## 5. Link Types`
- `### 5.1 Imported TypeDB Relations`
- ?? relation name + roles ?? parser ?? triple?
  - ??? relation ?? `project-building` ?? `Project HAS Building`
  - ????????? relation??????? triple
- ?????????????? entity ???

?????
```python
def render_tql_schema_as_definition_markdown(schema: TqlSchemaSpec) -> str:
    ...
```

**Step 4: Replace LLM-first conversion path**

? `pipelines/tql_to_markdown.py`?
- ????/HTTP ????????? `convert_tql_file_to_markdown_file()` ??????
  1. `extract_tql_schema(...)`
  2. `render_tql_schema_as_definition_markdown(...)`
  3. `parse_definition_markdown(...)` ????
  4. ?? `<stem>.converted.md`
- `convert_tql_to_markdown(...)` ????? extractor+renderer??? CLI/serve ?????? LLM

**Step 5: Run focused tests**

Run:
```bash
pytest tests/pipelines/test_input_file_resolver.py::test_convert_tql_file_to_markdown_file_renders_parser_compatible_markdown_for_real_schema -v
pytest tests/integration/test_build_ontology_cli.py::test_build_ontology_cli_accepts_real_tql_schema_file -v
```
Expected: PASS?

**Step 6: Commit**

```bash
git add pipelines/tql_schema_models.py pipelines/tql_schema_extractor.py pipelines/tql_schema_renderer.py pipelines/tql_to_markdown.py tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py
git commit -m "feat: render parser compatible markdown from tql"
```

### Task 3: ?????? TQL build/serve ???

**Files:**
- Modify if needed: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/server/test_ontology_http_app.py`
- Verify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/typedb_schema_v4.tql`

**Step 1: Add HTTP app regression if needed**

??? server ??????? `.tql` ???????
```python
def test_create_app_accepts_real_tql_schema_file():
    root = Path(__file__).resolve().parents[2]
    app = create_app(input_file=root / 'typedb_schema_v4.tql')
    client = TestClient(app)
    assert client.get('/api/graph').status_code == 200
```

**Step 2: Run focused verification**

Run:
```bash
pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q
```
Expected: PASS?

**Step 3: Run full verification**

Run:
```bash
pytest tests -q
```
Expected: PASS?

**Step 4: Real smoke verification**

Run:
```bash
python -m cloud_delivery_ontology_palantir.cli serve-ontology --input-file typedb_schema_v4.tql --host 127.0.0.1 --port 8000
```
Expected: ???????? `/api/graph` ?? 200?

**Step 5: Commit**

?? Task 3 ????/????????
