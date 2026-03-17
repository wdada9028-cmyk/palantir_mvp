from __future__ import annotations

from dataclasses import dataclass

from ..search.ontology_query_models import OntologyEvidenceBundle


@dataclass(slots=True)
class TemplateAnswer:
    answer: str
    insufficient_evidence: bool

    def to_dict(self) -> dict[str, object]:
        return {
            'answer': self.answer,
            'insufficient_evidence': self.insufficient_evidence,
        }


def build_template_answer(bundle: OntologyEvidenceBundle) -> TemplateAnswer:
    evidence_refs = ''.join(f'[{item.evidence_id}]' for item in bundle.evidence_chain)
    relation_items = [item for item in bundle.evidence_chain if item.kind == 'relation']
    seed_labels = [item.label for item in bundle.evidence_chain if item.kind in {'seed', 'node'}]

    if bundle.insufficient_evidence:
        anchor_text = f'已命中本体实体：{", ".join(seed_labels)}。' if seed_labels else ''
        answer = (
            f'证据不足：当前系统仅包含本体定义，不包含实例运行状态或实时数据，'
            f'无法直接回答“{bundle.question}”。{anchor_text}证据：{evidence_refs or "[E0]"}。'
        )
        return TemplateAnswer(answer=answer, insufficient_evidence=True)

    if relation_items:
        relation_text = '；'.join(item.label for item in relation_items)
        answer = f'根据当前本体定义，命中了这些关系：{relation_text}。证据：{evidence_refs}。'
        return TemplateAnswer(answer=answer, insufficient_evidence=False)

    if seed_labels:
        entity_text = '、'.join(seed_labels)
        answer = f'根据当前本体定义，问题主要命中实体：{entity_text}。证据：{evidence_refs}。'
        return TemplateAnswer(answer=answer, insufficient_evidence=False)

    answer = f'证据不足：当前本体定义中未匹配到可用实体或关系。证据：{evidence_refs or "[E0]"}。'
    return TemplateAnswer(answer=answer, insufficient_evidence=True)
