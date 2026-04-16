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
    assert '直接回答。跳过任何寒暄、开场白或礼貌性的结语。' in context.task_prompt
    assert '1~2 段自然语言' in context.task_prompt
    assert '云基础设施交付业务专家' in context.task_prompt
    assert '关键实例 ID' in context.task_prompt
    assert '严禁直接复述底层枚举值或系统码值' in context.task_prompt
    assert 'installing 应转译为“正在安装”' in context.task_prompt
    assert '回答口吻必须体现云基础设施交付业务视角。' in context.task_prompt
    assert '不要输出 iid' in context.style_prompt
    assert '不要直接输出底层英文枚举值' in context.style_prompt
    assert '只保留与问题直接相关的关键信息' in context.style_prompt
    assert '按业务含义组织答案' in context.style_prompt
    assert '不要一股脑罗列全部命中实例' in context.style_prompt

    payload = context.user_payload
    assert payload['question'] == 'L1-A机房断电一周，会有哪些影响？'
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


def test_build_llm_answer_context_injects_router_failure_diagnostics():
    bundle = _bundle()
    bundle.understanding['router_diagnostics'] = {
        'status': 'failed',
        'error_type': 'router_timeout',
        'error_message': 'timeout',
    }
    bundle.understanding['blocked_before_retrieval'] = True

    context = build_llm_answer_context(bundle)

    assert context.user_payload['router_diagnostics']['error_type'] == 'router_timeout'
    assert context.user_payload['blocked_before_retrieval'] is True
    assert '\u9519\u8bef\u7c7b\u578b\u3001\u53ef\u80fd\u539f\u56e0\u548c\u5efa\u8bae\u64cd\u4f5c' in context.to_messages()[1]['content']
    assert '\u4e0d\u8981\u628a\u7cfb\u7edf\u9519\u8bef\u5199\u6210\u4e1a\u52a1\u6570\u636e\u4e3a\u7a7a' in context.to_messages()[1]['content']
