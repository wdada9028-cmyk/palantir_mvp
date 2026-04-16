from __future__ import annotations

import re

_DASH_TRANSLATION = str.maketrans({
    '‐': '-',
    '‑': '-',
    '‒': '-',
    '–': '-',
    '—': '-',
    '―': '-',
    '−': '-',
})


def normalize_anchor_text_light(value: str) -> str:
    text = str(value or '').translate(_DASH_TRANSLATION).strip().upper()
    text = re.sub(r'\s+', ' ', text)
    return text


def normalize_anchor_text_loose(value: str) -> str:
    light = normalize_anchor_text_light(value)
    return re.sub(r'[^A-Z0-9]+', '', light)
