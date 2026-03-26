from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
from cloud_delivery_ontology_palantir.ontology.definition_models import ObjectTypeSpec, OntologyDefinitionSpec, PropertySpec


DESC_LABEL = '\u4e2d\u6587\u91ca\u4e49'
SEMANTIC_LABEL = '\u8bed\u4e49\u5b9a\u4e49'
KEY_PROPERTIES_LABEL = '\u5173\u952e\u5c5e\u6027'
NOTES_LABEL = '\u8bf4\u660e'
NAMING_LABEL = '\u547d\u540d\u5efa\u8bae'
EXTRA_NOTES_LABEL = '\u8865\u5145\u8bf4\u660e'

_SAMPLE_MARKDOWN = f"""# Demo Ontology

## 4. Object Types
## 4.1 Project Layer
### `Project`
{DESC_LABEL}: Project object.
{SEMANTIC_LABEL}: Project defines delivery scope.
{KEY_PROPERTIES_LABEL}:
- `project_id`: Project identifier

### `Building`
{DESC_LABEL}: Building object.
{SEMANTIC_LABEL}: Building hosts project space.
{KEY_PROPERTIES_LABEL}:
- `building_id`: Building identifier

### `PoD`
{DESC_LABEL}: PoD object.
{SEMANTIC_LABEL}: PoD is core delivery unit.
{KEY_PROPERTIES_LABEL}:
- `pod_id`: PoD identifier

## 5. Link Types
### 5.1 Project Relations
- `Project HAS Building`: Project contains building
- `Project DELIVERS PoD`: Project delivers PoD
"""


_SAMPLE_TQL = """define
attribute project-id, value string;
attribute building-id, value string;
attribute pod-id, value string;
relation project-building,
  relates owner-project,
  relates owned-building;
relation project-pod,
  relates owner-project,
  relates owned-pod;
entity project,
  owns project-id @key,
  plays project-building:owner-project,
  plays project-pod:owner-project;
entity building,
  owns building-id @key,
  plays project-building:owned-building;
entity pod,
  owns pod-id @key,
  plays project-pod:owned-pod;
"""


def _load_skill_module():
    root = Path(__file__).resolve().parents[2]
    script_path = root / '.agents' / 'skills' / 'tql-md-reviser' / 'scripts' / 'revise_tql_markdown.py'
    if not script_path.exists():
        pytest.fail(f'Missing skill script: {script_path}')

    spec = importlib.util.spec_from_file_location('tql_md_reviser_script', script_path)
    if spec is None or spec.loader is None:
        pytest.fail(f'Unable to load skill script module from: {script_path}')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_structure_anchor_is_stable_when_only_descriptions_change():
    parse_definition_markdown(_SAMPLE_MARKDOWN, source_file='sample.md')
    module = _load_skill_module()

    changed_markdown = (
        _SAMPLE_MARKDOWN
        .replace('Project object.', 'Project master object.')
        .replace('Building hosts project space.', 'Building hosts shared project space.')
    )

    assert changed_markdown != _SAMPLE_MARKDOWN
    original_anchors = module.compute_structure_anchors(_SAMPLE_MARKDOWN)
    changed_anchors = module.compute_structure_anchors(changed_markdown)

    assert original_anchors == changed_anchors


def test_structure_anchor_changes_when_object_heading_changes():
    parse_definition_markdown(_SAMPLE_MARKDOWN, source_file='sample.md')
    module = _load_skill_module()

    changed_heading = _SAMPLE_MARKDOWN.replace('### `Building`', '### `BuildingV2`')

    original_anchors = module.compute_structure_anchors(_SAMPLE_MARKDOWN)
    changed_anchors = module.compute_structure_anchors(changed_heading)

    assert original_anchors != changed_anchors


def test_revise_generates_revised_markdown_and_report_files(tmp_path: Path):
    parse_definition_markdown(_SAMPLE_MARKDOWN, source_file='sample.md')
    module = _load_skill_module()

    tql_file = tmp_path / 'schema.tql'
    md_file = tmp_path / 'current.md'
    revised_file = tmp_path / 'current.revised.md'
    report_file = tmp_path / 'current.revision-report.md'
    tql_file.write_text(_SAMPLE_TQL, encoding='utf-8')
    md_file.write_text(_SAMPLE_MARKDOWN, encoding='utf-8')

    result = module.revise_markdown_from_tql(
        tql_file=tql_file,
        markdown_file=md_file,
        revised_file=revised_file,
        report_file=report_file,
        max_retries=2,
    )

    assert revised_file.exists()
    assert report_file.exists()
    assert result['status'] == 'success'


def test_revised_markdown_is_parser_compatible(tmp_path: Path):
    parse_definition_markdown(_SAMPLE_MARKDOWN, source_file='sample.md')
    module = _load_skill_module()

    tql_file = tmp_path / 'schema.tql'
    md_file = tmp_path / 'current.md'
    revised_file = tmp_path / 'current.revised.md'
    report_file = tmp_path / 'current.revision-report.md'
    tql_file.write_text(_SAMPLE_TQL, encoding='utf-8')
    md_file.write_text(_SAMPLE_MARKDOWN, encoding='utf-8')

    module.revise_markdown_from_tql(
        tql_file=tql_file,
        markdown_file=md_file,
        revised_file=revised_file,
        report_file=report_file,
        max_retries=2,
    )

    text = revised_file.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(revised_file))

    assert len(spec.object_types) >= 3
    assert len(spec.relations) >= 2


