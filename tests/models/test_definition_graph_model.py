from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject


def test_definition_graph_serializes_metadata_and_alias_fields():
    graph = OntologyGraph(metadata={'graph_kind': 'ontology_definition_graph'})
    graph.add_object(OntologyObject(id='object_type:Project', type='ObjectType', name='Project'))
    payload = graph.to_dict()
    assert payload['metadata']['graph_kind'] == 'ontology_definition_graph'
    assert payload['nodes'][0]['name'] == 'Project'
    assert payload['objects'][0]['id'] == 'object_type:Project'
