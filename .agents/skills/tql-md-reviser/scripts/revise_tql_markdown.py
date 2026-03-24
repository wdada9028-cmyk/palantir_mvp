from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown
from cloud_delivery_ontology_palantir.ontology.definition_models import ObjectTypeSpec, OntologyDefinitionSpec, PropertySpec, RelationSpec
from cloud_delivery_ontology_palantir.pipelines.tql_schema_extractor import extract_tql_schema
from cloud_delivery_ontology_palantir.pipelines.tql_schema_renderer import render_tql_schema_as_definition_markdown

DESC_LABEL = '\u4e2d\u6587\u91ca\u4e49'
SEMANTIC_LABEL = '\u8bed\u4e49\u5b9a\u4e49'
KEY_PROPERTIES_LABEL = '\u5173\u952e\u5c5e\u6027'
STATUS_LABEL = '\u72b6\u6001\u5efa\u8bae'
RULES_LABEL = '\u89c4\u5219\u7ea6\u675f'
VIOLATIONS_LABEL = '\u5efa\u8bae\u7684\u8fdd\u89c4\u7c7b\u578b'
NOTES_LABEL = '\u8bf4\u660e'
NAMING_LABEL = '\u547d\u540d\u5efa\u8bae'
EXTRA_NOTES_LABEL = '\u8865\u5145\u8bf4\u660e'
BOUNDARIES_HEADING = '## \u5f53\u524d\u5efa\u6a21\u8fb9\u754c'
MAINLINE_HEADING = '## \u672c\u4f53\u4e3b\u7ebf'
OPTIONAL_HEADING = '## 4.7 MVP \u6682\u4e0d\u5f3a\u5236\u7684\u8865\u5145\u5c5e\u6027'
DERIVED_HEADING = '## 6. \u5173\u952e\u6d3e\u751f\u6307\u6807'
ALLOWED_LABELS = [
    DESC_LABEL,
    SEMANTIC_LABEL,
    KEY_PROPERTIES_LABEL,
    STATUS_LABEL,
    RULES_LABEL,
    VIOLATIONS_LABEL,
    NOTES_LABEL,
    NAMING_LABEL,
    EXTRA_NOTES_LABEL,
]
NOTE_LABELS = [NOTES_LABEL, NAMING_LABEL, EXTRA_NOTES_LABEL]
_PARSE_ERROR_RE = re.compile(r'Line\s+(\d+)\s*:\s*(.+)')
_LIST_ITEM_RE = re.compile(r'^(?:[-*]|\d+\.)\s+(.*)$')
_BACKTICKED_NAMED_RE = re.compile(r'^`([^`]+)`\s*[:\uFF1A]\s*(.+)$')
_OBJECT_HEADING_RE = re.compile(r'^###\s+`([^`]+)`\s*$')
_RELATION_ITEM_RE = re.compile(r'^[-*]\s+`([^`\s]+)\s+([A-Z_]+)\s+([^`\s]+)`')


def compute_structure_anchors(markdown_text: str) -> dict[str, Any]:
    return _scan_structure_anchors(markdown_text)


def extract_parse_error(exc: Exception) -> dict[str, Any]:
    raw = str(exc)
    match = _PARSE_ERROR_RE.search(raw)
    if match:
        return {
            'line_no': int(match.group(1)),
            'message': match.group(2).strip(),
            'exception_type': type(exc).__name__,
            'raw': raw,
        }
    return {
        'line_no': None,
        'message': raw,
        'exception_type': type(exc).__name__,
        'raw': raw,
    }


