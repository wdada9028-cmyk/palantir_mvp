from __future__ import annotations

import sys
import types

import pytest

from cloud_delivery_ontology_palantir.instance_qa.typedb_client import (
    TypeDBClient,
    TypeDBConfig,
    TypeDBConfigError,
    TypeDBConnectionError,
    TypeDBQueryError,
    load_typedb_config,
)


class _FakeAttributeType:
    def __init__(self, name: str):
        self.name = name

    def get_label(self):
        return self


class _FakeAttribute:
    def __init__(self, name: str, value: object):
        self._type = _FakeAttributeType(name)
        self._value = value

    def get_type(self):
        return self._type

    def get_value(self):
        return self._value


class _FakeEntityType:
    def __init__(self, name: str):
        self.name = name

    def get_label(self):
        return self


class _FakeEntity:
    def __init__(self, entity: str, iid: str, attributes: dict[str, object]):
        self._entity = entity
        self._iid = iid
        self._attributes = attributes

    def is_entity(self):
        return True

    def is_relation(self):
        return False

    def is_attribute(self):
        return False

    def as_entity(self):
        return self

    def get_iid(self):
        return self._iid

    def get_type(self):
        return _FakeEntityType(self._entity)

    def get_has(self, tx):
        return [_FakeAttribute(name, value) for name, value in self._attributes.items()]


class _FakeConceptMap:
    def __init__(self, values: dict[str, object]):
        self._values = values

    def get(self, name: str):
        return self._values.get(name)


class _FakeQueryManager:
    def __init__(self, results=None, error: Exception | None = None):
        self._results = results or []
        self._error = error
        self.seen_queries: list[str] = []

    def get(self, query: str):
        self.seen_queries.append(query)
        if self._error is not None:
            raise self._error
        return list(self._results)


class _FakeTransaction:
    def __init__(self, query_manager: _FakeQueryManager):
        self.query = query_manager

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeSession:
    def __init__(self, query_manager: _FakeQueryManager, seen_sessions: list[tuple[str, object]]):
        self._query_manager = query_manager
        self._seen_sessions = seen_sessions

    def transaction(self, transaction_type):
        self._seen_sessions.append(('transaction', transaction_type))
        return _FakeTransaction(self._query_manager)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeDriver:
    def __init__(self, query_manager: _FakeQueryManager):
        self._query_manager = query_manager
        self.closed = False
        self.seen_sessions: list[tuple[str, object]] = []

    def session(self, database: str, session_type):
        self.seen_sessions.append((database, session_type))
        return _FakeSession(self._query_manager, self.seen_sessions)

    def close(self):
        self.closed = True


def _install_fake_typedb(monkeypatch, *, query_manager: _FakeQueryManager):
    fake_driver = _FakeDriver(query_manager)
    module = types.ModuleType('typedb.driver')

    class _TypeDB:
        @staticmethod
        def core_driver(address: str):
            fake_driver.address = address
            return fake_driver

    class _SessionType:
        DATA = 'DATA'

    class _TransactionType:
        READ = 'READ'

    module.TypeDB = _TypeDB
    module.SessionType = _SessionType
    module.TransactionType = _TransactionType
    monkeypatch.setitem(sys.modules, 'typedb', types.ModuleType('typedb'))
    monkeypatch.setitem(sys.modules, 'typedb.driver', module)
    return fake_driver


def test_load_typedb_config_reads_single_database_env_without_credentials(monkeypatch):
    monkeypatch.setenv('TYPEDB_ADDRESS', 'localhost:1729')
    monkeypatch.setenv('TYPEDB_DATABASE', 'cloud_delivery')
    monkeypatch.delenv('TYPEDB_USERNAME', raising=False)
    monkeypatch.delenv('TYPEDB_PASSWORD', raising=False)

    config = load_typedb_config()

    assert config == TypeDBConfig(
        address='localhost:1729',
        database='cloud_delivery',
        username='',
        password='',
    )


