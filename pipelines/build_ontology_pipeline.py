from __future__ import annotations

from pathlib import Path

from cloud_delivery_ontology_palantir.graph_export import export_graph_pdf, export_interactive_graph_html
from cloud_delivery_ontology_palantir.ontology.definition_graph_builder import build_definition_graph
from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
from cloud_delivery_ontology_palantir.ontology.definition_writer import write_definition_outputs
from cloud_delivery_ontology_palantir.pipelines.input_file_resolver import resolve_input_to_markdown


def build_ontology_from_markdown(
    input_file: str | Path,
    output_dir: str | Path,
    *,
    generate_html: bool = True,
    generate_pdf: bool = False,
) -> dict[str, object]:
    input_path = Path(input_file)
    output_path = Path(output_dir)

    resolved_input_path = resolve_input_to_markdown(input_path)
    text = resolved_input_path.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(resolved_input_path))

    graph = build_definition_graph(spec)
    paths = write_definition_outputs(output_path, graph)
    if generate_html:
        paths['ontology_html'] = export_interactive_graph_html(graph, output_path / 'ontology.html', title=graph.metadata.get('title', 'Ontology Graph'))
    if generate_pdf:
        paths['ontology_pdf'] = export_graph_pdf(graph, output_path / 'ontology.pdf', title=graph.metadata.get('title', 'Ontology Graph'))

    result: dict[str, object] = {
        'graph': graph,
        'resolved_input_file': resolved_input_path,
        **paths,
    }
    if resolved_input_path.resolve() != input_path.resolve():
        result['converted_markdown_file'] = resolved_input_path

    return result
