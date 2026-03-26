from importlib import import_module
from pathlib import Path


_SAMPLE_TQL_SCHEMA = """define
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


_SAMPLE_CONSTRAINT_TQL_SCHEMA = """define
attribute room-id, value string;
attribute milestone-id, value string;
relation room-milestone-constraint,
  relates constraining-room-milestone,
  relates constrained-room;
relation floor-room-milestone-aggregation,
  relates owner-floor-milestone,
  relates member-room-milestone;
entity room,
  owns room-id @key,
  plays room-milestone-constraint:constrained-room;
entity milestone @abstract,
  owns milestone-id @key;
entity room-milestone sub milestone,
  plays room-milestone-constraint:constraining-room-milestone,
  plays floor-room-milestone-aggregation:member-room-milestone;
entity floor-milestone sub milestone,
  plays floor-room-milestone-aggregation:owner-floor-milestone;
"""


_SAMPLE_TEMPLATE_LINK_TQL_SCHEMA = """define
attribute template-id, value string;
attribute dependency-template-id, value string;
attribute activity-id, value string;
attribute pod-schedule-id, value string;
attribute pod-id, value string;
relation activity-template-instance,
  relates source-template,
  relates generated-instance;
relation activity-instance-dependency,
  relates predecessor-activity,
  relates successor-activity;
relation template-dependency-link,
  relates dependency-record,
  relates predecessor-template,
  relates successor-template;
relation pod-schedule-pod,
  relates owning-schedule,
  relates scheduled-pod;
entity activity-template,
  owns template-id @key,
  plays activity-template-instance:source-template,
  plays template-dependency-link:predecessor-template,
  plays template-dependency-link:successor-template;
entity activity-dependency-template,
  owns dependency-template-id @key,
  plays template-dependency-link:dependency-record;
entity activity-instance,
  owns activity-id @key,
  plays activity-template-instance:generated-instance,
  plays activity-instance-dependency:predecessor-activity,
  plays activity-instance-dependency:successor-activity;
entity pod-schedule,
  owns pod-schedule-id @key,
  plays pod-schedule-pod:owning-schedule;
entity pod,
  owns pod-id @key,
  plays pod-schedule-pod:scheduled-pod;
