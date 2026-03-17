from __future__ import annotations

import json
from pathlib import Path

from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph



def write_definition_outputs(output_dir: str | Path, graph: OntologyGraph) -> dict[str, Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    ontology_json = output_path / 'ontology.json'
    ontology_json.write_text(json.dumps(graph.to_dict(), ensure_ascii=False, indent=2), encoding='utf-8')

    groups = sorted({obj.attributes.get('group') for obj in graph.objects.values() if obj.attributes.get('group')})
    summary = {
        'title': graph.metadata.get('title'),
        'source_file': graph.metadata.get('source_file'),
        'counts': graph.metadata.get('counts', {}),
        'mainline': graph.metadata.get('mainline', []),
        'groups': groups,
    }
    schema_summary_json = output_path / 'schema_summary.json'
    schema_summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    return {
        'ontology_json': ontology_json,
        'schema_summary_json': schema_summary_json,
    }
