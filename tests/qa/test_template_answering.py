from cloud_delivery_ontology_palantir.qa.template_answering import build_template_answer, _build_search_trace_report, _dedupe_trace_steps
from cloud_delivery_ontology_palantir.search.ontology_query_models import (
    EvidenceItem,
    OntologyEvidenceBundle,
    RetrievalStep,
    SearchTrace,
    TraceExpansionStep,
)


def _build_trace_bundle() -> OntologyEvidenceBundle:
    return OntologyEvidenceBundle(
        question='\u5230\u8d27\u8ba1\u5212\u548c\u6cca\u4f4d\u662f\u4ec0\u4e48\u5173\u7cfb',
        seed_node_ids=['object_type:ArrivalPlan'],
        matched_node_ids=['object_type:ArrivalPlan', 'object_type:PoDPosition'],
        matched_edge_ids=['e1'],
        highlight_steps=[RetrievalStep(action='anchor_node', message='\u5b9a\u4f4d\u5230 ArrivalPlan', node_ids=['object_type:ArrivalPlan'])],
        evidence_chain=[
            EvidenceItem(
                evidence_id='E1',
                kind='seed',
                label='ArrivalPlan',
                message='\u95ee\u9898\u547d\u4e2d\u4e86\u5b9e\u4f53 \u5230\u8d27\u8ba1\u5212(ArrivalPlan)',
                node_ids=['object_type:ArrivalPlan'],
                why_matched=['\u8bed\u4e49\u89e3\u6790\u8ba4\u4e3a\u95ee\u9898\u5728\u95ee\u5230\u8d27\u8ba1\u5212'],
            ),
            EvidenceItem(
                evidence_id='E2',
                kind='relation',
                label='ArrivalPlan REFERENCES PoDPosition',
                message='\u5230\u8d27\u8ba1\u5212\u5f15\u7528\u6cca\u4f4d',
                node_ids=['object_type:ArrivalPlan', 'object_type:PoDPosition'],
                edge_ids=['e1'],
                why_matched=['\u5173\u7cfb\u90bb\u63a5\u6269\u5c55'],
            ),
        ],
        insufficient_evidence=False,
        search_trace=SearchTrace(
            seed_node_ids=['object_type:ArrivalPlan'],
            seed_resolution_source='llm',
            seed_resolution_reasoning='\u8bed\u4e49\u89e3\u6790\u8ba4\u4e3a\u95ee\u9898\u5728\u95ee\u5230\u8d27\u8ba1\u5212',
            seed_resolution_error='',
            expansion_steps=[
                TraceExpansionStep(
                    step=1,
                    from_node_id='object_type:ArrivalPlan',
                    edge_id='e1',
                    to_node_id='object_type:PoDPosition',
                    relation='REFERENCES',
                    reason='\u5173\u7cfb\u90bb\u63a5\u6269\u5c55',
                    snapshot_node_ids=['object_type:ArrivalPlan', 'object_type:PoDPosition'],
                    snapshot_edge_ids=['e1'],
                )
            ],
        ),
        display_name_map={
            'object_type:ArrivalPlan': '\u5230\u8d27\u8ba1\u5212(ArrivalPlan)',
            'object_type:PoDPosition': '\u6cca\u4f4d(PoDPosition)',
        },
        relation_name_map={'REFERENCES': '[\u5f15\u7528]'},
    )


def test_build_template_answer_separates_summary_from_trace_report():
    bundle = _build_trace_bundle()

    answer = build_template_answer(bundle)

    assert '\u68c0\u7d22\u8def\u5f84\u62a5\u544a' not in answer.answer
    assert '\u968f\u540e\u4ece' not in answer.answer
    assert '\u5230\u8d27\u8ba1\u5212(ArrivalPlan)' not in answer.answer
    assert '\u5230\u8d27\u8ba1\u5212' in answer.answer
    assert '\u6cca\u4f4d' in answer.answer


