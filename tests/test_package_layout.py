from importlib import import_module


def test_new_subpackages_import():
    assert import_module("cloud_delivery_ontology_palantir.models")
    assert import_module("cloud_delivery_ontology_palantir.ontology")
    assert import_module("cloud_delivery_ontology_palantir.export")
    assert import_module("cloud_delivery_ontology_palantir.pipelines")
