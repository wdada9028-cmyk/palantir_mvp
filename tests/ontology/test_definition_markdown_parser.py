from pathlib import Path

import pytest

from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown


@pytest.fixture
def real_markdown_text() -> str:
    root = Path(__file__).resolve().parents[2]
    markdown_path = next(root.glob('*核心决策v2.md'))
    return markdown_path.read_text(encoding='utf-8')


def test_parser_reads_project_and_pod_object_types_from_real_markdown(real_markdown_text: str):
    spec = parse_definition_markdown(real_markdown_text, source_file='real.md')
    names = {item.name for item in spec.object_types}
    assert 'Project' in names
    assert 'PoD' in names


def test_parser_reads_link_types_and_derived_metrics_from_real_markdown(real_markdown_text: str):
    spec = parse_definition_markdown(real_markdown_text, source_file='real.md')
    triples = {(rel.source_type, rel.relation, rel.target_type) for rel in spec.relations}
    metric_names = {metric.name for metric in spec.derived_metrics}
    assert ('Project', 'HAS', 'Building') in triples
    assert 'latest_safe_arrival_time' in metric_names


def test_parser_ignores_horizontal_rule_when_parsing_mainline(real_markdown_text: str):
    spec = parse_definition_markdown(real_markdown_text, source_file='real.md')
    assert '---' not in spec.mainline


def test_parser_rejects_relation_with_undefined_target():
    bad_text = """## 4. Object Types
## 4.1 项目与目标层
### `Project`
中文释义：项目。
关键属性：
- `project_id`：项目ID

## 5. Link Types
### 5.1 项目与空间关系
- `Project HAS MissingType`：错误
"""
    with pytest.raises(ValueError):
        parse_definition_markdown(bad_text, source_file='bad.md')



def test_parser_accepts_new_flat_object_types_format():
    text = """# typedb_schema_v4\n\n## Object Types\uff08\u5b9e\u4f53\uff09\n\n### `Project`\n\u4e2d\u6587\u91ca\u4e49\uff1a\u9879\u76ee\n\u5173\u952e\u5c5e\u6027\uff1a\n- `project_id`\uff1a\u6240\u5c5e\u9879\u76eeID\n\n### `Building`\n\u4e2d\u6587\u91ca\u4e49\uff1a\u697c\u680b\n\u5173\u952e\u5c5e\u6027\uff1a\n- `building_id`\uff1a\u6240\u5c5e\u697c\u680bID\n\n## Link Types\uff08\u5173\u7cfb\uff09\n- `Project HAS Building`\uff1a\u9879\u76ee\u5173\u8054\u697c\u680b\n"""

    spec = parse_definition_markdown(text, source_file='typedb_schema_v4.converted.md')

    assert spec.title == 'typedb_schema_v4'
    assert [item.name for item in spec.object_types] == ['Project', 'Building']
    assert spec.object_types[0].chinese_description == '\u9879\u76ee'
    assert spec.object_types[0].semantic_definition is None
    assert spec.object_types[0].key_properties[0].name == 'project_id'
    assert spec.object_types[0].key_properties[0].description == '\u6240\u5c5e\u9879\u76eeID'
    assert spec.relations[0].source_type == 'Project'
    assert spec.relations[0].target_type == 'Building'
