from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from .evidence_models import EvidenceEdge, InstanceEvidence

@dataclass(slots=True)
class EvidenceSubgraph:
    nodes: dict[str, list[InstanceEvidence]] = field(default_factory=dict)
    edges: list[EvidenceEdge] = field(default_factory=list)
    paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            'nodes': {
                entity: [item.to_dict() for item in items]
                for entity, items in self.nodes.items()
            },
            'edges': [edge.to_dict() for edge in self.edges],
            'paths': list(self.paths),
        }


def build_evidence_subgraph(fact_pack: dict[str, object]) -> EvidenceSubgraph:
    instances = fact_pack.get('instances') if isinstance(fact_pack, dict) else {}
    links = fact_pack.get('links') if isinstance(fact_pack, dict) else {}
    metadata = fact_pack.get('metadata') if isinstance(fact_pack, dict) else {}

    node_map: dict[str, list[InstanceEvidence]] = {}

    if isinstance(instances, dict):
        for entity, items in instances.items():
            if not isinstance(items, list):
                continue
            values: list[InstanceEvidence] = []
            for row in items:
                if not isinstance(row, dict):
                    continue
                iid = str(row.get('iid') or row.get('_iid') or '').strip()
                attributes = {
                    key: value
                    for key, value in row.items()
                    if key not in {'iid', '_iid'}
                }
                business_keys = _extract_business_keys(attributes)
                evidence = InstanceEvidence(
                    entity=str(entity),
                    iid=iid,
                    business_keys=business_keys,
                    attributes=attributes,
                    schema_context=None,
                    paths=[],
                )
                values.append(evidence)
            if values:
                node_map[str(entity)] = values

    edge_values: list[EvidenceEdge] = []
    if isinstance(links, list):
        for item in links:
            if not isinstance(item, dict):
                continue
            try:
                edge_values.append(
                    EvidenceEdge(
                        source_entity=str(item['source_entity']),
                        source_id=str(item['source_id']),
                        relation=str(item['relation']),
                        target_entity=str(item['target_entity']),
                        target_id=str(item['target_id']),
                    )
                )
            except Exception:
                continue

    paths = _build_paths_from_anchor(edge_values, metadata if isinstance(metadata, dict) else {})
    return EvidenceSubgraph(nodes=node_map, edges=edge_values, paths=paths)


def _extract_business_keys(attributes: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in attributes.items():
        normalized = str(key or '').strip().lower()
        if normalized == 'id' or normalized.endswith('_id') or normalized.endswith('-id'):
            result[str(key)] = value
    return result


def _build_paths_from_anchor(edges: list[EvidenceEdge], metadata: dict[str, object]) -> list[str]:
    anchor = metadata.get('anchor') if isinstance(metadata, dict) else None
    if not isinstance(anchor, dict):
        return []
    anchor_entity = str(anchor.get('entity') or '').strip()
    anchor_id = str(anchor.get('id') or '').strip()
    if not anchor_entity or not anchor_id:
        return []

    start = (anchor_entity, anchor_id)
    graph: dict[tuple[str, str], list[tuple[tuple[str, str], str, str]]] = {}
    for edge in edges:
        source = (edge.source_entity, edge.source_id)
        target = (edge.target_entity, edge.target_id)
        graph.setdefault(source, []).append((target, edge.relation, 'forward'))
        graph.setdefault(target, []).append((source, edge.relation, 'reverse'))

    queue = deque([(start, f'{anchor_entity}({anchor_id})')])
    seen = {start}
    paths: list[str] = []
    while queue:
        node, path = queue.popleft()
        for neighbor, relation, direction in graph.get(node, []):
            if neighbor in seen:
                continue
            seen.add(neighbor)
            if direction == 'forward':
                segment = f'{path} --{relation}--> {neighbor[0]}({neighbor[1]})'
            else:
                segment = f'{path} <--{relation}-- {neighbor[0]}({neighbor[1]})'
            paths.append(segment)
            queue.append((neighbor, segment))
    return paths
