from cloud_delivery_ontology_palantir.ontology.definition_models import ObjectTypeSpec, PropertySpec


def test_object_type_spec_holds_property_specs():
    prop = PropertySpec(name='project_id', description='项目ID', line_no=1)
    obj = ObjectTypeSpec(name='Project', group='4.1 项目与目标层', key_properties=[prop])
    assert obj.key_properties[0].name == 'project_id'