def test_load_typedb_config_returns_none_when_required_env_missing(monkeypatch):
    monkeypatch.delenv('TYPEDB_ADDRESS', raising=False)
    monkeypatch.delenv('TYPEDB_DATABASE', raising=False)
    monkeypatch.delenv('TYPEDB_USERNAME', raising=False)
    monkeypatch.delenv('TYPEDB_PASSWORD', raising=False)

    assert load_typedb_config() is None


def test_load_typedb_config_rejects_partial_required_env(monkeypatch):
    monkeypatch.setenv('TYPEDB_ADDRESS', 'localhost:1729')
    monkeypatch.delenv('TYPEDB_DATABASE', raising=False)

    with pytest.raises(TypeDBConfigError, match='TYPEDB_DATABASE'):
        load_typedb_config()


def test_load_typedb_config_rejects_partial_optional_credentials(monkeypatch):
    monkeypatch.setenv('TYPEDB_ADDRESS', 'localhost:1729')
    monkeypatch.setenv('TYPEDB_DATABASE', 'cloud_delivery')
    monkeypatch.setenv('TYPEDB_USERNAME', 'admin')
    monkeypatch.delenv('TYPEDB_PASSWORD', raising=False)

    with pytest.raises(TypeDBConfigError, match='TYPEDB_PASSWORD'):
        load_typedb_config()


def test_execute_readonly_returns_root_entity_rows(monkeypatch):
    query_manager = _FakeQueryManager(
        results=[
            _FakeConceptMap({'root': _FakeEntity('room', 'iid-room-01', {'room-id': '01', 'room-status': 'active'})})
        ]
    )
    fake_driver = _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='', password=''))
    client.connect()

    rows = client.execute_readonly("""match
$root isa room;
$root has room-id \"01\";
get $root;
limit 20;""")

    assert rows == [
        {
            '_entity': 'Room',
            '_iid': 'iid-room-01',
            'room_id': '01',
            'room_status': 'active',
        }
    ]
    assert fake_driver.address == 'localhost:1729'
    assert ('cloud_delivery', 'DATA') in fake_driver.seen_sessions
    assert ('transaction', 'READ') in fake_driver.seen_sessions


def test_execute_readonly_returns_neighbor_rows_with_link_metadata(monkeypatch):
    query_manager = _FakeQueryManager(
        results=[
            _FakeConceptMap(
                {
                    'root': _FakeEntity('room', 'iid-room-01', {'room-id': '01'}),
                    'n1': _FakeEntity('work-assignment', 'iid-wa-001', {'assignment-id': 'WA-001'}),
                }
            )
        ]
    )
    _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='', password=''))
    client.connect()

    rows = client.execute_readonly(
        """match
$root isa room;
$root has room-id \"01\";
($n1, $root) isa occurs-in;
$n1 isa work-assignment;
get $root, $n1;
limit 20;"""
    )

    assert rows == [
        {
            '_entity': 'WorkAssignment',
            '_iid': 'iid-wa-001',
            'assignment_id': 'WA-001',
            '_source_entity': 'WorkAssignment',
            '_source_id': 'WA-001',
            '_relation': 'OCCURS_IN',
            '_target_entity': 'Room',
            '_target_id': '01',
        }
    ]


def test_execute_readonly_wraps_query_errors(monkeypatch):
    query_manager = _FakeQueryManager(error=RuntimeError('boom'))
    _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='', password=''))
    client.connect()

    with pytest.raises(TypeDBQueryError, match='boom'):
        client.execute_readonly("""match
$root isa room;
get $root;""")


def test_execute_readonly_requires_connection():
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='', password=''))

    with pytest.raises(TypeDBConnectionError, match='not connected'):
        client.execute_readonly("""match
$root isa room;
get $root;""")



def test_execute_readonly_normalizes_business_entity_names(monkeypatch):
    query_manager = _FakeQueryManager(
        results=[
            _FakeConceptMap({'root': _FakeEntity('pod-schedule', 'iid-ps-001', {'pod-id': 'POD-001'})})
        ]
    )
    _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='', password=''))
    client.connect()

    rows = client.execute_readonly("""match
$root isa pod-schedule;
get $root;
limit 20;""")

    assert rows == [{'_entity': 'PoDSchedule', '_iid': 'iid-ps-001', 'pod_id': 'POD-001'}]
