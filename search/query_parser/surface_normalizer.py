from __future__ import annotations

import re
import unicodedata

_STRIP_CHARS = " ?!\uFF1F\uFF01\uFF0C\u3002\uFF1B;\u3001"


def normalize_query(value: object) -> str:
    text = unicodedata.normalize('NFKC', str(value or ''))
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(?<![A-Za-z])\s+|\s+(?![A-Za-z])', '', text)
    return text.strip(_STRIP_CHARS)
