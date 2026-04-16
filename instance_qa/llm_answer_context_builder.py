from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .evidence_models import EvidenceBundle
from .prompts import EVIDENCE_CONTRACT_PROMPT, ERROR_HANDLING_PROMPT, STYLE_PROMPT, SYSTEM_PROMPT, TASK_PROMPT


@dataclass(slots=True)
class LLMAnswerContext:
    system_prompt: str
    task_prompt: str
    evidence_contract_prompt: str
    style_prompt: str
    user_payload: dict[str, Any]

    def to_messages(self) -> list[dict[str, str]]:
        user_content = (
            f"{self.task_prompt}\n\n"
            f"{self.evidence_contract_prompt}\n\n"
            f"{self.style_prompt}\n\n"
            f"{ERROR_HANDLING_PROMPT}\n\n"
            f"evidence_payload:\n{json.dumps(self.user_payload, ensure_ascii=False)}"
        )
        return [
            {'role': 'system', 'content': self.system_prompt},
            {'role': 'user', 'content': user_content},
        ]


def build_llm_answer_context(bundle: EvidenceBundle) -> LLMAnswerContext:
    payload = _build_user_payload(bundle)
    return LLMAnswerContext(
        system_prompt=SYSTEM_PROMPT,
        task_prompt=TASK_PROMPT,
        evidence_contract_prompt=EVIDENCE_CONTRACT_PROMPT,
        style_prompt=STYLE_PROMPT,
        user_payload=payload,
    )


def _build_user_payload(bundle: EvidenceBundle) -> dict[str, Any]:
    data = bundle.to_dict()
    return {
        'question': data.get('question', ''),
        'understanding': data.get('understanding', {}),
        'positive_evidence': data.get('positive_evidence', []),
        'edges': data.get('edges', []),
        'paths': data.get('paths', []),
        'empty_entities': data.get('empty_entities', []),
        'unrelated_entities': data.get('unrelated_entities', []),
        'omitted_entities': data.get('omitted_entities', []),
        'router_diagnostics': data.get('understanding', {}).get('router_diagnostics', {}),
        'blocked_before_retrieval': bool(data.get('understanding', {}).get('blocked_before_retrieval', False)),
    }