def revise_markdown_from_tql(
    *,
    tql_file: str | Path,
    markdown_file: str | Path,
    revised_file: str | Path | None = None,
    report_file: str | Path | None = None,
    max_retries: int = 2,
) -> dict[str, Any]:
    tql_path = Path(tql_file)
    markdown_path = Path(markdown_file)
    revised_path = Path(revised_file) if revised_file is not None else markdown_path.with_name(f'{markdown_path.stem}.revised.md')
    report_path = Path(report_file) if report_file is not None else markdown_path.with_name(f'{markdown_path.stem}.revision-report.md')

    current_text = markdown_path.read_text(encoding='utf-8')
    current_spec = parse_definition_markdown(current_text, source_file=str(markdown_path))
    current_anchors = compute_structure_anchors(current_text)
    note_sections = _extract_object_note_sections(current_text)

    generated_markdown = render_tql_schema_as_definition_markdown(
        extract_tql_schema(tql_path.read_text(encoding='utf-8'), source_file=str(tql_path))
    )
    generated_spec = parse_definition_markdown(generated_markdown, source_file=str(tql_path))

    merged_spec, changes = _merge_specs(current_spec, generated_spec)
    final_text = render_definition_markdown(merged_spec, note_sections=note_sections)

    attempts: list[dict[str, Any]] = []
    parser_details: dict[str, Any] | None = None
    status = 'failed'

    for attempt_index in range(max_retries + 1):
        try:
            parse_definition_markdown(final_text, source_file=str(revised_path))
            _validate_structure(current_anchors, compute_structure_anchors(final_text))
            revised_path.write_text(final_text, encoding='utf-8')
            attempts.append({'attempt': attempt_index + 1, 'status': 'success'})
            parser_details = None
            status = 'success'
            break
        except Exception as exc:  # noqa: BLE001
            parser_details = extract_parse_error(exc)
            attempts.append({'attempt': attempt_index + 1, 'status': 'failed', 'error': parser_details})
            if attempt_index >= max_retries:
                break
            repaired = _apply_minimal_repair(final_text, parser_details)
            if repaired == final_text:
                break
            final_text = repaired

    report_text = _build_revision_report(
        tql_path=tql_path,
        markdown_path=markdown_path,
        revised_path=revised_path,
        status=status,
        changes=changes,
        attempts=attempts,
        parser_details=parser_details,
    )
    report_path.write_text(report_text, encoding='utf-8')

    result: dict[str, Any] = {
        'status': status,
        'tql_file': str(tql_path),
        'markdown_file': str(markdown_path),
        'revised_file': str(revised_path),
        'report_file': str(report_path),
        'changes': changes,
        'attempts': attempts,
    }
    if parser_details is not None:
        result['parser_error'] = parser_details
    return result


def render_definition_markdown(
    spec: OntologyDefinitionSpec,
    *,
    note_sections: dict[str, dict[str, list[str]]] | None = None,
) -> str:
    lines: list[str] = []
    if spec.title:
        lines.append(f'# {spec.title}')
        lines.append('')

    if spec.boundaries:
        lines.append(BOUNDARIES_HEADING)
        lines.extend(f'{idx}. {item}' for idx, item in enumerate(spec.boundaries, start=1))
        lines.append('')

    if spec.mainline:
        lines.append(MAINLINE_HEADING)
        lines.append(' -> '.join(f'`{item}`' for item in spec.mainline))
        lines.append('')

    lines.append('## 4. Object Types')
    for group_name, objects in _group_objects(spec.object_types):
        lines.append(f'## {group_name}')
        lines.append('')
        for obj in objects:
            lines.append(f'### `{obj.name}`')
            if obj.chinese_description:
                lines.append(f'{DESC_LABEL}: {obj.chinese_description}')
            if obj.semantic_definition:
                lines.append(f'{SEMANTIC_LABEL}: {obj.semantic_definition}')

            lines.append(f'{KEY_PROPERTIES_LABEL}:')
            for prop in obj.key_properties:
                lines.append(f'- `{prop.name}`: {prop.description}')

            if obj.status_values:
                lines.append(f'{STATUS_LABEL}:')
                for item in obj.status_values:
                    lines.append(f'- `{item.name}`: {item.description}')

            if obj.rules:
                lines.append(f'{RULES_LABEL}:')
                for item in obj.rules:
                    lines.append(f'- {item}')

            if obj.suggested_violation_types:
                lines.append(f'{VIOLATIONS_LABEL}:')
                for item in obj.suggested_violation_types:
                    lines.append(f'- `{item.name}`: {item.description}')

            labels = note_sections.get(obj.name, {}) if note_sections else {}
            if labels:
                for label in NOTE_LABELS:
                    items = labels.get(label, [])
                    if not items:
                        continue
                    lines.append(f'{label}:')
                    for item in items:
                        lines.append(f'- {item}')
            elif obj.notes:
                lines.append(f'{NOTES_LABEL}:')
                for item in obj.notes:
                    lines.append(f'- {item}')

            lines.append('')

    if spec.optional_properties or spec.optional_property_notes:
        lines.append(OPTIONAL_HEADING)
        for prop in spec.optional_properties:
            lines.append(f'- `{prop.name}`: {prop.description}')
        if spec.optional_property_notes:
            lines.append(f'{EXTRA_NOTES_LABEL}:')
            for item in spec.optional_property_notes:
                lines.append(f'- {item}')
        lines.append('')

    lines.append('## 5. Link Types')
    for group_name, relations in _group_relations(spec.relations):
        lines.append(f'### {group_name}')
        for rel in relations:
            lines.append(f'- `{rel.source_type} {rel.relation} {rel.target_type}`: {rel.description}')
        lines.append('')

    if spec.derived_metrics:
        lines.append(DERIVED_HEADING)
        for metric in spec.derived_metrics:
            lines.append(f'- `{metric.name}`: {metric.description}')
        lines.append('')

    return '\n'.join(lines).rstrip() + '\n'


