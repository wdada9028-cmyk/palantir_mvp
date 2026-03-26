from __future__ import annotations

from pathlib import Path
from typing import Any


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    try:
        import yaml  # type: ignore
    except Exception:
        return _load_simple_yaml(path)
    with path.open('r', encoding='utf-8') as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f'Expected top-level mapping in {path}')
    return payload


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    current_key: str | None = None
    current_nested_key: str | None = None
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith('#'):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(' '))
        line = raw_line.strip()
        if indent == 0 and line.endswith(':'):
            current_key = line[:-1].strip()
            root[current_key] = []
            current_nested_key = None
            continue
        if current_key is None:
            raise ValueError(f'Malformed YAML near: {raw_line}')
        if indent == 2 and line.endswith(':'):
            if isinstance(root[current_key], list):
                root[current_key] = {}
            current_nested_key = line[:-1].strip()
            root[current_key][current_nested_key] = []
            continue
        if indent == 2 and ': ' in line:
            if isinstance(root[current_key], list):
                root[current_key] = {}
            key, value = line.split(': ', 1)
            root[current_key][key.strip()] = _parse_scalar(value.strip())
            current_nested_key = None
            continue
        if line.startswith('- '):
            item = _parse_scalar(line[2:].strip())
            if current_nested_key is not None:
                container = root[current_key][current_nested_key]
                if not isinstance(container, list):
                    raise ValueError(f'Expected list at {current_key}.{current_nested_key}')
                container.append(item)
            else:
                container = root[current_key]
                if not isinstance(container, list):
                    raise ValueError(f'Expected list at {current_key}')
                container.append(item)
            continue
        raise ValueError(f'Unsupported YAML line: {raw_line}')
    return root


def _parse_scalar(value: str) -> Any:
    if value.isdigit():
        return int(value)
    return value.strip("\"'")
