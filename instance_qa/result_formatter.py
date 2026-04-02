from __future__ import annotations


def build_generator_context(
    *,
    question: str,
    schema_summary: dict[str, object],
    fact_pack: dict[str, object],
    reasoning_result: dict[str, object],
) -> dict[str, object]:
    return {
        'question': question,
        'schema_summary': schema_summary,
        'fact_pack': fact_pack,
        'reasoning': reasoning_result,
    }
