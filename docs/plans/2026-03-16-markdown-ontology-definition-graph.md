# Markdown Ontology Definition Graph Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current LLM-driven ontology build flow with a deterministic markdown-to-definition-graph pipeline that reads `D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md` and outputs the final ontology definition graph as JSON and HTML.

**Architecture:** The new system will parse the markdown as a constrained DSL, convert the parsed definition spec into a single `OntologyGraph` containing `ObjectType` and `DerivedMetric` nodes plus explicit link edges, and then render or serialize that graph through dedicated writer/exporter modules. Legacy LLM extraction, retrieval, and scheduling paths will be removed after the new parser, graph builder, CLI, and tests are working.

**Tech Stack:** Python 3, `dataclasses`, `pathlib`, `argparse`, `json`, `pytest`, browser-based HTML rendering in `D:/????/AI?????/??????/palantir_mvp/export/graph_export.py`

---

### Task 1: Extend the graph model for metadata-backed definition graphs

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/models/ontology.py`
- Modify: `D:/????/AI?????/??????/palantir_mvp/schema.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/models/test_definition_graph_model.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject


def test_definition_graph_serializes_metadata_and_alias_fields():
    graph = OntologyGraph(metadata={'graph_kind': 'ontology_definition_graph'})
    graph.add_object(OntologyObject(id='object_type:Project', type='ObjectType', name='Project'))
    payload = graph.to_dict()
    assert payload['metadata']['graph_kind'] == 'ontology_definition_graph'
    assert payload['nodes'][0]['name'] == 'Project'
    assert payload['objects'][0]['id'] == 'object_type:Project'
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/models/test_definition_graph_model.py" -v`
Expected: FAIL because `OntologyGraph` does not yet accept or serialize `metadata`.

**Step 3: Write minimal implementation**

```python
@dataclass(slots=True)
class OntologyGraph:
    objects: dict[str, OntologyObject] = field(default_factory=dict)
    relations: list[OntologyRelation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        objects = [obj.to_dict() for obj in self.objects.values()]
        relations = [relation.to_dict() for relation in self.relations]
        return {
            'metadata': dict(self.metadata),
            'objects': objects,
            'relations': relations,
            'nodes': objects,
            'edges': relations,
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/models/test_definition_graph_model.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/models/ontology.py" "D:/????/AI?????/??????/palantir_mvp/schema.py" "D:/????/AI?????/??????/palantir_mvp/tests/models/test_definition_graph_model.py"
git commit -m "refactor: add metadata support to ontology graph"
```

If `git` still reports that this workspace is not a repository, skip the commit and note that limitation in the execution log.

### Task 2: Add definition-spec dataclasses for parsed markdown content

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/ontology/definition_models.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_models.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.ontology.definition_models import ObjectTypeSpec, PropertySpec


def test_object_type_spec_holds_property_specs():
    prop = PropertySpec(name='project_id', description='??ID', line_no=1)
    obj = ObjectTypeSpec(name='Project', group='4.1 ??????', key_properties=[prop])
    assert obj.key_properties[0].name == 'project_id'
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_models.py" -v`
Expected: FAIL because `definition_models.py` does not exist.

**Step 3: Write minimal implementation**

```python
@dataclass(slots=True)
class PropertySpec:
    name: str
    description: str
    line_no: int

@dataclass(slots=True)
class ObjectTypeSpec:
    name: str
    group: str
    chinese_description: str = ''
    semantic_definition: str | None = None
    key_properties: list[PropertySpec] = field(default_factory=list)
```

Then add the remaining spec classes required by the design: `NamedValueSpec`, `RelationSpec`, `DerivedMetricSpec`, and `OntologyDefinitionSpec`.

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_models.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/ontology/definition_models.py" "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_models.py"
git commit -m "feat: add ontology definition spec models"
```

### Task 3: Parse object-type sections from the markdown definition file

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/ontology/definition_markdown_parser.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown


def test_parser_reads_project_and_pod_object_types_from_real_markdown():
    text = Path(r'D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md').read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file='real.md')
    names = {item.name for item in spec.object_types}
    assert 'Project' in names
    assert 'PoD' in names
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py::test_parser_reads_project_and_pod_object_types_from_real_markdown" -v`
Expected: FAIL because the parser does not exist.

