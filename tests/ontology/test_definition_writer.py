from pathlib import Path

from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph
from cloud_delivery_ontology_palantir.ontology.definition_writer import write_definition_outputs


def test_writer_creates_ontology_json_and_schema_summary(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '本体建模 v2', 'counts': {'object_type_count': 1}})
    paths = write_definition_outputs(tmp_path, graph)
    assert (tmp_path / 'ontology.json').exists()
    assert (tmp_path / 'schema_summary.json').exists()
    assert paths['ontology_json'].name == 'ontology.json'
