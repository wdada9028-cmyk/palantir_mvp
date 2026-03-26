from __future__ import annotations

from pathlib import Path

from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
from cloud_delivery_ontology_palantir.pipelines.tql_schema_extractor import extract_tql_schema
from cloud_delivery_ontology_palantir.pipelines.tql_schema_renderer import render_tql_schema_as_definition_markdown


def _render_parser_compatible_markdown(tql_text: str, *, source_file: str) -> str:
    schema = extract_tql_schema(tql_text, source_file=source_file)
    markdown = render_tql_schema_as_definition_markdown(schema)
    parse_definition_markdown(markdown, source_file=source_file)
    return markdown


def convert_tql_file_to_markdown_file(input_file: str | Path) -> Path:
    input_path = Path(input_file)
    tql_text = input_path.read_text(encoding='utf-8')
    markdown = _render_parser_compatible_markdown(tql_text, source_file=str(input_path))
    parse_definition_markdown(markdown, source_file=str(input_path))

    output_path = input_path.with_name(f'{input_path.stem}.converted.md')
    output_path.write_text(markdown, encoding='utf-8')
    return output_path
