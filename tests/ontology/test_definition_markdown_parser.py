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
