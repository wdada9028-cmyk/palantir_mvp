from cloud_delivery_ontology_palantir.instance_qa.typedb_client import TypeDBConfig, load_typedb_config


def test_load_typedb_config_reads_single_database_env(monkeypatch):
    monkeypatch.setenv('TYPEDB_ADDRESS', 'localhost:1729')
    monkeypatch.setenv('TYPEDB_DATABASE', 'cloud_delivery')
    monkeypatch.setenv('TYPEDB_USERNAME', 'admin')
    monkeypatch.setenv('TYPEDB_PASSWORD', 'secret')

    config = load_typedb_config()

    assert config == TypeDBConfig(
        address='localhost:1729',
        database='cloud_delivery',
        username='admin',
        password='secret',
    )


def test_load_typedb_config_returns_none_when_required_env_missing(monkeypatch):
    monkeypatch.delenv('TYPEDB_ADDRESS', raising=False)
    monkeypatch.delenv('TYPEDB_DATABASE', raising=False)
    monkeypatch.delenv('TYPEDB_USERNAME', raising=False)
    monkeypatch.delenv('TYPEDB_PASSWORD', raising=False)

    assert load_typedb_config() is None