**Step 3: Write minimal implementation**

Implement a line-oriented parser that:
- captures the document title from `# ...`
- collects `## 2. ??????`
- collects `## 3. ????`
- enters object-type mode at `## 4. Object Types`
- creates an `ObjectTypeSpec` for each heading matching `### \`Name\``
- fills `????`, `????`, `????`, `????`, `????`, `???????`, and note sections

Use helper functions such as:

```python
def _parse_backticked_name(line: str) -> str: ...
def _parse_named_item(line: str) -> tuple[str, str]: ...
def _strip_label(line: str, label: str) -> str: ...
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py::test_parser_reads_project_and_pod_object_types_from_real_markdown" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/ontology/definition_markdown_parser.py" "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py"
git commit -m "feat: parse object types from ontology markdown"
```

### Task 4: Parse link types, derived metrics, optional properties, and validation errors

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/ontology/definition_markdown_parser.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py`

**Step 1: Write the failing test**

```python
import pytest
from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown


def test_parser_reads_link_types_and_derived_metrics_from_real_markdown(real_markdown_text):
    spec = parse_definition_markdown(real_markdown_text, source_file='real.md')
    triples = {(rel.source_type, rel.relation, rel.target_type) for rel in spec.relations}
    metric_names = {metric.name for metric in spec.derived_metrics}
    assert ('Project', 'HAS', 'Building') in triples
    assert 'latest_safe_arrival_time' in metric_names


def test_parser_rejects_relation_with_undefined_target():
    bad_text = """## 4. Object Types
## 4.1 ??????
### `Project`
????????
?????
- `project_id`???ID

## 5. Link Types
### 5.1 ???????
- `Project HAS MissingType`???
"""
    with pytest.raises(ValueError):
        parse_definition_markdown(bad_text, source_file='bad.md')
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py" -v`
Expected: FAIL because relations, metrics, or validation are incomplete.

**Step 3: Write minimal implementation**

Extend the parser to:
- parse `## 4.7 MVP ?????????`
- parse `## 5. Link Types` relation triples with group labels
- parse `## 6. ??????`
- validate duplicate object names, duplicate property names, duplicate triples, and undefined relation endpoints
- raise `ValueError` with line-numbered messages

Example validation helper:

```python
def _fail(line_no: int, message: str) -> None:
    raise ValueError(f'Line {line_no}: {message}')
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/ontology/definition_markdown_parser.py" "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py"
git commit -m "feat: validate relations and derived metrics in ontology markdown"
```

### Task 5: Build the final definition graph from the parsed spec

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/ontology/definition_graph_builder.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_graph_builder.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
from cloud_delivery_ontology_palantir.ontology.definition_graph_builder import build_definition_graph


def test_graph_builder_creates_object_and_metric_nodes_from_real_markdown():
    text = Path(r'D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md').read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file='real.md')
    graph = build_definition_graph(spec)
    assert graph.metadata['graph_kind'] == 'ontology_definition_graph'
    assert graph.get_object('object_type:PoD').type == 'ObjectType'
    assert graph.get_object('derived_metric:latest_safe_arrival_time').type == 'DerivedMetric'
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_graph_builder.py" -v`
Expected: FAIL because the graph builder does not exist.

**Step 3: Write minimal implementation**

