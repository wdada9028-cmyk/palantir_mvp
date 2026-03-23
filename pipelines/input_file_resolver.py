from __future__ import annotations

from pathlib import Path

from cloud_delivery_ontology_palantir.pipelines.tql_to_markdown import convert_tql_file_to_markdown_file


def resolve_input_to_markdown(input_file: str | Path) -> Path:
    input_path = Path(input_file)
    suffix = input_path.suffix.lower()

    if suffix == '.md':
        return input_path
    if suffix == '.tql':
        return convert_tql_file_to_markdown_file(input_path)

    raise ValueError(f'Unsupported input file type: {input_path}. Only .md and .tql are supported.')
