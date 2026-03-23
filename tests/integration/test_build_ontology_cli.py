from pathlib import Path

import cloud_delivery_ontology_palantir.cli as cli_module
from cloud_delivery_ontology_palantir.cli import main


def test_build_ontology_cli_generates_outputs(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    input_file = next(root.glob('*核心决策v2.md'))
    output_dir = tmp_path / 'output'
    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert (output_dir / 'ontology.json').exists()
    assert (output_dir / 'schema_summary.json').exists()
    assert (output_dir / 'ontology.html').exists()


def test_build_ontology_cli_resolves_tql_input_before_build(tmp_path: Path, monkeypatch):
    input_file = tmp_path / 'ontology.tql'
    input_file.write_text('SELECT * FROM ontology;', encoding='utf-8')
    converted_file = tmp_path / 'ontology.converted.md'
    converted_file.write_text('# converted', encoding='utf-8')
    output_dir = tmp_path / 'output'

    resolver_calls: list[Path] = []
    build_calls: list[dict[str, object]] = []

    def fake_resolve_input_file(path: Path) -> Path:
        resolver_calls.append(Path(path))
        return converted_file

    def fake_build_ontology_from_markdown(
        input_file: str | Path,
        output_dir: str | Path,
        *,
        generate_html: bool,
        generate_pdf: bool,
    ) -> dict[str, object]:
        build_calls.append(
            {
                'input_file': Path(input_file),
                'output_dir': Path(output_dir),
                'generate_html': generate_html,
                'generate_pdf': generate_pdf,
            }
        )
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ontology_json = out_dir / 'ontology.json'
        schema_summary_json = out_dir / 'schema_summary.json'
        ontology_html = out_dir / 'ontology.html'
        ontology_json.write_text('{}', encoding='utf-8')
        schema_summary_json.write_text('{}', encoding='utf-8')
        ontology_html.write_text('<html></html>', encoding='utf-8')
        return {
            'ontology_json': ontology_json,
            'schema_summary_json': schema_summary_json,
            'ontology_html': ontology_html,
        }

    monkeypatch.setattr(cli_module, 'resolve_input_file', fake_resolve_input_file, raising=False)
    monkeypatch.setattr(cli_module, 'build_ontology_from_markdown', fake_build_ontology_from_markdown)

    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert resolver_calls == [input_file]
    assert build_calls[0]['input_file'] == converted_file
