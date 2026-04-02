from __future__ import annotations

import re

from .fact_query_models import FactQueryDSL

_ALLOWED_FILTER_OPS = {'eq'}
_ALLOWED_AGGREGATES = {None, 'count'}


def build_typeql_query(query: FactQueryDSL) -> str:
    if query.aggregate not in _ALLOWED_AGGREGATES:
        raise ValueError(f'Unsupported aggregate for TypeQL builder: {query.aggregate}')

    for item in query.filters:
        if item.op not in _ALLOWED_FILTER_OPS:
            raise ValueError(f'Unsupported filter op for TypeQL builder: {item.op}')
        if item.entity != query.root.entity:
            raise ValueError('Non-root filters are not supported by the current TypeQL builder.')

    lines: list[str] = ['match']
    root_type = _type_label(query.root.entity)
    lines.append(f'$root isa {root_type};')

    identifier = query.root.identifier
    if identifier is not None:
        lines.append(f'$root has {_attr_label(identifier.attribute)} {_render_literal(identifier.value)};')

    for index, item in enumerate(query.traversals, start=1):
        relation_type = _type_label(item.relation)
        from_var = '$root' if index == 1 and item.from_entity == query.root.entity else f'$from{index}'
        to_var = f'$n{index}'
        if item.direction == 'out':
            lines.append(f'({from_var}, {to_var}) isa {relation_type};')
        else:
            lines.append(f'({to_var}, {from_var}) isa {relation_type};')
        lines.append(f'{to_var} isa {_type_label(item.to_entity)};')

    for item in query.filters:
        lines.append(f'$root has {_attr_label(item.attribute)} {_render_literal(item.value)};')

    projection_vars = ['$root', *[f'$n{index}' for index, _ in enumerate(query.traversals, start=1)]]
    if query.aggregate == 'count':
        lines.append('count;')
    else:
        lines.append('get ' + ', '.join(projection_vars) + ';')
        lines.append(f'limit {int(query.limit)};')

    return '\n'.join(lines)


def _type_label(value: str) -> str:
    value = value.replace('_', '-')
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', value)
    value = value.lower()
    value = value.replace('po-d', 'pod')
    return value


def _attr_label(value: str) -> str:
    return value.strip().replace('_', '-').lower()


def _render_literal(value: object) -> str:
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    escaped = text.replace('"', '\\"')
    return f'"{escaped}"'
