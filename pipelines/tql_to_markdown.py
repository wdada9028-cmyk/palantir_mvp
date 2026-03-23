from __future__ import annotations

import os
from pathlib import Path

import httpx

_DEFAULT_MODEL = 'qwen2.5-32b-instruct'


def _required_env(name: str) -> str:
    value = os.getenv(name, '').strip()
    if not value:
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


def _extract_markdown_content(payload: dict, *, source_file: str) -> str:
    choices = payload.get('choices')
    if not isinstance(choices, list) or not choices:
        raise RuntimeError(f'Qwen response missing choices for {source_file}')

    message = choices[0].get('message') if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise RuntimeError(f'Qwen response missing message for {source_file}')

    content = message.get('content')
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            text_value = item.get('text')
            if isinstance(text_value, str):
                text_parts.append(text_value)
        return ''.join(text_parts)

    return ''


def _strip_markdown_fences(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith('```'):
        return stripped

    lines = stripped.splitlines()
    if len(lines) < 2:
        return stripped.replace('```', '').strip()

    if lines[-1].strip() != '```':
        return stripped

    return '\n'.join(lines[1:-1]).strip()


def convert_tql_to_markdown(tql_text: str, *, source_file: str, timeout_s: float = 30.0) -> str:
    api_base = _required_env('QWEN_API_BASE').rstrip('/')
    api_key = _required_env('QWEN_API_KEY')
    model = os.getenv('QWEN_MODEL', _DEFAULT_MODEL).strip() or _DEFAULT_MODEL

    endpoint = f'{api_base}/chat/completions'
    payload = {
        'model': model,
        'temperature': 0,
        'messages': [
            {
                'role': 'system',
                'content': 'You convert ontology TQL into clean Markdown definition documents. Return Markdown only.',
            },
            {
                'role': 'user',
                'content': f'Source file: {source_file}\n\nConvert the following TQL into Markdown.\n\n{tql_text}',
            },
        ],
    }

    try:
        with httpx.Client(timeout=timeout_s) as client:
            response = client.post(
                endpoint,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise RuntimeError(f'Failed to call Qwen API for {source_file}: {exc}') from exc

    if response.status_code >= 400:
        body = response.text.strip()
        snippet = body[:500] + ('...' if len(body) > 500 else '')
        raise RuntimeError(
            f'Qwen API request failed for {source_file}: HTTP {response.status_code} - {snippet or "<empty body>"}'
        )

    try:
        response_payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f'Qwen API returned non-JSON response for {source_file}') from exc

    markdown = _strip_markdown_fences(_extract_markdown_content(response_payload, source_file=source_file))
    if not markdown:
        raise RuntimeError(f'Qwen API returned empty markdown for {source_file}')
    return markdown


def convert_tql_file_to_markdown_file(input_file: str | Path) -> Path:
    input_path = Path(input_file)
    tql_text = input_path.read_text(encoding='utf-8')
    markdown = convert_tql_to_markdown(tql_text, source_file=str(input_path))

    output_path = input_path.with_name(f'{input_path.stem}.converted.md')
    output_path.write_text(markdown, encoding='utf-8')
    return output_path
