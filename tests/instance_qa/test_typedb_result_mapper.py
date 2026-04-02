from cloud_delivery_ontology_palantir.instance_qa.typedb_result_mapper import map_typedb_rows_to_fact_pack


def test_map_typedb_rows_to_fact_pack_groups_instances_by_entity():
    rows = [
        {'_entity': 'PoD', 'pod_code': 'POD-001', 'pod_status': 'active'},
        {'_entity': 'PoD', 'pod_code': 'POD-002', 'pod_status': 'planned'},
        {'_entity': 'WorkAssignment', 'assignment_id': 'WA-001', 'assignment_status': 'open'},
    ]

    fact_pack = map_typedb_rows_to_fact_pack(rows, purpose='collect_neighbors')

    assert fact_pack['metadata']['purpose'] == 'collect_neighbors'
    assert len(fact_pack['instances']['PoD']) == 2
    assert len(fact_pack['instances']['WorkAssignment']) == 1
