from pathlib import Path

import cloud_delivery_ontology_palantir.pipelines.build_ontology_pipeline as pipeline_module
from cloud_delivery_ontology_palantir.cli import main


def test_build_ontology_cli_generates_outputs(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    input_file = next(root.glob('*????v2.md'))
    output_dir = tmp_path / 'output'
    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert (output_dir / 'ontology.json').exists()
    assert (output_dir / 'schema_summary.json').exists()
    assert (output_dir / 'ontology.html').exists()


def test_build_ontology_cli_with_tql_uses_pipeline_resolution_before_build(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.tql'
    input_file.write_text('SELECT * FROM ontology;', encoding='utf-8')
    converted_md = tmp_path / 'ontology.converted.md'
    root = Path(__file__).resolve().parents[2]
    sample_md = next(root.glob('*v2.md'))
    converted_md.write_text(sample_md.read_text(encoding='utf-8'), encoding='utf-8')
    output_dir = tmp_path / 'output'

    resolver_calls: list[Path] = []

    def fake_resolve_input_to_markdown(path: str | Path) -> Path:
        resolver_calls.append(Path(path))
        return converted_md

    monkeypatch.setattr(pipeline_module, 'resolve_input_to_markdown', fake_resolve_input_to_markdown, raising=False)

    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert resolver_calls == [input_file]
    assert (output_dir / 'ontology.json').exists()
    assert (output_dir / 'schema_summary.json').exists()
    assert (output_dir / 'ontology.html').exists()


def test_cli_help_text_keeps_tql_only_for_build_and_markdown_for_serve(capsys):
    assert main(['build-ontology', '--help']) == 0
    build_help = capsys.readouterr().out
    assert '.md' in build_help
    assert '.tql' in build_help

    assert main(['serve-ontology', '--help']) == 0
    serve_help = capsys.readouterr().out
    assert 'markdown file' in serve_help
    assert '.tql' not in serve_help