def test_build_search_trace_report_only_annotates_first_entity_occurrence_with_english_name():
    bundle = OntologyEvidenceBundle(
        question='PoD\u6392\u671f\u5982\u4f55\u4f5c\u7528\u4e8ePoD',
        seed_node_ids=['object_type:PoDSchedule'],
        matched_node_ids=['object_type:PoDSchedule', 'object_type:PoD', 'object_type:ActivityInstance'],
        matched_edge_ids=['e1', 'e2'],
        highlight_steps=[],
        evidence_chain=[],
        insufficient_evidence=False,
        search_trace=SearchTrace(
            seed_node_ids=['object_type:PoDSchedule'],
            seed_resolution_source='alias_rule',
            seed_resolution_reasoning='PoDSchedule',
            seed_resolution_error='',
            expansion_steps=[
                TraceExpansionStep(
                    step=1,
                    from_node_id='object_type:PoDSchedule',
                    edge_id='e1',
                    to_node_id='object_type:PoD',
                    relation='APPLIES_TO',
                    reason='\u5173\u7cfb\u90bb\u63a5\u6269\u5c55',
                    snapshot_node_ids=['object_type:PoDSchedule', 'object_type:PoD'],
                    snapshot_edge_ids=['e1'],
                ),
                TraceExpansionStep(
                    step=2,
                    from_node_id='object_type:PoDSchedule',
                    edge_id='e2',
                    to_node_id='object_type:ActivityInstance',
                    relation='CONTAINS',
                    reason='\u5173\u7cfb\u90bb\u63a5\u6269\u5c55',
                    snapshot_node_ids=['object_type:PoDSchedule', 'object_type:PoD', 'object_type:ActivityInstance'],
                    snapshot_edge_ids=['e1', 'e2'],
                ),
            ],
        ),
        display_name_map={
            'object_type:PoDSchedule': 'PoD\u6392\u671f(PoDSchedule)',
            'object_type:PoD': 'PoD\u4ea4\u4ed8\u5355\u5143(PoD)',
            'object_type:ActivityInstance': '\u6d3b\u52a8\u5b9e\u4f8b(ActivityInstance)',
        },
        relation_name_map={'APPLIES_TO': '[\u4f5c\u7528\u4e8e]', 'CONTAINS': '[\u5305\u542b]'},
    )

    trace = _build_search_trace_report(bundle, _dedupe_trace_steps(bundle.search_trace.expansion_steps))

    assert trace.count('PoD\u6392\u671f(PoDSchedule)') == 1
    assert '\u8bc6\u522b\u51fa\u7684\u6838\u5fc3\u5b9e\u4f53\n- PoD\u6392\u671f(PoDSchedule)' in trace
    assert '\n\n\u5b9e\u4f53\u8bc6\u522b\u4f9d\u636e\n- PoDSchedule' in trace
    assert trace.count('\u5173\u952e\u6269\u5c55') == 1
    assert '\n\n\u5173\u952e\u6269\u5c55\n- \u4ecePoD\u6392\u671f \u6cbf [\u4f5c\u7528\u4e8e] \u6269\u5c55\u5230 PoD\u4ea4\u4ed8\u5355\u5143(PoD)\n- \u4ecePoD\u6392\u671f \u6cbf [\u5305\u542b] \u6269\u5c55\u5230 \u6d3b\u52a8\u5b9e\u4f8b(ActivityInstance)' in trace
    assert '\n\n\u547d\u4e2d\u7684\u5173\u952e\u5173\u7cfb\n- PoD\u6392\u671f [\u4f5c\u7528\u4e8e] PoD\u4ea4\u4ed8\u5355\u5143\n- PoD\u6392\u671f [\u5305\u542b] \u6d3b\u52a8\u5b9e\u4f8b' in trace
    assert '\uff1b' not in trace


def test_build_template_answer_keeps_insufficient_evidence_summary_user_facing():
    bundle = OntologyEvidenceBundle(
        question='\u54ea\u4e9b\u670d\u52a1\u5668\u5b95\u673a',
        seed_node_ids=['object_type:PoD'],
        matched_node_ids=['object_type:PoD'],
        matched_edge_ids=[],
        highlight_steps=[RetrievalStep(action='anchor_node', message='\u5b9a\u4f4d\u5230 PoD', node_ids=['object_type:PoD'])],
        evidence_chain=[
            EvidenceItem(
                evidence_id='E1',
                kind='seed',
                label='PoD',
                message='\u95ee\u9898\u547d\u4e2d\u4e86\u5b9e\u4f53 \u8bbe\u5907\u843d\u4f4d\u70b9(PoD)',
                node_ids=['object_type:PoD'],
                why_matched=['\u5b9e\u4f53\u540d\u79f0\u5339\u914d'],
            )
        ],
        insufficient_evidence=True,
        search_trace=SearchTrace(seed_node_ids=['object_type:PoD']),
        display_name_map={'object_type:PoD': '\u8bbe\u5907\u843d\u4f4d\u70b9(PoD)'},
        relation_name_map={},
    )

    answer = build_template_answer(bundle)

    assert '\u8bc1\u636e\u4e0d\u8db3' in answer.answer
    assert '\u68c0\u7d22\u8def\u5f84\u62a5\u544a' not in answer.answer
    assert '\u8bbe\u5907\u843d\u4f4d\u70b9(PoD)' not in answer.answer
    assert '\u8bbe\u5907\u843d\u4f4d\u70b9' in answer.answer
    assert '[E1]' not in answer.answer