"""


def _load_resolver_module():
    return import_module('cloud_delivery_ontology_palantir.pipelines.input_file_resolver')


def test_resolve_input_to_markdown_passthrough_for_markdown_without_conversion(tmp_path: Path, monkeypatch):
    resolver_module = _load_resolver_module()
    input_file = tmp_path / 'ontology.md'
    input_file.write_text('# ontology', encoding='utf-8')

    converter_calls: list[Path] = []

    def fake_convert_tql_file_to_markdown_file(path: Path) -> Path:
        converter_calls.append(Path(path))
        return input_file.with_suffix('.converted.md')

    monkeypatch.setattr(
        resolver_module,
        'convert_tql_file_to_markdown_file',
        fake_convert_tql_file_to_markdown_file,
        raising=False,
    )

    resolved = resolver_module.resolve_input_to_markdown(input_file)

    assert resolved == input_file
    assert converter_calls == []


def test_resolve_input_to_markdown_converts_tql_into_stem_converted_markdown_in_same_directory(tmp_path: Path, monkeypatch):
    resolver_module = _load_resolver_module()
    input_file = tmp_path / 'ontology_source.tql'
    input_file.write_text('SELECT * FROM ontology;', encoding='utf-8')

    converter_calls: list[Path] = []
    converted_text = '# converted from tql\n- node: PoD\n'

    def fake_convert_tql_file_to_markdown_file(path: Path) -> Path:
        converter_calls.append(Path(path))
        output_file = Path(path).with_suffix('.converted.md')
        output_file.write_text(converted_text, encoding='utf-8')
        return output_file

    monkeypatch.setattr(
        resolver_module,
        'convert_tql_file_to_markdown_file',
        fake_convert_tql_file_to_markdown_file,
        raising=False,
    )

    resolved = resolver_module.resolve_input_to_markdown(input_file)

    expected_output = input_file.with_suffix('.converted.md')
    assert converter_calls == [input_file]
    assert resolved == expected_output
    assert expected_output.exists()
    assert expected_output.read_text(encoding='utf-8') == converted_text


def test_convert_tql_file_to_markdown_file_renders_parser_compatible_markdown(tmp_path: Path):
    from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file

    input_file = tmp_path / 'schema.tql'
    input_file.write_text(_SAMPLE_TQL_SCHEMA, encoding='utf-8')

    output_file = convert_tql_file_to_markdown_file(input_file)
    text = output_file.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(output_file))

    names = {item.name for item in spec.object_types}
    triples = {(rel.source_type, rel.relation, rel.target_type) for rel in spec.relations}
    assert output_file.name == 'schema.converted.md'
    assert 'Project' in names
    assert 'Building' in names
    assert 'PoD' in names
    assert ('Project', 'HAS', 'Building') in triples


def test_convert_tql_file_to_markdown_file_is_deterministic_without_llm_configuration(tmp_path: Path):
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file

    input_file = tmp_path / 'schema.tql'
    input_file.write_text(_SAMPLE_TQL_SCHEMA, encoding='utf-8')

    first = convert_tql_file_to_markdown_file(input_file).read_text(encoding='utf-8')
    second = convert_tql_file_to_markdown_file(input_file).read_text(encoding='utf-8')

    assert first == second


def test_convert_tql_file_to_markdown_file_skips_enhancer_and_writes_skeleton_directly(tmp_path: Path, monkeypatch):
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file, _render_parser_compatible_markdown

    input_file = tmp_path / 'schema.tql'
    input_file.write_text(_SAMPLE_TQL_SCHEMA, encoding='utf-8')
    monkeypatch.setattr(
        'cloud_delivery_ontology_palantir.pipelines.tql_to_markdown.enhance_tql_markdown',
        lambda **kwargs: (_ for _ in ()).throw(AssertionError('enhancer should not be reached')),
        raising=False,
    )

    output_file = convert_tql_file_to_markdown_file(input_file)
    expected = _render_parser_compatible_markdown(_SAMPLE_TQL_SCHEMA, source_file=str(input_file))

    assert output_file.read_text(encoding='utf-8') == expected


def test_convert_tql_file_to_markdown_file_uses_flat_object_types_headings_and_strict_property_format(tmp_path: Path):
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file

    input_file = tmp_path / 'typedb_schema_v4.tql'
    input_file.write_text(_SAMPLE_TQL_SCHEMA, encoding='utf-8')

    output_file = convert_tql_file_to_markdown_file(input_file)
    text = output_file.read_text(encoding='utf-8')

    assert text.startswith('# typedb_schema_v4\n\n## Object Types\uff08\u5b9e\u4f53\uff09\n')
    assert '## 4.1' not in text
    assert '## 4.2' not in text
    assert '### `Project`' in text
    assert '### `Building`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u5927\u697c' in text
    assert '\u4e2d\u6587\u91ca\u4e49\uff1a' in text
    assert '\u8bed\u4e49\u5b9a\u4e49\uff1a' not in text
    assert '- `project_id`\uff1a\u6240\u5c5e\u9879\u76eeID' in text
    assert '- `building_id`\uff1a\u6240\u5c5e\u5927\u697cID' in text
    assert '\n## Link Types\uff08\u5173\u7cfb\uff09\n' in text


def test_convert_tql_file_to_markdown_file_uses_business_semantic_relation_direction_for_constraint_and_aggregation(tmp_path: Path):
    from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file

    input_file = tmp_path / 'constraint_schema.tql'
    input_file.write_text(_SAMPLE_CONSTRAINT_TQL_SCHEMA, encoding='utf-8')

    output_file = convert_tql_file_to_markdown_file(input_file)
    spec = parse_definition_markdown(output_file.read_text(encoding='utf-8'), source_file=str(output_file))
    triples = {(rel.source_type, rel.relation, rel.target_type) for rel in spec.relations}

    assert ('RoomMilestone', 'CONSTRAINS', 'Room') in triples
    assert ('FloorMilestone', 'AGGREGATES', 'RoomMilestone') in triples
    assert ('Room', 'CONSTRAINS', 'RoomMilestone') not in triples


def test_convert_tql_file_to_markdown_file_renders_template_dependency_link_and_linktype_business_descriptions(tmp_path: Path):
    from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file

    input_file = tmp_path / 'template_link_schema.tql'
    input_file.write_text(_SAMPLE_TEMPLATE_LINK_TQL_SCHEMA, encoding='utf-8')

    output_file = convert_tql_file_to_markdown_file(input_file)
    text = output_file.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(output_file))
    triples = {(rel.source_type, rel.relation, rel.target_type) for rel in spec.relations}

    assert ('ActivityDependencyTemplate', 'DEFINES', 'ActivityInstance') in triples
    assert ('ActivityInstance', 'DEPENDS_ON', 'ActivityInstance') in triples
    assert ('ActivityDependencyTemplate', 'REFERENCES_PREDECESSOR', 'ActivityTemplate') not in triples
    assert ('ActivityDependencyTemplate', 'REFERENCES_SUCCESSOR', 'ActivityTemplate') not in triples
    assert '`PoDSchedule APPLIES_TO PoD`\uff1aPoD\u6392\u671f\u4f5c\u7528\u4e8ePoD' in text
    assert '`ActivityDependencyTemplate DEFINES ActivityInstance`\uff1a\u6d3b\u52a8\u4f9d\u8d56\u6a21\u677f\u5b9a\u4e49\u6d3b\u52a8\u5b9e\u4f8b' in text
    assert '`PlacementPlan REFERENCES Building`\uff1a\u843d\u4f4d\u5efa\u8bae\u65b9\u6848\u5173\u8054\u5927\u697c' in convert_tql_file_to_markdown_file(Path('typedb_schema_v4.tql')).read_text(encoding='utf-8')


def test_convert_tql_file_to_markdown_file_uses_updated_object_type_business_labels(tmp_path: Path):
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file

    input_file = tmp_path / 'typedb_schema_v4.tql'
    input_file.write_text(Path('typedb_schema_v4.tql').read_text(encoding='utf-8'), encoding='utf-8')

    output_file = convert_tql_file_to_markdown_file(input_file)
    text = output_file.read_text(encoding='utf-8')

    assert '### `Building`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u5927\u697c' in text
    assert '### `PoDPosition`\n\n\u4e2d\u6587\u91ca\u4e49\uff1aPoD\u843d\u4f4d' in text
    assert '### `Shipment`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u53d1\u8d27\u5355' in text
    assert '### `ActivityTemplate`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u6d3b\u52a8\u6a21\u677f' in text
    assert '### `ActivityDependencyTemplate`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u6d3b\u52a8\u4f9d\u8d56\u6a21\u677f' in text
    assert '### `ActivityInstance`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u6d3b\u52a8\u5b9e\u4f8b' in text
    assert '### `SLAStandard`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u6807\u51c6SLA' in text
    assert '### `Crew`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u65bd\u5de5\u961f' in text
    assert '### `WorkAssignment`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u65bd\u5de5\u5206\u914d' in text
    assert '### `PlacementPlan`\n\n\u4e2d\u6587\u91ca\u4e49\uff1a\u843d\u4f4d\u5efa\u8bae\u65b9\u6848' in text



def test_convert_tql_file_to_markdown_file_keeps_attribute_business_terms_aligned_with_entity_terms(tmp_path: Path):
    from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file

    input_file = tmp_path / 'typedb_schema_v4.tql'
    input_file.write_text(Path('typedb_schema_v4.tql').read_text(encoding='utf-8'), encoding='utf-8')

    output_file = convert_tql_file_to_markdown_file(input_file)
    text = output_file.read_text(encoding='utf-8')

    assert '- `building_id`\uff1a\u6240\u5c5e\u5927\u697cID' in text
    assert '- `building_name`\uff1a\u5927\u697c\u540d\u79f0' in text
    assert '- `position_id`\uff1aPoD\u843d\u4f4dID' in text
    assert '- `position_code`\uff1aPoD\u843d\u4f4d\u7f16\u7801' in text
    assert '- `position_status`\uff1aPoD\u843d\u4f4d\u72b6\u6001' in text
    assert '- `shipment_id`\uff1a\u53d1\u8d27\u5355ID' in text
    assert '- `shipment_no`\uff1a\u53d1\u8d27\u5355\u53f7' in text
    assert '- `shipment_status`\uff1a\u53d1\u8d27\u5355\u72b6\u6001' in text
    assert '- `planned_ship_time`\uff1a\u8ba1\u5212\u53d1\u8d27\u65f6\u95f4' in text
    assert '- `template_id`\uff1a\u6d3b\u52a8\u6a21\u677fID' in text
    assert '- `dependency_template_id`\uff1a\u6d3b\u52a8\u4f9d\u8d56\u6a21\u677fID' in text
    assert '- `activity_category`\uff1a\u6d3b\u52a8\u7c7b\u522b' in text
    assert '- `activity_id`\uff1a\u6d3b\u52a8ID' in text
    assert '- `activity_status`\uff1a\u6d3b\u52a8\u72b6\u6001' in text
    assert '- `crew_capacity_assumption`\uff1a\u65bd\u5de5\u961f\u4ea7\u80fd\u5047\u8bbe' in text
    assert '- `crew_id`\uff1a\u65bd\u5de5\u961fID' in text
    assert '- `crew_status`\uff1a\u65bd\u5de5\u961f\u72b6\u6001' in text
    assert '- `assignment_id`\uff1a\u65bd\u5de5\u5206\u914dID' in text
    assert '- `assignment_date`\uff1a\u65bd\u5de5\u5206\u914d\u65e5\u671f' in text
    assert '- `assignment_status`\uff1a\u65bd\u5de5\u5206\u914d\u72b6\u6001' in text
    assert '- `placement_plan_id`\uff1a\u843d\u4f4d\u5efa\u8bae\u65b9\u6848ID' in text
    assert '- `placement_score`\uff1a\u843d\u4f4d\u5efa\u8bae\u65b9\u6848\u8bc4\u5206' in text
