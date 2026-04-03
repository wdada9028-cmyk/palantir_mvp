from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TypeDBConfig:
    address: str
    database: str
    username: str = ''
    password: str = ''


@dataclass(frozen=True, slots=True)
class _TraversalShape:
    source_var: str
    target_var: str
    relation: str


@dataclass(frozen=True, slots=True)
class _QueryShape:
    projection_vars: list[str]
    traversals: list[_TraversalShape]


class TypeDBConfigError(RuntimeError):
    pass


class TypeDBConnectionError(RuntimeError):
    pass


class TypeDBQueryError(RuntimeError):
    pass


_GET_LINE_RE = re.compile(r'^get\s+(.+);$', re.IGNORECASE)
_RELATION_LINE_RE = re.compile(r'^\((\$[A-Za-z0-9_]+),\s*(\$[A-Za-z0-9_]+)\)\s+isa\s+([a-z0-9\-]+);$', re.IGNORECASE)


def load_typedb_config() -> TypeDBConfig | None:
    address = os.getenv('TYPEDB_ADDRESS', '').strip()
    database = os.getenv('TYPEDB_DATABASE', '').strip()
    username = os.getenv('TYPEDB_USERNAME', '').strip()
    password = os.getenv('TYPEDB_PASSWORD', '').strip()

    if not address and not database and not username and not password:
        return None

    missing_required = [
        name
        for name, value in (
            ('TYPEDB_ADDRESS', address),
            ('TYPEDB_DATABASE', database),
        )
        if not value
    ]
    if missing_required:
        raise TypeDBConfigError(f'Missing required TypeDB environment variables: {", ".join(missing_required)}')

    missing_optional_pair = [
        name
        for name, value in (
            ('TYPEDB_USERNAME', username),
            ('TYPEDB_PASSWORD', password),
        )
        if not value
    ]
    if (username or password) and missing_optional_pair:
        raise TypeDBConfigError(f'Missing required TypeDB environment variables: {", ".join(missing_optional_pair)}')

    return TypeDBConfig(address=address, database=database, username=username, password=password)


class TypeDBClient:
    """Read-only TypeDB client for the instance QA pipeline."""

    def __init__(self, config: TypeDBConfig):
        self._config = config
        self._driver = None

    @property
    def config(self) -> TypeDBConfig:
        return self._config

    def connect(self) -> None:
        try:
            from typedb.driver import TypeDB
        except Exception as exc:  # pragma: no cover - import failures are environmental
            raise TypeDBConnectionError(f'Unable to import typedb-driver: {exc}') from exc

        try:
            self._driver = TypeDB.core_driver(self._config.address)
        except Exception as exc:  # pragma: no cover - integration path
            raise TypeDBConnectionError(f'Failed to connect TypeDB driver: {exc}') from exc

    def close(self) -> None:
        driver = self._driver
        self._driver = None
        if driver is None:
            return
        try:
            driver.close()
        except Exception:
            return

    def execute_readonly(self, query: str) -> list[dict[str, object]]:
        if self._driver is None:
            raise TypeDBConnectionError('TypeDB driver is not connected.')
        if not query.strip():
            raise TypeDBQueryError('TypeQL query must not be empty.')

        try:
            from typedb.driver import SessionType, TransactionType
        except Exception as exc:  # pragma: no cover - import failures are environmental
            raise TypeDBConnectionError(f'Unable to import typedb-driver session types: {exc}') from exc

        try:
            with self._driver.session(self._config.database, SessionType.DATA) as session:
                with session.transaction(TransactionType.READ) as tx:
                    results = list(tx.query.get(query))
                    return _map_query_results(query, results, tx)
        except TypeDBConnectionError:
            raise
        except Exception as exc:
            raise TypeDBQueryError(f'Failed to execute TypeQL query: {exc}') from exc


def _map_query_results(query: str, results: list[Any], tx: Any) -> list[dict[str, object]]:
    shape = _parse_query_shape(query)
    rows: list[dict[str, object]] = []

    if not shape.traversals:
        for result in results:
            root = _concept_from_result(result, 'root')
            row = _thing_row(root, tx)
            if row is not None:
                rows.append(row)
        return rows

    for result in results:
        for traversal in shape.traversals:
            source = _concept_from_result(result, traversal.source_var)
            target = _concept_from_result(result, traversal.target_var)
            source_row = _thing_row(source, tx)
            target_row = _thing_row(target, tx)
            if source_row is None or target_row is None:
                continue

            non_root_var = traversal.target_var if traversal.source_var == 'root' else traversal.source_var
            neighbor_row = dict(target_row if non_root_var == traversal.target_var else source_row)
            neighbor_row.update(
                {
                    '_source_entity': source_row.get('_entity', ''),
                    '_source_id': _best_identifier(source_row),
                    '_relation': _normalize_relation_label(traversal.relation),
                    '_target_entity': target_row.get('_entity', ''),
                    '_target_id': _best_identifier(target_row),
                }
            )
            rows.append(neighbor_row)
    return rows


