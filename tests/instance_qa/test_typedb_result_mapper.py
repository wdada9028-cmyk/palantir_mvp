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



def test_map_typedb_rows_to_fact_pack_extracts_relation_links_and_counts():
    rows = [
        {
            '_entity': 'WorkAssignment',
            'assignment_id': 'WA-001',
            '_source_entity': 'WorkAssignment',
            '_source_id': 'WA-001',
            '_relation': 'ASSIGNS',
            '_target_entity': 'PoD',
            '_target_id': 'POD-001',
        }
    ]

    fact_pack = map_typedb_rows_to_fact_pack(rows, purpose='collect_neighbors')

    assert fact_pack['counts']['WorkAssignment'] == 1
    assert fact_pack['metadata']['total_rows'] == 1
    assert fact_pack['links'] == [
        {
            'source_entity': 'WorkAssignment',
            'source_id': 'WA-001',
            'relation': 'ASSIGNS',
            'target_entity': 'PoD',
            'target_id': 'POD-001',
        }
    ]


def test_map_typedb_rows_to_fact_pack_dedupes_duplicate_instance_rows():
    rows = [
        {
            '_entity': 'PoD',
            'pod_code': 'POD-001',
            'pod_status': 'active',
            '_source_entity': 'WorkAssignment',
            '_source_id': 'WA-001',
            '_relation': 'ASSIGNS',
            '_target_entity': 'PoD',
            '_target_id': 'POD-001',
        },
        {
            '_entity': 'PoD',
            'pod_code': 'POD-001',
            'pod_status': 'active',
            '_source_entity': 'WorkAssignment',
            '_source_id': 'WA-002',
            '_relation': 'ASSIGNS',
            '_target_entity': 'PoD',
            '_target_id': 'POD-001',
        },
    ]

    fact_pack = map_typedb_rows_to_fact_pack(rows, purpose='collect_neighbors')

    assert fact_pack['counts']['PoD'] == 1
    assert fact_pack['instances']['PoD'] == [
        {
            'pod_code': 'POD-001',
            'pod_status': 'active',
        }
    ]


def test_map_typedb_rows_to_fact_pack_uses_entity_specific_identifier_priority():
    rows = [
        {
            '_entity': 'WorkAssignment',
            'assignment_id': 'WA-001',
            'pod_code': 'POD-001',
            'assignment_status': 'open',
        },
        {
            '_entity': 'WorkAssignment',
            'assignment_id': 'WA-001',
            'pod_code': 'POD-002',
            'assignment_status': 'open',
        },
    ]

    fact_pack = map_typedb_rows_to_fact_pack(rows, purpose='collect_neighbors')

    assert fact_pack['counts']['WorkAssignment'] == 1
    assert fact_pack['instances']['WorkAssignment'] == [
        {
            'assignment_id': 'WA-001',
            'pod_code': 'POD-001',
            'assignment_status': 'open',
        }
    ]
