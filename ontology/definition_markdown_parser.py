from __future__ import annotations

import re

from .definition_models import (
    DerivedMetricSpec,
    NamedValueSpec,
    ObjectTypeSpec,
    OntologyDefinitionSpec,
    PropertySpec,
    RelationSpec,
)


_H2_RE = re.compile(r'^##\s+(.+)$')
_H3_RE = re.compile(r'^###\s+(.+)$')
_OBJECT_HEADING_RE = re.compile(r'^###\s+`([^`]+)`\s*$')
_LIST_ITEM_RE = re.compile(r'^(?:[-*]|\d+\.)\s+(.*)$')
_NAMED_ITEM_RE = re.compile(r'^`([^`]+)`\s*[：:]\s*(.+)$')
_RELATION_ITEM_RE = re.compile(r'^`([^`\s]+)\s+([A-Z_]+)\s+([^`\s]+)`\s*[：:]\s*(.+)$')


class _ParseError(ValueError):
    pass



def parse_definition_markdown(text: str, source_file: str | None = None) -> OntologyDefinitionSpec:
    spec = OntologyDefinitionSpec(source_file=source_file)
    lines = text.splitlines()
    current_h2 = ''
    current_group = ''
    current_relation_group = ''
    current_object: ObjectTypeSpec | None = None
    current_submode: str | None = None
    in_optional_notes = False

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith('# '):
            spec.title = line[2:].strip()
            continue

        h2_match = _H2_RE.match(line)
        if h2_match:
            if current_object is not None and current_object.source_end_line is None:
                current_object.source_end_line = line_no - 1
                current_object = None
            current_h2 = h2_match.group(1).strip()
            if current_h2.startswith('4.') and current_h2 not in {'4. Object Types', '4.7 MVP 暂不强制的补充属性'}:
                current_group = current_h2
            current_submode = None
            in_optional_notes = False
            continue

        if current_h2 == '2. 当前建模边界':
            item = _extract_list_or_ordered_text(line)
            if item:
                spec.boundaries.append(item)
            continue

        if current_h2 == '3. 本体主线':
            if line == '---' or ('`' not in line and '->' not in line):
                continue
            cleaned = [part.strip().strip('`') for part in line.split('->') if part.strip() and part.strip() != '---']
            spec.mainline.extend(cleaned)
            continue

        if current_h2 == '4. Object Types' or (current_h2.startswith('4.') and current_h2 != '4.7 MVP 暂不强制的补充属性'):
            h3_match = _H3_RE.match(line)
            if h3_match:
                object_heading = _OBJECT_HEADING_RE.match(line)
                if object_heading:
                    if current_object is not None and current_object.source_end_line is None:
                        current_object.source_end_line = line_no - 1
                    current_object = ObjectTypeSpec(
                        name=object_heading.group(1),
                        group=current_group,
                        source_start_line=line_no,
                    )
                    spec.object_types.append(current_object)
                    current_submode = None
                    continue
                current_group = h3_match.group(1).strip()
                current_submode = None
                continue

            if current_object is None:
                continue

            if _has_label(line, '中文释义'):
                current_object.chinese_description = _strip_label(line)
                continue
            if _has_label(line, '语义定义'):
                current_object.semantic_definition = _strip_label(line)
                continue

            mode_label_map = {
                '关键属性': 'key_properties',
                '状态建议': 'status_values',
                '规则约束': 'rules',
                '建议的违规类型': 'suggested_violation_types',
                '说明': 'notes',
                '命名建议': 'notes',
                '补充说明': 'notes',
            }
            matched_mode = next((label for label in mode_label_map if _is_block_label(line, label)), None)
            if matched_mode is not None:
                current_submode = mode_label_map[matched_mode]
                continue

            item_match = _LIST_ITEM_RE.match(line)
            if item_match and current_submode is not None:
                item = item_match.group(1).strip()
                if current_submode == 'key_properties':
                    name, description = _parse_named_item(item, line_no)
                    current_object.key_properties.append(PropertySpec(name=name, description=description, line_no=line_no))
                elif current_submode == 'status_values':
                    name, description = _parse_named_item(item, line_no)
                    current_object.status_values.append(NamedValueSpec(name=name, description=description, line_no=line_no))
                elif current_submode == 'suggested_violation_types':
                    name, description = _parse_named_item(item, line_no)
                    current_object.suggested_violation_types.append(NamedValueSpec(name=name, description=description, line_no=line_no))
                elif current_submode == 'rules':
                    current_object.rules.append(item)
                elif current_submode == 'notes':
                    current_object.notes.append(item)
                continue

        if current_h2 == '4.7 MVP 暂不强制的补充属性':
            if _is_block_label(line, '补充说明'):
                in_optional_notes = True
                continue
            item_match = _LIST_ITEM_RE.match(line)
            if item_match:
                item = item_match.group(1).strip()
                if in_optional_notes:
                    spec.optional_property_notes.append(item)
                else:
                    name, description = _parse_named_item(item, line_no)
                    spec.optional_properties.append(PropertySpec(name=name, description=description, line_no=line_no))
            continue

        if current_h2 == '5. Link Types':
            h3_match = _H3_RE.match(line)
            if h3_match:
                current_relation_group = h3_match.group(1).strip()
                continue
            item_match = _LIST_ITEM_RE.match(line)
            if item_match:
                source_type, relation, target_type, description = _parse_relation_item(item_match.group(1).strip(), line_no)
                spec.relations.append(
                    RelationSpec(
                        source_type=source_type,
                        relation=relation,
                        target_type=target_type,
                        description=description,
                        group=current_relation_group,
                        line_no=line_no,
                    )
                )
            continue

        if current_h2 == '6. 关键派生指标':
            item_match = _LIST_ITEM_RE.match(line)
            if item_match:
                name, description = _parse_named_item(item_match.group(1).strip(), line_no)
                spec.derived_metrics.append(DerivedMetricSpec(name=name, description=description, line_no=line_no))
            continue

    if current_object is not None and current_object.source_end_line is None:
        current_object.source_end_line = len(lines)

    _validate_spec(spec)
    return spec