def _parse_query_shape(query: str) -> _QueryShape:
    projection_vars: list[str] = []
    traversals: list[_TraversalShape] = []

    for raw_line in query.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        get_match = _GET_LINE_RE.match(line)
        if get_match:
            projection_vars = [item.strip().lstrip('$') for item in get_match.group(1).split(',') if item.strip()]
            continue
        relation_match = _RELATION_LINE_RE.match(line)
        if relation_match:
            source_var, target_var, relation = relation_match.groups()
            traversals.append(
                _TraversalShape(
                    source_var=source_var.lstrip('$'),
                    target_var=target_var.lstrip('$'),
                    relation=relation,
                )
            )

    return _QueryShape(projection_vars=projection_vars, traversals=traversals)


def _concept_from_result(result: Any, variable: str) -> Any | None:
    getter = getattr(result, 'get', None)
    if getter is None:
        return None
    return getter(variable)


def _thing_row(thing: Any, tx: Any) -> dict[str, object] | None:
    if thing is None:
        return None
    if not getattr(thing, 'is_entity', lambda: False)():
        return None

    entity = thing.as_entity()
    row: dict[str, object] = {
        '_entity': _normalize_entity_label(_label_name(entity.get_type())),
        '_iid': _safe_call(entity, 'get_iid') or '',
    }

    for attribute in _safe_iter(entity, 'get_has', tx):
        label = _snake_case(_label_name(attribute.get_type()))
        if not label:
            continue
        row[label] = _attribute_value(attribute)

    return row


def _attribute_value(attribute: Any) -> object:
    value = _safe_call(attribute, 'get_value')
    if hasattr(value, 'isoformat'):
        try:
            return value.isoformat()
        except Exception:
            return value
    return value


def _safe_iter(obj: Any, method_name: str, *args: Any) -> list[Any]:
    method = getattr(obj, method_name, None)
    if method is None:
        return []
    try:
        values = method(*args)
    except TypeError:
        values = method()
    return list(values or [])


def _safe_call(obj: Any, method_name: str) -> Any:
    method = getattr(obj, method_name, None)
    if method is None:
        return None
    try:
        return method()
    except Exception:
        return None


def _label_name(obj: Any) -> str:
    if obj is None:
        return ''
    label = getattr(obj, 'get_label', None)
    if callable(label):
        obj = label()
    name = getattr(obj, 'name', None)
    if name is not None:
        return str(name)
    scoped_name = getattr(obj, 'scoped_name', None)
    if callable(scoped_name):
        try:
            return str(scoped_name())
        except Exception:
            return ''
    return str(obj)


def _snake_case(value: str) -> str:
    text = str(value or '').strip().replace('-', '_')
    text = re.sub(r'([a-z0-9])([A-Z])', r'_', text)
    return text.lower()


_ENTITY_TOKEN_OVERRIDES = {'pod': 'PoD', 'sla': 'SLA'}


def _normalize_entity_label(value: str) -> str:
    parts = [part for part in _snake_case(value).split('_') if part]
    return ''.join(_ENTITY_TOKEN_OVERRIDES.get(part, part.capitalize()) for part in parts)


def _normalize_relation_label(value: str) -> str:
    return _snake_case(value).upper()


_IDENTIFIER_CANDIDATES = (
    'id',
    'project_id',
    'building_id',
    'floor_id',
    'room_id',
    'position_id',
    'pod_id',
    'pod_code',
    'shipment_id',
    'arrival_event_id',
    'arrival_plan_id',
    'template_id',
    'dependency_template_id',
    'sla_id',
    'activity_id',
    'crew_id',
    'assignment_id',
    'placement_plan_id',
    'violation_id',
    'recommendation_id',
    'milestone_id',
)


def _best_identifier(row: dict[str, object]) -> str:
    for key in _IDENTIFIER_CANDIDATES:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    iid = row.get('_iid')
    return str(iid).strip() if iid is not None else ''
