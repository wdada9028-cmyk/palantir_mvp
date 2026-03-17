from __future__ import annotations

from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation

from .definition_models import OntologyDefinitionSpec


def build_definition_graph(spec: OntologyDefinitionSpec) -> OntologyGraph:
    graph = OntologyGraph(
        metadata={
            'graph_kind': 'ontology_definition_graph',
            'title': spec.title,
            'source_file': spec.source_file,
            'boundaries': list(spec.boundaries),
            'mainline': list(spec.mainline),
            'optional_properties': [
                {'name': prop.name, 'description': prop.description, 'line_no': prop.line_no}
                for prop in spec.optional_properties
            ],
            'optional_property_notes': list(spec.optional_property_notes),
        }
    )

    for obj in spec.object_types:
        graph.add_object(
            OntologyObject(
                id=f'object_type:{obj.name}',
                type='ObjectType',
                name=obj.name,
                attributes={
                    'group': obj.group,
                    'chinese_description': obj.chinese_description,
                    'semantic_definition': obj.semantic_definition,
                    'key_properties': [
                        {'name': prop.name, 'description': prop.description, 'line_no': prop.line_no}
                        for prop in obj.key_properties
                    ],
                    'status_values': [
                        {'name': item.name, 'description': item.description, 'line_no': item.line_no}
                        for item in obj.status_values
                    ],
                    'rules': list(obj.rules),
                    'notes': list(obj.notes),
                    'suggested_violation_types': [
                        {'name': item.name, 'description': item.description, 'line_no': item.line_no}
                        for item in obj.suggested_violation_types
                    ],
                    'source_lines': {
                        'start': obj.source_start_line,
                        'end': obj.source_end_line,
                    },
                },
            )
        )

    for metric in spec.derived_metrics:
        graph.add_object(
            OntologyObject(
                id=f'derived_metric:{metric.name}',
                type='DerivedMetric',
                name=metric.name,
                attributes={
                    'group': '6. 关键派生指标',
                    'description': metric.description,
                    'source_lines': {
                        'start': metric.line_no,
                        'end': metric.line_no,
                    },
                },
            )
        )

    for relation in spec.relations:
        graph.add_relation(
            OntologyRelation(
                source_id=f'object_type:{relation.source_type}',
                target_id=f'object_type:{relation.target_type}',
                relation=relation.relation,
                attributes={
                    'group': relation.group,
                    'description': relation.description,
                    'source_lines': {
                        'start': relation.line_no,
                        'end': relation.line_no,
                    },
                },
            )
        )

    graph.metadata['counts'] = {
        'object_type_count': len(spec.object_types),
        'derived_metric_count': len(spec.derived_metrics),
        'relation_count': len(spec.relations),
        'total_node_count': len(graph.objects),
    }
    return graph
