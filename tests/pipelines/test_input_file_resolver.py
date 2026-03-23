from importlib import import_module
from pathlib import Path


def _load_resolver_module():
    return import_module('cloud_delivery_ontology_palantir.pipelines.input_file_resolver')


def test_resolve_input_file_passthrough_for_markdown_without_conversion(tmp_path: Path, monkeypatch):
    resolver_module = _load_resolver_module()
    input_file = tmp_path / 'ontology.md'
    input_file.write_text('# ontology', encoding='utf-8')

    converter_calls: list[Path] = []

    def fake_convert_tql_to_markdown(path: Path) -> Path:
        converter_calls.append(Path(path))
        return tmp_path / 'should-not-be-used.converted.md'

    monkeypatch.setattr(resolver_module, 'convert_tql_to_markdown', fake_convert_tql_to_markdown, raising=False)

    resolved = resolver_module.resolve_input_file(input_file)

    assert resolved == input_file
    assert converter_calls == []


def test_resolve_input_file_converts_tql_to_converted_markdown(tmp_path: Path, monkeypatch):
    resolver_module = _load_resolver_module()
    input_file = tmp_path / 'ontology.tql'
    input_file.write_text('SELECT * FROM ontology;', encoding='utf-8')
    converted_file = tmp_path / 'ontology.converted.md'

    converter_calls: list[Path] = []

    def fake_convert_tql_to_markdown(path: Path) -> Path:
        converter_calls.append(Path(path))
        return converted_file

    monkeypatch.setattr(resolver_module, 'convert_tql_to_markdown', fake_convert_tql_to_markdown, raising=False)

    resolved = resolver_module.resolve_input_file(input_file)

    assert converter_calls == [input_file]
    assert resolved == converted_file
