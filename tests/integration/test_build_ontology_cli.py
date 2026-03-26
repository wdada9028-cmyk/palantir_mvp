from pathlib import Path

_SAMPLE_TQL_SCHEMA = """define
attribute project-id, value string;
attribute building-id, value string;
attribute pod-id, value string;
relation project-building,
  relates owner-project,
  relates owned-building;
relation project-pod,
  relates owner-project,
  relates owned-pod;
entity project,
  owns project-id @key,
  plays project-building:owner-project,
  plays project-pod:owner-project;
entity building,
  owns building-id @key,
  plays project-building:owned-building;
entity pod,
  owns pod-id @key,
  plays project-pod:owned-pod;
"""

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


def test_cli_help_text_advertises_md_and_tql_for_build_and_serve(capsys):
    assert main(['build-ontology', '--help']) == 0
    build_help = capsys.readouterr().out
    assert '.md' in build_help
    assert '.tql' in build_help

    assert main(['serve-ontology', '--help']) == 0
    serve_help = capsys.readouterr().out
    assert '.md' in serve_help
    assert '.tql' in serve_help



def test_build_ontology_cli_accepts_native_tql_conversion_without_qwen_env(tmp_path: Path, monkeypatch):
    monkeypatch.delenv('QWEN_API_BASE', raising=False)
    monkeypatch.delenv('QWEN_API_KEY', raising=False)

    input_file = tmp_path / 'schema.tql'
    input_file.write_text(_SAMPLE_TQL_SCHEMA, encoding='utf-8')
    output_dir = tmp_path / 'output'

    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert (output_dir / 'ontology.json').exists()
    assert (tmp_path / 'schema.converted.md').exists()
