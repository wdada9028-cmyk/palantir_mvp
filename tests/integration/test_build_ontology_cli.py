from pathlib import Path

from cloud_delivery_ontology_palantir.cli import main


def test_build_ontology_cli_generates_outputs(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    input_file = next(root.glob('*核心决策v2.md'))
    output_dir = tmp_path / 'output'
    assert main(['build-ontology', '--input-file', str(input_file), '--output-dir', str(output_dir)]) == 0
    assert (output_dir / 'ontology.json').exists()
    assert (output_dir / 'schema_summary.json').exists()
    assert (output_dir / 'ontology.html').exists()
