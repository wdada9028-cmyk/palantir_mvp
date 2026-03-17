"""Markdown ontology definition graph package."""

__all__ = ["__version__", "build_ontology_from_markdown"]

__version__ = "0.2.0"


def build_ontology_from_markdown(*args, **kwargs):
    from .pipelines.build_ontology_pipeline import build_ontology_from_markdown as _impl
    return _impl(*args, **kwargs)