def _merge_specs(current: OntologyDefinitionSpec, generated: OntologyDefinitionSpec) -> tuple[OntologyDefinitionSpec, dict[str, Any]]:
    generated_objects = {obj.name: obj for obj in generated.object_types}

    merged_objects: list[ObjectTypeSpec] = []
    revised_objects: list[str] = []
    added_objects: list[str] = []
    added_properties: dict[str, list[str]] = {}

    seen: set[str] = set()
    for obj in current.object_types:
        seen.add(obj.name)
        gen = generated_objects.get(obj.name)
        if gen is None:
            merged_objects.append(replace(obj))
            continue
        merged, added = _merge_object(obj, gen)
        merged_objects.append(merged)
        if added:
            added_properties[obj.name] = added
            revised_objects.append(obj.name)
        if obj.chinese_description != merged.chinese_description or obj.semantic_definition != merged.semantic_definition:
            revised_objects.append(obj.name)

    for obj in generated.object_types:
        if obj.name in seen:
            continue
        merged_objects.append(replace(obj))
        added_objects.append(obj.name)
        if obj.key_properties:
            added_properties[obj.name] = [prop.name for prop in obj.key_properties]

    current_relations = {(r.source_type, r.relation, r.target_type): r for r in current.relations}
    merged_relations: list[RelationSpec] = [replace(r) for r in current.relations]
    added_relations: list[str] = []
    existing_keys = set(current_relations)

    for rel in generated.relations:
        key = (rel.source_type, rel.relation, rel.target_type)
        inverse = (rel.target_type, rel.relation, rel.source_type)
        if key in existing_keys or inverse in existing_keys:
            continue
        merged_relations.append(replace(rel))
        existing_keys.add(key)
        added_relations.append(f'{rel.source_type} {rel.relation} {rel.target_type}')

    merged = OntologyDefinitionSpec(
        title=current.title or generated.title,
        source_file=current.source_file,
        boundaries=list(current.boundaries),
        mainline=list(current.mainline),
        object_types=merged_objects,
        relations=merged_relations,
        derived_metrics=list(current.derived_metrics),
        optional_properties=list(current.optional_properties),
        optional_property_notes=list(current.optional_property_notes),
    )
    return merged, {
        'added_objects': added_objects,
        'revised_objects': sorted(set(revised_objects)),
        'added_properties': added_properties,
        'added_relations': added_relations,
    }


def _merge_object(current: ObjectTypeSpec, generated: ObjectTypeSpec) -> tuple[ObjectTypeSpec, list[str]]:
    merged_props: list[PropertySpec] = [replace(prop) for prop in current.key_properties]
    existing_names = {prop.name for prop in current.key_properties}
    added: list[str] = []

    for prop in generated.key_properties:
        if prop.name in existing_names:
            continue
        merged_props.append(replace(prop))
        added.append(prop.name)

    merged = ObjectTypeSpec(
        name=current.name,
        group=current.group or generated.group,
        chinese_description=current.chinese_description or generated.chinese_description,
        semantic_definition=current.semantic_definition or generated.semantic_definition,
        key_properties=merged_props,
        status_values=list(current.status_values or generated.status_values),
        rules=list(current.rules or generated.rules),
        notes=list(current.notes or generated.notes),
        suggested_violation_types=list(current.suggested_violation_types or generated.suggested_violation_types),
        source_start_line=current.source_start_line,
        source_end_line=current.source_end_line,
    )
    return merged, added


