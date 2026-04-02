from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TypeDBConfig:
    address: str
    database: str
    username: str
    password: str


class TypeDBConfigError(RuntimeError):
    pass


class TypeDBConnectionError(RuntimeError):
    pass


class TypeDBQueryError(RuntimeError):
    pass


def load_typedb_config() -> TypeDBConfig | None:
    address = os.getenv('TYPEDB_ADDRESS', '').strip()
    database = os.getenv('TYPEDB_DATABASE', '').strip()
    username = os.getenv('TYPEDB_USERNAME', '').strip()
    password = os.getenv('TYPEDB_PASSWORD', '').strip()

    if not address and not database and not username and not password:
        return None

    missing = [
        name
        for name, value in (
            ('TYPEDB_ADDRESS', address),
            ('TYPEDB_DATABASE', database),
            ('TYPEDB_USERNAME', username),
            ('TYPEDB_PASSWORD', password),
        )
        if not value
    ]
    if missing:
        raise TypeDBConfigError(f'Missing required TypeDB environment variables: {", ".join(missing)}')

    return TypeDBConfig(address=address, database=database, username=username, password=password)


class TypeDBClient:
    """Read-only TypeDB client scaffold for the instance QA pipeline."""

    def __init__(self, config: TypeDBConfig):
        self._config = config
        self._driver = None

    @property
    def config(self) -> TypeDBConfig:
        return self._config

    def connect(self) -> None:
        """Initialize a driver connection. Real wire-up is intentionally deferred in Task 1."""
        try:
            from typedb.driver import TypeDB
        except Exception as exc:  # pragma: no cover - import failures are environmental
            raise TypeDBConnectionError(f'Unable to import typedb-driver: {exc}') from exc

        try:
            # Keep scaffold minimal: create driver handle only.
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

        raise TypeDBQueryError('Read-only query execution scaffold is not implemented yet.')