```python
def build_definition_graph(spec: OntologyDefinitionSpec) -> OntologyGraph:
    graph = OntologyGraph(metadata={
        'graph_kind': 'ontology_definition_graph',
        'title': spec.title,
        'source_file': spec.source_file,
        'boundaries': list(spec.boundaries),
        'mainline': list(spec.mainline),
        'optional_properties': [...],
        'optional_property_notes': list(spec.optional_property_notes),
    })
    # add object_type nodes
    # add derived_metric nodes
    # add relation edges
    # add counts
    return graph
```

Use node IDs `object_type:<Name>` and `derived_metric:<Name>`.

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_graph_builder.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/ontology/definition_graph_builder.py" "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_graph_builder.py"
git commit -m "feat: build ontology definition graph from parsed markdown"
```

### Task 6: Write ontology.json and schema_summary.json outputs

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/ontology/definition_writer.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_writer.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph
from cloud_delivery_ontology_palantir.ontology.definition_writer import write_definition_outputs


def test_writer_creates_ontology_json_and_schema_summary(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2', 'counts': {'object_type_count': 1}})
    paths = write_definition_outputs(tmp_path, graph)
    assert (tmp_path / 'ontology.json').exists()
    assert (tmp_path / 'schema_summary.json').exists()
    assert paths['ontology_json'].name == 'ontology.json'
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_writer.py" -v`
Expected: FAIL because the writer does not exist.

**Step 3: Write minimal implementation**

Write `ontology.json` from `graph.to_dict()` and `schema_summary.json` from a compact subset of `graph.metadata`, for example:

```python
summary = {
    'title': graph.metadata.get('title'),
    'source_file': graph.metadata.get('source_file'),
    'counts': graph.metadata.get('counts', {}),
    'mainline': graph.metadata.get('mainline', []),
    'groups': sorted({obj.attributes.get('group', '') for obj in graph.objects.values() if obj.attributes.get('group')})
}
```

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_writer.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/ontology/definition_writer.py" "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_writer.py"
git commit -m "feat: write ontology definition outputs"
```

### Task 7: Rewrite the HTML exporter around definition-graph semantics

**Files:**
- Modify: `D:/????/AI?????/??????/palantir_mvp/export/graph_export.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject
from cloud_delivery_ontology_palantir.export.graph_export import export_interactive_graph_html


