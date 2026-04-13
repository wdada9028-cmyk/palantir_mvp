from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest

WORKSPACE = Path(__file__).resolve().parents[1]
PACKAGE_NAME = 'cloud_delivery_ontology_palantir'
PACKAGE_INIT = WORKSPACE / '__init__.py'


def _ensure_workspace_package_alias() -> None:
    existing = sys.modules.get(PACKAGE_NAME)
    if existing is not None:
        existing_file = getattr(existing, '__file__', None)
        if existing_file and Path(existing_file).resolve() == PACKAGE_INIT.resolve():
            return
        sys.modules.pop(PACKAGE_NAME, None)

    spec = spec_from_file_location(
        PACKAGE_NAME,
        PACKAGE_INIT,
        submodule_search_locations=[str(WORKSPACE)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load package alias for {PACKAGE_NAME}')
    module = module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = module
    spec.loader.exec_module(module)


_ensure_workspace_package_alias()



@pytest.fixture(autouse=True)
def _isolate_qwen_env(monkeypatch):
    for name in (
        'QWEN_API_BASE',
        'QWEN_API_KEY',
        'QWEN_MODEL',
        'QWEN_ANSWER_MODEL',
        'QWEN_INTENT_MODEL',
        'QWEN_ROUTER_MODEL',
    ):
        monkeypatch.delenv(name, raising=False)
