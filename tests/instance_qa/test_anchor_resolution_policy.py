from cloud_delivery_ontology_palantir.instance_qa.anchor_candidate_resolver import AnchorCandidate, AnchorResolutionResult
from cloud_delivery_ontology_palantir.instance_qa.anchor_candidate_ranker import AnchorRankDecision
from cloud_delivery_ontology_palantir.instance_qa.anchor_resolution_policy import apply_anchor_resolution_policy


def _deterministic_result(*, match_stage: str = 'loose', selected: bool = False) -> AnchorResolutionResult:
    row_1 = {'pod_id': 'POD-001'}
    row_2 = {'pod_id': 'POD-002'}
    candidate_1 = AnchorCandidate(entity='PoD', attribute='pod_id', value='POD-001', source_row=row_1)
    candidate_2 = AnchorCandidate(entity='PoD', attribute='pod_id', value='POD-002', source_row=row_2)
    return AnchorResolutionResult(
        raw_anchor_text='pod-001',
        match_stage=match_stage,
        selected=candidate_1 if selected else None,
        candidates=[candidate_1, candidate_2],
    )


def _candidate_context() -> dict[str, object]:
    return {
        'raw_anchor_text': 'pod-001',
        'question': 'pod-001???????',
        'candidate_entity': 'PoD',
        'candidates': [
            {
                'candidate_id': 'cand_1',
                'entity': 'PoD',
                'locator': {
                    'matched_attribute': 'pod_id',
                    'matched_value': 'POD-001',
                    'match_stage': 'light',
                },
            },
            {
                'candidate_id': 'cand_2',
                'entity': 'PoD',
                'locator': {
                    'matched_attribute': 'pod_id',
                    'matched_value': 'POD-002',
                    'match_stage': 'light',
                },
            },
        ],
    }


def test_apply_anchor_resolution_policy_accepts_high_confidence_select():
    payload = apply_anchor_resolution_policy(
        deterministic_result=_deterministic_result(),
        candidate_context=_candidate_context(),
        rank_decision=AnchorRankDecision(decision='select', selected_candidate_id='cand_2', confidence=0.92, reason='best'),
    )

    assert payload is not None
    assert set(payload.keys()) == {'raw_anchor_text', 'match_stage', 'selection', 'selected', 'candidates'}
    assert payload['selection']['decision'] == 'select'
    assert payload['selection']['confidence_tier'] == 'high'
    assert payload['selected'] == {'entity': 'PoD', 'attribute': 'pod_id', 'value': 'POD-002'}


def test_apply_anchor_resolution_policy_marks_medium_confidence_select():
    payload = apply_anchor_resolution_policy(
        deterministic_result=_deterministic_result(),
        candidate_context=_candidate_context(),
        rank_decision=AnchorRankDecision(decision='select', selected_candidate_id='cand_1', confidence=0.70, reason='good'),
    )

    assert payload is not None
    assert payload['selection']['decision'] == 'select'
    assert payload['selection']['confidence_tier'] == 'medium'
    assert payload['selected'] == {'entity': 'PoD', 'attribute': 'pod_id', 'value': 'POD-001'}


def test_apply_anchor_resolution_policy_downgrades_low_confidence_select_to_ambiguous():
    payload = apply_anchor_resolution_policy(
        deterministic_result=_deterministic_result(),
        candidate_context=_candidate_context(),
        rank_decision=AnchorRankDecision(decision='select', selected_candidate_id='cand_1', confidence=0.30, reason='weak'),
    )

    assert payload is not None
    assert payload['selection']['decision'] == 'ambiguous'
    assert payload['selection']['confidence_tier'] == 'low'
    assert payload['selected'] is None


def test_apply_anchor_resolution_policy_does_not_force_select_on_reject():
    payload = apply_anchor_resolution_policy(
        deterministic_result=_deterministic_result(),
        candidate_context=_candidate_context(),
        rank_decision=AnchorRankDecision(decision='reject', selected_candidate_id='', confidence=0.95, reason='no match'),
    )

    assert payload is not None
    assert payload['selection']['decision'] == 'reject'
    assert payload['selected'] is None


def test_apply_anchor_resolution_policy_does_not_force_select_on_ambiguous():
    payload = apply_anchor_resolution_policy(
        deterministic_result=_deterministic_result(),
        candidate_context=_candidate_context(),
        rank_decision=AnchorRankDecision(decision='ambiguous', selected_candidate_id='', confidence=0.55, reason='multiple'),
    )

    assert payload is not None
    assert payload['selection']['decision'] == 'ambiguous'
    assert payload['selected'] is None


def test_apply_anchor_resolution_policy_short_circuits_on_exact_or_light_selected_without_ranker():
    payload = apply_anchor_resolution_policy(
        deterministic_result=_deterministic_result(match_stage='exact', selected=True),
        candidate_context=_candidate_context(),
        rank_decision=None,
    )

    assert payload is not None
    assert payload['selection']['source'] == 'deterministic_short_circuit'
    assert payload['selection']['decision'] == 'select'
    assert payload['selected'] == {'entity': 'PoD', 'attribute': 'pod_id', 'value': 'POD-001'}


def test_apply_anchor_resolution_policy_falls_back_when_ranker_returns_none():
    payload = apply_anchor_resolution_policy(
        deterministic_result=_deterministic_result(match_stage='loose', selected=False),
        candidate_context=_candidate_context(),
        rank_decision=None,
    )

    assert payload is not None
    assert payload['selection']['source'] == 'deterministic_fallback'
    assert payload['selection']['decision'] == 'ambiguous'
    assert payload['selected'] is None
    assert len(payload['candidates']) == 2


def test_apply_anchor_resolution_policy_returns_none_when_no_inputs_available():
    payload = apply_anchor_resolution_policy(
        deterministic_result=None,
        candidate_context=None,
        rank_decision=None,
    )

    assert payload is None
