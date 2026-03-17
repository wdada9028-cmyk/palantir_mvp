__all__ = ['OntologyBuilder']


def __getattr__(name: str):
    if name == 'OntologyBuilder':
        from .builder import OntologyBuilder
        return OntologyBuilder
    raise AttributeError(name)
