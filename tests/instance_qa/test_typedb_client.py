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


class _FakePromise:
    def __init__(self, value=None, error: Exception | None = None):
        self._value = value
        self._error = error

    def resolve(self):
        if self._error is not None:
            raise self._error
        return self._value


class _FakeQueryAnswer:
    def __init__(self, *, docs=None):
        self._docs = docs or []

    def is_concept_documents(self):
        return True

    def as_concept_documents(self):
        return list(self._docs)


class _FakeQueryManager:
    def __init__(self, *, docs=None, error: Exception | None = None):
        self._docs = docs or []
        self._error = error
        self.seen_queries: list[str] = []

    def __call__(self, query: str):
        self.seen_queries.append(query)
        return _FakePromise(_FakeQueryAnswer(docs=self._docs), self._error)


class _FakeTransaction:
    def __init__(self, query_manager: _FakeQueryManager, seen_calls: list[tuple[str, object]]):
        self._query_manager = query_manager
        self._seen_calls = seen_calls

    def query(self, query: str):
        self._seen_calls.append(('query', query))
        return self._query_manager(query)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeDriver:
    def __init__(self, query_manager: _FakeQueryManager):
        self._query_manager = query_manager
        self.closed = False
        self.seen_calls: list[tuple[str, object]] = []
        self.address = ''
        self.credentials = None
        self.driver_options = None

    def transaction(self, database: str, transaction_type, options=None):
        self.seen_calls.append(('transaction', (database, transaction_type, options)))
        return _FakeTransaction(self._query_manager, self.seen_calls)

    def close(self):
        self.closed = True


def _install_fake_typedb(monkeypatch, *, query_manager: _FakeQueryManager):
    fake_driver = _FakeDriver(query_manager)
    module = types.ModuleType('typedb.driver')

    class _Credentials:
        def __init__(self, username: str, password: str):
            self.username = username
            self.password = password

    class _DriverOptions:
        def __init__(self, is_tls_enabled: bool = True, tls_root_ca_path=None):
            self.is_tls_enabled = is_tls_enabled
            self.tls_root_ca_path = tls_root_ca_path

    class _TypeDB:
        @staticmethod
        def driver(address: str, credentials, driver_options):
            fake_driver.address = address
            fake_driver.credentials = credentials
            fake_driver.driver_options = driver_options
            return fake_driver

    class _TransactionType:
        READ = 'READ'

    module.TypeDB = _TypeDB
    module.Credentials = _Credentials
    module.DriverOptions = _DriverOptions
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


def test_execute_readonly_uses_typedb_3_driver_and_returns_root_entity_rows(monkeypatch):
    query_manager = _FakeQueryManager(
        docs=[
            {
                'root': {
                    'iid': 'iid-room-01',
                    'data': {'room-id': '01', 'room-status': 'active'},
                }
            }
        ]
    )
    fake_driver = _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='admin', password='password'))
    client.connect()

    rows = client.execute_readonly("""match
$root isa room;
$root has room-id "01";
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
    assert fake_driver.credentials.username == 'admin'
    assert fake_driver.credentials.password == 'password'
    assert fake_driver.driver_options.is_tls_enabled is False
    assert ('transaction', ('cloud_delivery', 'READ', None)) in fake_driver.seen_calls
    fetch_query = query_manager.seen_queries[0]
    assert 'fetch {' in fetch_query
    assert '"iid": iid($root)' in fetch_query
    assert '"data": { $root.* }' in fetch_query


def test_execute_readonly_returns_neighbor_rows_with_link_metadata(monkeypatch):
    query_manager = _FakeQueryManager(
        docs=[
            {
                'root': {
                    'iid': 'iid-room-01',
                    'data': {'room-id': '01'},
                },
                'n1': {
                    'iid': 'iid-wa-001',
                    'data': {'assignment-id': 'WA-001'},
                },
            }
        ]
    )
    _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='admin', password='password'))
    client.connect()

    rows = client.execute_readonly("""match
$root isa room;
$root has room-id "01";
(assignment-record: $n1, assigned-room: $root) isa work-assignment-room;
$n1 isa work-assignment;
get $root, $n1;
limit 20;""")

    assert rows == [
        {
            '_entity': 'WorkAssignment',
            '_iid': 'iid-wa-001',
            'assignment_id': 'WA-001',
            '_source_entity': 'WorkAssignment',
            '_source_id': 'WA-001',
            '_relation': 'WORK_ASSIGNMENT_ROOM',
            '_target_entity': 'Room',
            '_target_id': '01',
        }
    ]


def test_execute_readonly_normalizes_business_entity_names(monkeypatch):
    query_manager = _FakeQueryManager(
        docs=[
            {
                'root': {
                    'iid': 'iid-ps-001',
                    'data': {'pod-id': 'POD-001'},
                }
            }
        ]
    )
    _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='admin', password='password'))
    client.connect()

    rows = client.execute_readonly("""match
$root isa pod-schedule;
get $root;
limit 20;""")

    assert rows == [{'_entity': 'PoDSchedule', '_iid': 'iid-ps-001', 'pod_id': 'POD-001'}]


def test_execute_readonly_wraps_query_errors(monkeypatch):
    query_manager = _FakeQueryManager(error=RuntimeError('boom'))
    _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='admin', password='password'))
    client.connect()

    with pytest.raises(TypeDBQueryError, match='boom'):
        client.execute_readonly("""match
$root isa room;
get $root;""")


def test_execute_readonly_requires_connection():
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='admin', password='password'))

    with pytest.raises(TypeDBConnectionError, match='not connected'):
        client.execute_readonly("""match
$root isa room;
get $root;""")


def test_typedb_client_context_manager_connects_and_closes(monkeypatch):
    query_manager = _FakeQueryManager(docs=[])
    fake_driver = _install_fake_typedb(monkeypatch, query_manager=query_manager)
    client = TypeDBClient(TypeDBConfig(address='localhost:1729', database='cloud_delivery', username='admin', password='password'))

    with client as connected:
        assert connected is client
        assert client._driver is not None

    assert fake_driver.closed is True