def test_extract_parse_error_returns_line_and_message():
    module = _load_skill_module()

    err = ValueError('Line 42: malformed relation entry, expected `Source RELATION Target`')
    details = module.extract_parse_error(err)

    assert details['line_no'] == 42
    assert 'malformed relation entry' in details['message']


def test_group_objects_fallback_group_does_not_double_hash_in_render():
    module = _load_skill_module()

    spec = OntologyDefinitionSpec(
        title='Demo',
        object_types=[
            ObjectTypeSpec(
                name='LooseObject',
                group='',
                chinese_description='Loose object.',
                semantic_definition='Loose semantic.',
                key_properties=[PropertySpec(name='loose_id', description='Loose identifier', line_no=1)],
            )
        ],
    )

    rendered = module.render_definition_markdown(spec)

    assert '## ## 4.9 Imported Objects' not in rendered
    assert '## 4.9 Imported Objects' in rendered


def test_revise_preserves_notes_naming_extra_labels_round_trip(tmp_path: Path):
    module = _load_skill_module()

    markdown_text = f"""# Demo Ontology

## 4. Object Types
## 4.1 Project Layer
### `Project`
{DESC_LABEL}: Project object.
{KEY_PROPERTIES_LABEL}:
- `project_id`: Project identifier
{NOTES_LABEL}:
- note item
{NAMING_LABEL}:
- naming item
{EXTRA_NOTES_LABEL}:
- extra item

## 5. Link Types
### 5.1 Project Relations
- `Project HAS Project`: self relation
"""

    tql_text = """define
attribute project-id, value string;
relation project-self,
  relates owner-project,
  relates owned-project;
entity project,
  owns project-id @key,
  plays project-self:owner-project,
  plays project-self:owned-project;
"""

    tql_file = tmp_path / 'schema.tql'
    md_file = tmp_path / 'current.md'
    revised_file = tmp_path / 'current.revised.md'
    report_file = tmp_path / 'current.revision-report.md'
    tql_file.write_text(tql_text, encoding='utf-8')
    md_file.write_text(markdown_text, encoding='utf-8')

    result = module.revise_markdown_from_tql(
        tql_file=tql_file,
        markdown_file=md_file,
        revised_file=revised_file,
        report_file=report_file,
    )

    revised = revised_file.read_text(encoding='utf-8')
    assert result['status'] == 'success'
    assert f'{NOTES_LABEL}:' in revised
    assert f'{NAMING_LABEL}:' in revised
    assert f'{EXTRA_NOTES_LABEL}:' in revised
    assert '- note item' in revised
    assert '- naming item' in revised
    assert '- extra item' in revised


def test_report_omits_final_parser_error_after_successful_repair(tmp_path: Path):
    module = _load_skill_module()

    tql_file = tmp_path / 'schema.tql'
    md_file = tmp_path / 'current.md'
    revised_file = tmp_path / 'current.revised.md'
    report_file = tmp_path / 'current.revision-report.md'
    tql_file.write_text(_SAMPLE_TQL, encoding='utf-8')
    md_file.write_text(_SAMPLE_MARKDOWN, encoding='utf-8')

    original_render = module.render_definition_markdown

    def broken_render(spec, **kwargs):
        text = original_render(spec, **kwargs)
        return text.replace('- `project_id`: Project identifier', '- `project_id` Project identifier', 1)

    module.render_definition_markdown = broken_render
    try:
        result = module.revise_markdown_from_tql(
            tql_file=tql_file,
            markdown_file=md_file,
            revised_file=revised_file,
            report_file=report_file,
            max_retries=2,
        )
    finally:
        module.render_definition_markdown = original_render

    report = report_file.read_text(encoding='utf-8')
    assert result['status'] == 'success'
    assert '## Final Parser Error' not in report
    assert 'attempt 1: failed' in report
    assert 'attempt 2: success' in report


def test_minimal_repair_only_changes_target_line():
    module = _load_skill_module()
    markdown_text = f"""# Demo Ontology

## 4. Object Types
## 4.1 Project Layer
### `Project`
{KEY_PROPERTIES_LABEL}:
- `project_id` Project identifier

## 5. Link Types
### 5.1 Project Relations
- `Project HAS Project`: self relation
"""

    repaired = module._apply_minimal_repair(
        markdown_text,
        {
            'line_no': 7,
            'message': 'expected backticked named item, got: `project_id` Project identifier',
            'exception_type': '_ParseError',
            'raw': 'Line 7: expected backticked named item, got: `project_id` Project identifier',
        },
    )

    before_lines = markdown_text.splitlines()
    after_lines = repaired.splitlines()

    assert before_lines[:6] == after_lines[:6]
    assert before_lines[7:] == after_lines[7:]
    assert after_lines[6] == '- `project_id`: Project identifier'


def test_parser_contract_examples_use_only_colon_separators():
    contract = Path('.agents/skills/tql-md-reviser/references/parser-contract.md').read_text(encoding='utf-8')
    assert '?description' not in contract
    assert '`- `prop_name`: description`' in contract
    assert '`- `Source RELATION Target`: description`' in contract


def test_skill_rule_is_unambiguous_and_forbids_question_separator():
    skill_text = Path('.agents/skills/tql-md-reviser/SKILL.md').read_text(encoding='utf-8')
    assert 'Use `:` for parser labels and list-item separators; never use `?`.' in skill_text
    assert 'never use `?`' in skill_text
    assert 'Use `:` or `?`' not in skill_text


def test_parser_alignment_rejects_question_separator_in_label_and_named_item():
    module = _load_skill_module()
    assert module._is_label_line(f'{DESC_LABEL}?', DESC_LABEL) is False
    assert module._BACKTICKED_NAMED_RE.match('`project_id`? Project identifier') is None
