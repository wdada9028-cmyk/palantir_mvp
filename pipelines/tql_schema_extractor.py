from __future__ import annotations

import re
from pathlib import Path

from .tql_schema_models import TqlAttributeSpec, TqlEntityPlaySpec, TqlEntityTypeSpec, TqlRelationTypeSpec, TqlSchemaSpec

_ATTRIBUTE_RE = re.compile(r'^attribute\s+([a-z0-9-]+),\s*value\s+([a-z0-9-]+)$')
_RELATION_RE = re.compile(r'^relation\s+([a-z0-9-]+)$')
_ENTITY_RE = re.compile(r'^entity\s+([a-z0-9-]+)(?:\s+sub\s+([a-z0-9-]+))?(?:\s+@abstract)?$')
_OWNS_RE = re.compile(r'^owns\s+([a-z0-9-]+)(?:\s+@key)?$')
_RELATES_RE = re.compile(r'^relates\s+([a-z0-9-]+)$')
_PLAYS_RE = re.compile(r'^plays\s+([a-z0-9-]+):([a-z0-9-]+)$')
_DIRECTIVE_RE = re.compile(r'^#\s*([a-zA-Z-]+)\s*:\s*(.+?)\s*$')


def extract_tql_schema(text: str, *, source_file: str) -> TqlSchemaSpec:
    schema = TqlSchemaSpec(title=_extract_title(source_file))

    for statement, comments in _iter_statement_records(text):
        if statement == 'define':
            continue
        directives = _parse_directives(comments)
        if _parse_attribute(statement, schema, directives):
            continue
        if _parse_relation(statement, schema):
            continue
        if _parse_entity(statement, schema, directives):
            continue

    _apply_explicit_group_defaults(schema)
    return schema


def _extract_title(source_file: str) -> str:
    path = Path(source_file)
    stem = path.stem.strip()
    return stem or path.name or source_file


def _iter_statement_records(text: str) -> list[tuple[str, list[str]]]:
    records: list[tuple[str, list[str]]] = []
    current: list[str] = []
    comments: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if not current:
                comments = []
            continue
        if line.startswith('#'):
            if not current:
                comments.append(line)
            continue
        if line == 'define' and not current:
            records.append(('define', comments))
            comments = []
            continue
        current.append(line)
        if line.endswith(';'):
            records.append((' '.join(current)[:-1].strip(), comments))
            current = []
            comments = []
    if current:
        records.append((' '.join(current).strip(), comments))
    return records


def _parse_directives(comments: list[str]) -> dict[str, str]:
    directives: dict[str, str] = {}
    for comment in comments:
        match = _DIRECTIVE_RE.match(comment)
        if not match:
            continue
        key, value = match.groups()
        directives[key.strip().lower()] = value.strip()
    return directives


def _parse_attribute(statement: str, schema: TqlSchemaSpec, directives: dict[str, str]) -> bool:
    match = _ATTRIBUTE_RE.match(statement)
    if not match:
        return False
    name, value_type = match.groups()
    schema.attributes[name] = TqlAttributeSpec(name=name, value_type=value_type, zh_label=directives.get('zh'))
    return True


def _parse_relation(statement: str, schema: TqlSchemaSpec) -> bool:
    parts = [part.strip() for part in statement.split(',') if part.strip()]
    if not parts:
        return False
    head = _RELATION_RE.match(parts[0])
    if not head:
        return False
    relation_name = head.group(1)
    roles: list[str] = []
    for part in parts[1:]:
        role_match = _RELATES_RE.match(part)
        if role_match:
            roles.append(role_match.group(1))
    schema.relations[relation_name] = TqlRelationTypeSpec(name=relation_name, roles=roles)
    return True


def _parse_entity(statement: str, schema: TqlSchemaSpec, directives: dict[str, str]) -> bool:
    parts = [part.strip() for part in statement.split(',') if part.strip()]
    if not parts:
        return False
    head = _ENTITY_RE.match(parts[0])
    if not head:
        return False

    entity_name, parent = head.groups()
    entity = TqlEntityTypeSpec(
        name=entity_name,
        parent=parent,
        is_abstract='@abstract' in parts[0],
        group_label=directives.get('group'),
        zh_label=directives.get('zh'),
        semantic_definition=directives.get('semantic'),
    )

    for part in parts[1:]:
        owns_match = _OWNS_RE.match(part)
        if owns_match:
            entity.own_attributes.append(owns_match.group(1))
            continue
        plays_match = _PLAYS_RE.match(part)
        if plays_match:
            entity.plays.append(TqlEntityPlaySpec(relation_name=plays_match.group(1), role_name=plays_match.group(2)))

    schema.entities.append(entity)
    return True


def _apply_explicit_group_defaults(schema: TqlSchemaSpec) -> None:
    entity_by_name = {entity.name: entity for entity in schema.entities}
    for entity in schema.entities:
        if entity.group_label or not entity.parent:
            continue
        parent = entity_by_name.get(entity.parent)
        if parent is None or not parent.is_abstract:
            continue
        entity.group_label = parent.zh_label or _fallback_group_label(parent.name)


def _fallback_group_label(entity_name: str) -> str:
    return ' '.join(part.capitalize() for part in entity_name.split('-'))
