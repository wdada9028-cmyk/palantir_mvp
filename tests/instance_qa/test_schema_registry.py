from pathlib import Path

from cloud_delivery_ontology_palantir.instance_qa.schema_registry import build_schema_registry
from cloud_delivery_ontology_palantir.ontology.definition_graph_builder import build_definition_graph
from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown


def _build_demo_graph():
    text = """# demo

## Object Types

### `Room`
中文释义：机房
关键属性：
- `room_id`：机房ID
- `rack_slot`：机柜槽位
- `room_status`：机房状态

### `WorkAssignment`
中文释义：施工分配
关键属性：
- `assignment_id`：分配ID

## Link Types
- `WorkAssignment OCCURS_IN Room`：施工分配发生于机房
"""
    spec = parse_definition_markdown(text, source_file='demo.md')
    return build_definition_graph(spec)


def test_build_schema_registry_collects_entity_attributes_and_key_attributes():
    graph = _build_demo_graph()

    registry = build_schema_registry(graph)

    assert 'Room' in registry.entities
    room = registry.entities['Room']
    assert room.attributes == ['room_id', 'rack_slot', 'room_status']
    assert room.key_attributes == ['room_id', 'rack_slot', 'room_status']


def test_build_schema_registry_collects_directional_adjacency_and_relations():
    graph = _build_demo_graph()

    registry = build_schema_registry(graph)

    assert ('WorkAssignment', 'OCCURS_IN', 'Room') in {
        (item.source_entity, item.relation, item.target_entity)
        for item in registry.relations
    }

    room_edges = registry.adjacency['Room']
    assignment_edges = registry.adjacency['WorkAssignment']

    assert any(item.relation == 'OCCURS_IN' and item.direction == 'in' and item.neighbor_entity == 'WorkAssignment' for item in room_edges)
    assert any(item.relation == 'OCCURS_IN' and item.direction == 'out' and item.neighbor_entity == 'Room' for item in assignment_edges)



def test_build_schema_registry_resolves_physical_typedb_relation_and_roles(tmp_path: Path):
    tql_file = tmp_path / 'schema.tql'
    tql_file.write_text(
        """define
attribute room-id, value string;
attribute assignment-id, value string;
relation work-assignment-room,
  relates assignment-record,
  relates assigned-room;
entity room,
  owns room-id @key,
  plays work-assignment-room:assigned-room;
entity work-assignment,
  owns assignment-id @key,
  plays work-assignment-room:assignment-record;
""",
        encoding='utf-8',
    )

    graph = _build_demo_graph()
    graph.metadata['typedb_schema_input_file'] = str(tql_file)

    registry = build_schema_registry(graph)
    room_edge = next(item for item in registry.adjacency['Room'] if item.neighbor_entity == 'WorkAssignment')

    assert room_edge.typedb_relation == 'work-assignment-room'
    assert room_edge.entity_role == 'assigned-room'
    assert room_edge.neighbor_role == 'assignment-record'
