from pathlib import Path

from cloud_delivery_ontology_palantir.ontology.definition_graph_builder import build_definition_graph
from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown


def test_graph_builder_creates_object_and_metric_nodes_from_real_markdown():
    root = Path(__file__).resolve().parents[2]
    markdown_path = next(root.glob('*核心决策v2.md'))
    spec = parse_definition_markdown(markdown_path.read_text(encoding='utf-8'), source_file=markdown_path.name)
    graph = build_definition_graph(spec)
    assert graph.metadata['graph_kind'] == 'ontology_definition_graph'
    assert graph.get_object('object_type:PoD').type == 'ObjectType'
    assert graph.get_object('derived_metric:latest_safe_arrival_time').type == 'DerivedMetric'