def _scan_structure_anchors(markdown_text: str) -> dict[str, Any]:
    groups: list[str] = []
    objects: dict[str, dict[str, Any]] = {}
    relations: dict[str, dict[str, str]] = {}

    current_section = ''
    current_group = ''
    current_object: str | None = None
    in_key_props = False

    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith('## '):
            heading = line[3:].strip()
            if heading in {'4. Object Types', '5. Link Types'}:
                current_section = heading
                current_object = None
                in_key_props = False
                continue
            if current_section == '4. Object Types' and heading.startswith('4.'):
                current_group = heading
                if current_group not in groups:
                    groups.append(current_group)
                current_object = None
                in_key_props = False
                continue
            current_section = heading
            current_object = None
            in_key_props = False
            continue

        object_match = _OBJECT_HEADING_RE.match(line)
        if current_section == '4. Object Types' and object_match:
            current_object = object_match.group(1)
            objects[current_object] = {'group': current_group, 'key_properties': []}
            in_key_props = False
            continue

        if current_object is not None and _is_label_line(line, KEY_PROPERTIES_LABEL):
            in_key_props = True
            continue

        if current_object is not None and any(_is_label_line(line, label) for label in ALLOWED_LABELS if label != KEY_PROPERTIES_LABEL):
            in_key_props = False
            continue

        if current_object is not None and in_key_props:
            item_match = _LIST_ITEM_RE.match(line)
            if item_match:
                prop_match = _BACKTICKED_NAMED_RE.match(item_match.group(1).strip())
                if prop_match:
                    objects[current_object]['key_properties'].append(prop_match.group(1))
            continue

        relation_match = _RELATION_ITEM_RE.match(line)
        if relation_match:
            key = f'{relation_match.group(1)}|{relation_match.group(2)}|{relation_match.group(3)}'
            relations[key] = {'key': key}

    return {'group_order': groups, 'objects': objects, 'relations': relations}


def _extract_object_note_sections(markdown_text: str) -> dict[str, dict[str, list[str]]]:
    sections: dict[str, dict[str, list[str]]] = {}
    current_section = ''
    current_object: str | None = None
    current_note_label: str | None = None

    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith('## '):
            heading = line[3:].strip()
            if heading == '4. Object Types':
                current_section = '4. Object Types'
                current_object = None
                current_note_label = None
                continue
            if current_section == '4. Object Types' and heading.startswith('4.'):
                current_object = None
                current_note_label = None
                continue
            current_section = heading
            current_object = None
            current_note_label = None
            continue

        object_match = _OBJECT_HEADING_RE.match(line)
        if current_section == '4. Object Types' and object_match:
            current_object = object_match.group(1)
            sections.setdefault(current_object, {label: [] for label in NOTE_LABELS})
            current_note_label = None
            continue

        if current_object is None:
            continue

        note_label = next((label for label in NOTE_LABELS if _is_label_line(line, label)), None)
        if note_label is not None:
            current_note_label = note_label
            continue

        if current_note_label is None:
            continue

        item_match = _LIST_ITEM_RE.match(line)
        if item_match:
            sections[current_object][current_note_label].append(item_match.group(1).strip())
            continue

        current_note_label = None

    return sections


def _validate_structure(original: dict[str, Any], revised: dict[str, Any]) -> None:
    if not _is_subsequence(original['group_order'], revised['group_order']):
        raise ValueError('Line 1: structure anchor mismatch for object group order')

    for name, info in original['objects'].items():
        revised_info = revised['objects'].get(name)
        if revised_info is None:
            raise ValueError(f'Line 1: structure anchor missing object {name}')
        if info['group'] != revised_info['group']:
            raise ValueError(f'Line 1: structure anchor moved object {name}')
        if not set(info['key_properties']).issubset(set(revised_info['key_properties'])):
            raise ValueError(f'Line 1: structure anchor dropped key properties for {name}')

    for relation_key in original['relations']:
        if relation_key not in revised['relations']:
            raise ValueError(f'Line 1: structure anchor missing relation {relation_key}')


def _apply_minimal_repair(markdown_text: str, error: dict[str, Any]) -> str:
    exception_type = str(error.get('exception_type') or '')
    message = str(error.get('message') or '').lower()
    if exception_type not in {'_ParseError', 'ValueError'}:
        return markdown_text
    if 'structure anchor' in message:
        return markdown_text

    line_no = error.get('line_no')
    if not isinstance(line_no, int) or line_no <= 0:
        return markdown_text

    lines = markdown_text.splitlines()
    if line_no > len(lines):
        return markdown_text

    target_line = lines[line_no - 1]
    stripped = target_line.strip()

    for label in ALLOWED_LABELS:
        if stripped.startswith(label) and not _is_label_line(stripped, label):
            lines[line_no - 1] = target_line + ':'
            return '\n'.join(lines) + '\n'

    if stripped.startswith('- `') and ':' not in stripped and '?' not in stripped:
        right_tick = target_line.find('`', target_line.find('`') + 1)
        if right_tick != -1:
            lines[line_no - 1] = target_line[: right_tick + 1] + ': ' + target_line[right_tick + 1 :].lstrip()
            return '\n'.join(lines) + '\n'

    return markdown_text


