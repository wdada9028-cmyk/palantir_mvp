from pathlib import Path

import cloud_delivery_ontology_palantir


def test_imports_resolve_to_current_workspace():
    workspace = Path(__file__).resolve().parents[1]
    package_file = Path(cloud_delivery_ontology_palantir.__file__).resolve()

    assert package_file.is_relative_to(workspace)
