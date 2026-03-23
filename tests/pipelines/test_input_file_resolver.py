from importlib import import_module
from pathlib import Path


def _load_resolver_module():
    return import_module('cloud_delivery_ontology_palantir.pipelines.input_file_resolver')


def test_resolve_input_file_passthrough_for_markdown_without_conversion(tmp_path: Path, monkeypatch):
    resolver_module = _load_resolver_module()
    input_file = tmp_path / 'ontology.md'
    input_file.write_text('# ontology', encoding='utf-8')

    converter_calls: list[Path] = []

    def fake_convert_tql_file_to_markdown_file(path: Path) -> Path:
        converter_calls.append(Path(path))
        return input_file.with_suffix('.converted.md')

    monkeypatch.setattr(
        resolver_module,
        'convert_tql_file_to_markdown_file',
        fake_convert_tql_file_to_markdown_file,
        raising=False,
    )

    resolved = resolver_module.resolve_input_file(input_file)

    assert resolved == input_file
    assert converter_calls == []


def test_resolve_input_file_converts_tql_into_stem_converted_markdown_in_same_directory(tmp_path: Path, monkeypatch):
    resolver_module = _load_resolver_module()
    input_file = tmp_path / 'ontology_source.tql'
    input_file.write_text('SELECT * FROM ontology;', encoding='utf-8')

    converter_calls: list[Path] = []
    converted_text = '# converted from tql\n- node: PoD\n'

    def fake_convert_tql_file_to_markdown_file(path: Path) -> Path:
        converter_calls.append(Path(path))
        output_file = Path(path).with_suffix('.converted.md')
        output_file.write_text(converted_text, encoding='utf-8')
        return output_file

    monkeypatch.setattr(
        resolver_module,
        'convert_tql_file_to_markdown_file',
        fake_convert_tql_file_to_markdown_file,
        raising=False,
    )

    resolved = resolver_module.resolve_input_file(input_file)

    expected_output = input_file.with_suffix('.converted.md')
    assert converter_calls == [input_file]
    assert resolved == expected_output
    assert expected_output.exists()
    assert expected_output.read_text(encoding='utf-8') == converted_text
