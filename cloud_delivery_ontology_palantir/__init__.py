from __future__ import annotations

from pathlib import Path

__all__ = ['__version__', 'build_ontology_from_markdown']
__version__ = '0.2.0'

_workspace_root = Path(__file__).resolve().parent.parent
__path__ = [str(_workspace_root)]


def build_ontology_from_markdown(*args, **kwargs):
    from .pipelines.build_ontology_pipeline import build_ontology_from_markdown as _impl
    return _impl(*args, **kwargs)
