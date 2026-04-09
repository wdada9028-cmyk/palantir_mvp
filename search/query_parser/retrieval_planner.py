from __future__ import annotations

import logging

from .models import ParsedQuery, RetrievalPlan

logger = logging.getLogger(__name__)

_POLICY_MAP = {
    'impact_analysis': {
        'allowed_relations': ['DEPENDS_ON', 'CONSTRAINS', 'REFERENCES', 'APPLIES_TO', 'ASSIGNED_TO', 'ASSIGNS', 'EXECUTES'],
        'max_hop': 3,
        'answer_style': 'impact_chain',
        'ranking_policy': 'query_guided',
    },
    'relation_query': {
        'allowed_relations': ['HAS', 'CONTAINS', 'APPLIES_TO', 'DEFINES', 'GENERATES', 'REFERENCES', 'ASSIGNED_TO'],
        'max_hop': 2,
        'answer_style': 'triple_list',
        'ranking_policy': 'relation_first',
    },
    'process_query': {
        'allowed_relations': ['HAS', 'GENERATES', 'DEPENDS_ON', 'DEFINES', 'APPLIES_TO', 'CONTAINS', 'EXECUTES', 'ASSIGNS', 'OCCURS_IN', 'OCCURS_AT'],
        'max_hop': 3,
        'answer_style': 'ordered_steps',
        'ranking_policy': 'process_first',
    },
    'dependency_analysis': {
        'allowed_relations': ['DEPENDS_ON', 'DEFINES', 'GENERATES', 'USES', 'REFERENCES'],
        'max_hop': 2,
        'answer_style': 'dependency_tree',
        'ranking_policy': 'dependency_first',
    },
    'constraint_query': {
        'allowed_relations': ['CONSTRAINS', 'REFERENCES', 'DEPENDS_ON'],
        'max_hop': 3,
        'answer_style': 'constraint_chain',
        'ranking_policy': 'constraint_first',
    },
    'definition_query': {
        'allowed_relations': None,
        'max_hop': 1,
        'answer_style': 'definition',
        'ranking_policy': 'seed_first',
    },
    'listing_query': {
        'allowed_relations': ['HAS', 'CONTAINS', 'APPLIES_TO', 'ASSIGNED_TO', 'REFERENCES'],
        'max_hop': 2,
        'answer_style': 'entity_list',
        'ranking_policy': 'seed_first',
    },
}
_DEFAULT_POLICY = _POLICY_MAP['listing_query']


def merge_seed_entities(alias_entities: list[str], llm_entities: list[str] | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in [*alias_entities, *(llm_entities or [])]:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def build_retrieval_plan(parsed: ParsedQuery) -> RetrievalPlan:
    policy = _POLICY_MAP.get(parsed.intent.name, _DEFAULT_POLICY)
    debug_reason = [
        f'intent={parsed.intent.name}',
        f'matched_rules={parsed.intent.matched_rules}',
        f'ranking_policy={policy["ranking_policy"]}',
    ]
    plan = RetrievalPlan(
        seed_entities=list(parsed.canonical_entities),
        allowed_relations=list(policy['allowed_relations']) if policy['allowed_relations'] is not None else None,
        blocked_relations=None,
        max_hop=int(policy['max_hop']),
        answer_style=str(policy['answer_style']),
        ranking_policy=str(policy['ranking_policy']),
        debug_reason=debug_reason,
    )
    logger.debug('retrieval.plan', extra={'seed_entities': plan.seed_entities, 'allowed_relations': plan.allowed_relations, 'intent': parsed.intent.name})
    return plan
