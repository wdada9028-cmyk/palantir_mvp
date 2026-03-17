from pathlib import Path
import subprocess
import sys

from cloud_delivery_ontology_palantir.cli import main


def test_cli_exposes_serve_ontology_subcommand():
    rc = main([
        'serve-ontology',
        '--help',
    ])
    assert rc == 0


def test_python_m_cli_help_works_from_workspace_root():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, '-m', 'cloud_delivery_ontology_palantir.cli', 'serve-ontology', '--help'],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
