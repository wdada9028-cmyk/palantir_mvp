from cloud_delivery_ontology_palantir.instance_qa.evidence_models import (
    EmptyEntityEvidence,
    EntityEvidenceGroup,
    EvidenceBundle,
    EvidenceEdge,
    InstanceEvidence,
    OmittedEntityEvidence,
    SchemaContext,
    UnrelatedEntityEvidence,
)
from cloud_delivery_ontology_palantir.instance_qa.llm_answer_context_builder import build_llm_answer_context


def _bundle() -> EvidenceBundle:
    return EvidenceBundle(
        question='L1-A机房断电一周，会有哪些影响？',
        understanding={
            'anchor': {'entity': 'Room', 'id': 'L1-A'},
            'mode': 'impact_analysis',
        },
        positive_evidence=[
            EntityEvidenceGroup(
                entity='Floor',
                instances=[
                    InstanceEvidence(
                        entity='Floor',
                        iid='0x1e0002',
                        business_keys={'floor-id': 'L1'},
                        attributes={'floor-id': 'L1', 'floor-no': 1, 'install-sequence': 1},
                        schema_context=SchemaContext(
                            entity_name='Floor',
                            entity_zh='楼层',
                            key_attributes=['floor-id'],
                            relevant_relations=['floor-room'],
                        ),
                        paths=['Room(L1-A) <--FLOOR_ROOM-- Floor(L1)'],
                    )
                ],
            )
        ],
        edges=[
            EvidenceEdge(
                source_entity='Floor',
                source_id='L1',
                relation='FLOOR_ROOM',
                target_entity='Room',
                target_id='L1-A',
            )
        ],
        paths=['Room(L1-A) <--FLOOR_ROOM-- Floor(L1)'],
        empty_entities=[
            EmptyEntityEvidence(entity='PoDSchedule', reason='schema命中，但当前无实例数据'),
        ],
        unrelated_entities=[
            UnrelatedEntityEvidence(entity='WorkAssignment', reason='实例存在但与当前证据链无关联'),
        ],
        omitted_entities=[
            OmittedEntityEvidence(entity='PoDPosition', omitted_count=20, reason='超出上下文上限'),
        ],
    )


def test_build_llm_answer_context_contains_compact_payload_and_constraints():
    context = build_llm_answer_context(_bundle())

    assert "只能依据提供的证据回答" in context.system_prompt
    assert 'full-row' in context.evidence_contract_prompt
    assert 'iid' in context.evidence_contract_prompt
    assert '1~2 段自然语言' in context.task_prompt
    assert '业务专家' in context.task_prompt
    assert '关键实例 ID' in context.task_prompt
    assert '不要输出 iid' in context.style_prompt
    assert '只保留与问题直接相关的关键信息' in context.style_prompt
    assert '按业务含义组织答案' in context.style_prompt
    assert '不要一股脑罗列全部命中实例' in context.style_prompt

    payload = context.user_payload
    assert payload['question'] == 'L1-A\u673a\u623f\u65ad\u7535\u4e00\u5468\uff0c\u4f1a\u6709\u54ea\u4e9b\u5f71\u54cd\uff1f'
    assert payload['positive_evidence'][0]['instances'][0]['attributes']['floor-no'] == 1
    assert payload['positive_evidence'][0]['instances'][0]['iid'] == '0x1e0002'
    assert payload['empty_entities'][0]['entity'] == 'PoDSchedule'
    assert payload['unrelated_entities'][0]['entity'] == 'WorkAssignment'
    assert payload['omitted_entities'][0]['omitted_count'] == 20


def test_llm_answer_context_to_messages_contains_json_payload():
    context = build_llm_answer_context(_bundle())

    messages = context.to_messages()

    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'
    assert 'positive_evidence' in messages[1]['content']
    assert 'floor-no' in messages[1]['content']