def _validate_spec(spec: OntologyDefinitionSpec) -> None:
    if not spec.object_types:
        _fail(1, 'Object Types section did not define any object types')
    if not spec.relations:
        _fail(1, 'Link Types section did not define any relations')

    object_names: set[str] = set()
    for obj in spec.object_types:
        if obj.name in object_names:
            _fail(obj.source_start_line or 1, f'duplicate object type: {obj.name}')
        object_names.add(obj.name)
        seen_properties: set[str] = set()
        for prop in obj.key_properties:
            if prop.name in seen_properties:
                _fail(prop.line_no, f'duplicate property {prop.name!r} in object type {obj.name}')
            seen_properties.add(prop.name)

    seen_relations: set[tuple[str, str, str]] = set()
    for rel in spec.relations:
        if rel.source_type not in object_names:
            _fail(rel.line_no, f'relation source type {rel.source_type!r} is not defined in Object Types')
        if rel.target_type not in object_names:
            _fail(rel.line_no, f'relation target type {rel.target_type!r} is not defined in Object Types')
        key = (rel.source_type, rel.relation, rel.target_type)
        if key in seen_relations:
            _fail(rel.line_no, f'duplicate relation triple: {rel.source_type} {rel.relation} {rel.target_type}')
        seen_relations.add(key)



def _extract_list_or_ordered_text(line: str) -> str:
    match = _LIST_ITEM_RE.match(line)
    return match.group(1).strip() if match else ''



def _has_label(line: str, label: str) -> bool:
    return line.startswith(f'{label}：') or line.startswith(f'{label}:')



def _is_block_label(line: str, label: str) -> bool:
    return line == f'{label}：' or line == f'{label}:' or _has_label(line, label)



def _strip_label(line: str) -> str:
    if '：' in line:
        return line.split('：', 1)[1].strip()
    return line.split(':', 1)[1].strip()



def _parse_named_item(text: str, line_no: int) -> tuple[str, str]:
    match = _NAMED_ITEM_RE.match(text)
    if not match:
        _fail(line_no, f'expected backticked named item, got: {text}')
    return match.group(1), match.group(2).strip()



def _parse_relation_item(text: str, line_no: int) -> tuple[str, str, str, str]:
    match = _RELATION_ITEM_RE.match(text)
    if not match:
        _fail(line_no, f'malformed relation entry, expected `Source RELATION Target`: {text}')
    return match.group(1), match.group(2), match.group(3), match.group(4).strip()



def _fail(line_no: int, message: str) -> None:
    raise _ParseError(f'Line {line_no}: {message}')
