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
    entity_by_var: dict[str, str]
    projection_vars: list[str]
    traversals: list[_TraversalShape]
    base_lines: list[str]
    limit_line: str | None
    aggregate: str | None


class TypeDBConfigError(RuntimeError):
    pass


class TypeDBConnectionError(RuntimeError):
    pass


class TypeDBQueryError(RuntimeError):
    pass


_GET_LINE_RE = re.compile(r'^get\s+(.+);$', re.IGNORECASE)
_LIMIT_LINE_RE = re.compile(r'^limit\s+\d+;$', re.IGNORECASE)
_ISA_LINE_RE = re.compile(r'^(\$[A-Za-z0-9_]+)\s+isa\s+([a-z0-9\-]+);$', re.IGNORECASE)
_RELATION_LINE_RE = re.compile(r'^\(\s*(?:[a-z0-9\-]+\s*:\s*)?(\$[A-Za-z0-9_]+),\s*(?:[a-z0-9\-]+\s*:\s*)?(\$[A-Za-z0-9_]+)\s*\)\s+isa\s+([a-z0-9\-]+);$', re.IGNORECASE)
_COUNT_LINE_RE = re.compile(r'^count;$', re.IGNORECASE)

_ENTITY_TOKEN_OVERRIDES = {'pod': 'PoD', 'sla': 'SLA'}
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


    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def connect(self) -> None:
        try:
            from typedb.driver import Credentials, DriverOptions, TypeDB
        except Exception as exc:  # pragma: no cover - import failures are environmental
            raise TypeDBConnectionError(f'Unable to import typedb-driver: {exc}') from exc

        try:
            credentials = Credentials(self._config.username, self._config.password)
            driver_options = DriverOptions(is_tls_enabled=False)
            self._driver = TypeDB.driver(self._config.address, credentials, driver_options)
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
            from typedb.driver import TransactionType
        except Exception as exc:  # pragma: no cover - import failures are environmental
            raise TypeDBConnectionError(f'Unable to import typedb-driver transaction types: {exc}') from exc

        shape = _parse_query_shape(query)
        if shape.aggregate == 'count':
            raise TypeDBQueryError('Count queries are not implemented for the current TypeDB 3.x client.')

        fetch_query = _build_fetch_query(shape)
        try:
            with self._driver.transaction(self._config.database, TransactionType.READ) as tx:
                answer = tx.query(fetch_query).resolve()
                if not answer.is_concept_documents():
                    raise TypeDBQueryError('Expected concept documents from fetch query.')
                return _map_concept_documents(shape, list(answer.as_concept_documents()))
        except TypeDBQueryError:
            raise
        except Exception as exc:
            raise TypeDBQueryError(f'Failed to execute TypeQL query: {exc}') from exc


def _parse_query_shape(query: str) -> _QueryShape:
    entity_by_var: dict[str, str] = {}
    projection_vars: list[str] = []
    traversals: list[_TraversalShape] = []
    base_lines: list[str] = []
    limit_line: str | None = None
    aggregate: str | None = None

    for raw_line in query.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        get_match = _GET_LINE_RE.match(line)
        if get_match:
            projection_vars = [item.strip().lstrip('$') for item in get_match.group(1).split(',') if item.strip()]
            continue
        if _COUNT_LINE_RE.match(line):
            aggregate = 'count'
            continue
        if _LIMIT_LINE_RE.match(line):
            limit_line = line
            continue

        isa_match = _ISA_LINE_RE.match(line)
        if isa_match:
            variable, entity = isa_match.groups()
            entity_by_var[variable.lstrip('$')] = _normalize_entity_label(entity)
            base_lines.append(line)
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
            base_lines.append(line)
            continue

        base_lines.append(line)

    return _QueryShape(
        entity_by_var=entity_by_var,
        projection_vars=projection_vars,
        traversals=traversals,
        base_lines=base_lines,
        limit_line=limit_line,
        aggregate=aggregate,
    )


def _build_fetch_query(shape: _QueryShape) -> str:
    lines = list(shape.base_lines)
    if shape.limit_line:
        lines.append(shape.limit_line)

    fetch_lines = ['fetch {']
    for index, variable in enumerate(shape.projection_vars):
        suffix = ',' if index < len(shape.projection_vars) - 1 else ''
        fetch_lines.extend(
            [
                f'    "{variable}": {{',
                f'        "iid": iid(${variable}),',
                f'        "data": {{ ${variable}.* }}',
                f'    }}{suffix}',
            ]
        )
    fetch_lines.append('};')
    return '\n'.join(lines + fetch_lines)


def _map_concept_documents(shape: _QueryShape, documents: list[dict[str, Any]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not shape.traversals:
        for document in documents:
            root_doc = document.get('root') if isinstance(document, dict) else None
            row = _document_to_row(shape.entity_by_var.get('root', 'Root'), root_doc)
            if row is not None:
                rows.append(row)
        return rows

    for document in documents:
        if not isinstance(document, dict):
            continue
        for traversal in shape.traversals:
            source_entity = shape.entity_by_var.get(traversal.source_var, traversal.source_var)
            target_entity = shape.entity_by_var.get(traversal.target_var, traversal.target_var)
            source_row = _document_to_row(source_entity, document.get(traversal.source_var))
            target_row = _document_to_row(target_entity, document.get(traversal.target_var))
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


def _document_to_row(entity_name: str, document: Any) -> dict[str, object] | None:
    if not isinstance(document, dict):
        return None
    data = document.get('data')
    if not isinstance(data, dict):
        data = {}
    row: dict[str, object] = {
        '_entity': entity_name,
        '_iid': str(document.get('iid') or '').strip(),
    }
    for key, value in data.items():
        attr = _snake_case(str(key))
        row[attr] = _normalize_value(value)
    return row


def _normalize_value(value: Any) -> object:
    if isinstance(value, dict):
        if 'value' in value and len(value) == 1:
            return value['value']
        return {str(key): _normalize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if hasattr(value, 'isoformat'):
        try:
            return value.isoformat()
        except Exception:
            return value
    return value


def _snake_case(value: str) -> str:
    text = str(value or '').strip().replace('-', '_')
    text = re.sub(r'([a-z0-9])([A-Z])', r'_', text)
    return text.lower()


def _normalize_entity_label(value: str) -> str:
    parts = [part for part in _snake_case(value).split('_') if part]
    return ''.join(_ENTITY_TOKEN_OVERRIDES.get(part, part.capitalize()) for part in parts)


def _normalize_relation_label(value: str) -> str:
    return _snake_case(value).upper()


def _best_identifier(row: dict[str, object]) -> str:
    for key in _IDENTIFIER_CANDIDATES:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    iid = row.get('_iid')
    return str(iid).strip() if iid is not None else ''
