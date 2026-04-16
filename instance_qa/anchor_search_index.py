from __future__ import annotations

import json
import sqlite3
from pathlib import Path


_SCHEMA = '''
CREATE TABLE IF NOT EXISTS anchor_index (
  entity TEXT NOT NULL,
  attribute TEXT NOT NULL,
  raw_value TEXT NOT NULL,
  normalized_value TEXT NOT NULL,
  iid TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_anchor_norm ON anchor_index(normalized_value);
CREATE INDEX IF NOT EXISTS idx_anchor_entity_norm ON anchor_index(entity, normalized_value);
CREATE INDEX IF NOT EXISTS idx_anchor_raw ON anchor_index(raw_value);
'''


def normalize_anchor_value(value: str) -> str:
    return ''.join(ch for ch in str(value or '').casefold() if ch.isalnum())



def build_anchor_search_index(rows: list[dict[str, object]], *, db_path: Path) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        conn.execute('DELETE FROM anchor_index')
        payloads = [
            (
                str(row.get('entity') or '').strip(),
                str(row.get('attribute') or '').strip(),
                str(row.get('raw_value') or '').strip(),
                normalize_anchor_value(str(row.get('raw_value') or '').strip()),
                str(row.get('iid') or '').strip(),
                json.dumps(row.get('payload') or {}, ensure_ascii=False),
            )
            for row in rows
            if str(row.get('entity') or '').strip()
            and str(row.get('attribute') or '').strip()
            and str(row.get('raw_value') or '').strip()
            and str(row.get('iid') or '').strip()
        ]
        conn.executemany(
            'INSERT INTO anchor_index(entity, attribute, raw_value, normalized_value, iid, payload_json) VALUES (?, ?, ?, ?, ?, ?)',
            payloads,
        )
    return db_path



def search_anchor_candidates(db_path: Path, raw_anchor_text: str, *, top_k: int = 20) -> list[dict[str, object]]:
    db_path = Path(db_path)
    if not db_path.exists():
        return []

    query = str(raw_anchor_text or '').strip()
    normalized = normalize_anchor_value(query)
    limit = max(int(top_k), 1)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        exact_rows = conn.execute(
            'SELECT entity, attribute, raw_value, normalized_value, iid, payload_json FROM anchor_index WHERE raw_value = ? LIMIT ?',
            (query, limit),
        ).fetchall()
        if exact_rows:
            return [_to_hit(row, 'exact') for row in exact_rows[:limit]]

        normalized_rows = conn.execute(
            'SELECT entity, attribute, raw_value, normalized_value, iid, payload_json FROM anchor_index WHERE normalized_value = ? LIMIT ?',
            (normalized, limit),
        ).fetchall()
        if normalized_rows:
            return [_to_hit(row, 'normalized') for row in normalized_rows[:limit]]

        like_rows = conn.execute(
            'SELECT entity, attribute, raw_value, normalized_value, iid, payload_json FROM anchor_index WHERE normalized_value LIKE ? ORDER BY raw_value LIMIT ?',
            (f'%{normalized}%', limit),
        ).fetchall()
        return [_to_hit(row, 'contains') for row in like_rows[:limit]]



def _to_hit(row: sqlite3.Row, match_stage: str) -> dict[str, object]:
    return {
        'entity': str(row['entity']),
        'attribute': str(row['attribute']),
        'raw_value': str(row['raw_value']),
        'normalized_value': str(row['normalized_value']),
        'iid': str(row['iid']),
        'payload': json.loads(str(row['payload_json']) or '{}'),
        'match_stage': match_stage,
    }