def _build_revision_report(
    *,
    tql_path: Path,
    markdown_path: Path,
    revised_path: Path,
    status: str,
    changes: dict[str, Any],
    attempts: list[dict[str, Any]],
    parser_details: dict[str, Any] | None,
) -> str:
    lines = [
        '# Revision Report',
        '',
        f'- status: {status}',
        f'- tql_file: {tql_path}',
        f'- markdown_file: {markdown_path}',
        f'- revised_file: {revised_path}',
        f'- retries: {max(0, len(attempts) - 1)}',
        '',
        '## Changes',
        f"- added_objects: {', '.join(changes['added_objects']) if changes['added_objects'] else 'None'}",
        f"- revised_objects: {', '.join(changes['revised_objects']) if changes['revised_objects'] else 'None'}",
        f"- added_relations: {', '.join(changes['added_relations']) if changes['added_relations'] else 'None'}",
        '- added_properties:',
    ]

    if changes['added_properties']:
        for object_name, prop_names in changes['added_properties'].items():
            lines.append(f"  - {object_name}: {', '.join(prop_names)}")
    else:
        lines.append('  - None')

    lines.extend(['', '## Validation Attempts'])
    for attempt in attempts:
        lines.append(f"- attempt {attempt['attempt']}: {attempt['status']}")
        if 'error' in attempt:
            error = attempt['error']
            lines.append(f"  - exception_type: {error['exception_type']}")
            lines.append(f"  - line_no: {error['line_no']}")
            lines.append(f"  - message: {error['message']}")

    if status != 'success' and parser_details is not None:
        lines.extend([
            '',
            '## Final Parser Error',
            f"- exception_type: {parser_details['exception_type']}",
            f"- line_no: {parser_details['line_no']}",
            f"- message: {parser_details['message']}",
        ])

    lines.append('')
    return '\n'.join(lines)


def _group_objects(objects: list[ObjectTypeSpec]) -> list[tuple[str, list[ObjectTypeSpec]]]:
    grouped: dict[str, list[ObjectTypeSpec]] = {}
    order: list[str] = []
    for obj in objects:
        group = obj.group or '4.9 Imported Objects'
        if group not in grouped:
            grouped[group] = []
            order.append(group)
        grouped[group].append(obj)
    return [(group, grouped[group]) for group in order]


def _group_relations(relations: list[RelationSpec]) -> list[tuple[str, list[RelationSpec]]]:
    grouped: dict[str, list[RelationSpec]] = {}
    order: list[str] = []
    for rel in relations:
        group = rel.group or '5.1 Imported Relations'
        if group not in grouped:
            grouped[group] = []
            order.append(group)
        grouped[group].append(rel)
    return [(group, grouped[group]) for group in order]


def _is_subsequence(original: list[str], revised: list[str]) -> bool:
    it = iter(revised)
    return all(any(item == candidate for candidate in it) for item in original)


def _is_label_line(line: str, label: str) -> bool:
    return line == f'{label}:' or line == f'{label}\uFF1A'


def _stable_hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Revise ontology markdown from TQL with parser-safe structure locking.')
    parser.add_argument('--tql', required=True, help='Path to source TQL file')
    parser.add_argument('--markdown', required=True, help='Path to current markdown file')
    parser.add_argument('--revised-output', default=None, help='Optional path for revised markdown output')
    parser.add_argument('--report-output', default=None, help='Optional path for revision report output')
    parser.add_argument('--max-retries', type=int, default=2, help='Maximum minimal repair retries')
    args = parser.parse_args(argv)

    result = revise_markdown_from_tql(
        tql_file=args.tql,
        markdown_file=args.markdown,
        revised_file=args.revised_output,
        report_file=args.report_output,
        max_retries=args.max_retries,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'success' else 1


if __name__ == '__main__':
    raise SystemExit(main())