def test_exported_html_renders_definition_node_attributes(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2'})
    graph.add_object(OntologyObject(
        id='object_type:Project',
        type='ObjectType',
        name='Project',
        attributes={'group': '4.1 ??????', 'key_properties': [{'name': 'project_id', 'description': '??ID'}]}
    ))
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')
    assert 'project_id' in text
    assert '????' in text
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py" -v`
Expected: FAIL because the exporter still expects a schedule and old task-centric behavior.

**Step 3: Write minimal implementation**

Rewrite the exporter so that:
- `export_interactive_graph_html(graph, output_html_path, title=...)` accepts only the graph
- node colors derive from `attributes['group']` or `node.type`
- the detail panel renders dynamic `attributes`
- the panel shows relation summary first, then expandable relation detail
- the relation filter dropdown is built from the actual relation labels in `graph.relations`

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/export/graph_export.py" "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py"
git commit -m "feat: render ontology definition graph in html exporter"
```

### Task 8: Add the new build_ontology pipeline and CLI command

**Files:**
- Create: `D:/????/AI?????/??????/palantir_mvp/pipelines/build_ontology_pipeline.py`
- Modify: `D:/????/AI?????/??????/palantir_mvp/cli.py`
- Test: `D:/????/AI?????/??????/palantir_mvp/tests/integration/test_build_ontology_cli.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
from cloud_delivery_ontology_palantir.cli import main


def test_build_ontology_cli_generates_outputs(tmp_path: Path):
    input_file = Path(r'D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md')
    output_dir = tmp_path / 'output'
    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert (output_dir / 'ontology.json').exists()
    assert (output_dir / 'schema_summary.json').exists()
    assert (output_dir / 'ontology.html').exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_build_ontology_cli.py" -v`
Expected: FAIL because the command does not exist.

**Step 3: Write minimal implementation**

Implement:

```python
def build_ontology_from_markdown(input_file, output_dir, generate_html=True, generate_pdf=False):
    text = Path(input_file).read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(input_file))
    graph = build_definition_graph(spec)
    paths = write_definition_outputs(output_dir, graph)
    if generate_html:
        paths['ontology_html'] = export_interactive_graph_html(graph, Path(output_dir) / 'ontology.html')
    return {'graph': graph, **paths}
```

Then update `cli.py` to expose only the new ontology-build command path.

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_build_ontology_cli.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add "D:/????/AI?????/??????/palantir_mvp/pipelines/build_ontology_pipeline.py" "D:/????/AI?????/??????/palantir_mvp/cli.py" "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_build_ontology_cli.py"
git commit -m "feat: add build-ontology cli workflow"
```

### Task 9: Remove legacy LLM / retrieval / scheduling paths and dead tests

**Files:**
- Delete: `D:/????/AI?????/??????/palantir_mvp/prompts.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/extractor.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/pipeline.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/retriever.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/sample_data.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/ask_three_questions.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/ontology.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/ontology_mapper.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/ontology_registry.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/ontology/builder.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/ontology/mapper.py`
- Delete: `D:/????/AI?????/??????/palantir_mvp/ontology/registry.py`
- Delete directories / tests tied to old flow under `answering`, `ingestion`, `planning`, `search`, and matching `tests/answering`, `tests/ingestion`, `tests/llm`, `tests/pipelines`, `tests/search`

**Step 1: Write the failing verification test**

```python
from pathlib import Path


def test_legacy_prompt_file_has_been_removed():
    assert not Path(r'D:/????/AI?????/??????/palantir_mvp/prompts.py').exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_legacy_files_removed.py" -v`
Expected: FAIL because the old files still exist.

**Step 3: Delete the legacy files and update any imports that still reference them**

After deletions, confirm the remaining tree matches the new architecture:
- `cli.py`
- `models/ontology.py`
- `schema.py`
- `export/graph_export.py`
- `ontology/definition_*.py`
- `pipelines/build_ontology_pipeline.py`
- new parser/builder/CLI tests

**Step 4: Run test to verify it passes**

Run: `pytest "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_legacy_files_removed.py" -v`
Expected: PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove legacy ontology build pipeline"
```

### Task 10: Run the end-to-end verification suite and smoke-build the real markdown

**Files:**
- No new source files
- Verification targets: all new tests and one real CLI build

**Step 1: Run the focused test suite**

Run:

```bash
pytest   "D:/????/AI?????/??????/palantir_mvp/tests/models/test_definition_graph_model.py"   "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_models.py"   "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_markdown_parser.py"   "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_graph_builder.py"   "D:/????/AI?????/??????/palantir_mvp/tests/ontology/test_definition_writer.py"   "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_definition_graph_export.py"   "D:/????/AI?????/??????/palantir_mvp/tests/integration/test_build_ontology_cli.py"   -v
```

Expected: all PASS

**Step 2: Run a real build against the markdown source**

Run:

```bash
python -m cloud_delivery_ontology_palantir.cli build-ontology --input-file "D:/????/AI?????/??????/palantir_mvp/[????] ????2?????v2.md" --output-dir "D:/????/AI?????/??????/palantir_mvp/output"
```

Expected: `ontology.json`, `schema_summary.json`, and `ontology.html` exist under the output directory.

**Step 3: Manually smoke-check the HTML prototype**

Open `D:/????/AI?????/??????/palantir_mvp/output/ontology.html` and verify:
- the graph loads
- clicking `PoD` shows its key properties
- relation summary appears collapsed by default
- relation details can expand
- derived metrics can be shown or hidden

**Step 4: Commit**

```bash
git add -A
git commit -m "test: verify markdown ontology definition graph workflow"
```

If the workspace is still not a git repository, skip the commit and record that the verification completed without commit support.
