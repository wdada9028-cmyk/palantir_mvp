# Business Trustworthy Answer Summary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make non-attribute answer summaries business-trustworthy by removing impact-count templating from final summaries and having both LLM and fallback summarize concrete instance data and relations directly.

**Architecture:** Keep retrieval split unchanged: attribute questions remain anchor-only and other questions expand the graph. In the answer layer, stop using `impact_summary` as the final answer source; instead, feed the LLM stricter summary guidance and make fallback summarize concrete instances/links rather than counts.

**Tech Stack:** Python, OpenAI SDK, pytest

---

### Task 1: Lock the new summary contract with tests

**Files:**
- Modify: `tests/qa/test_template_answering.py`
- Modify: `tests/instance_qa/test_llm_answer_context_builder.py`

**Step 1: Write the failing tests**
- Add a test proving relation-style fallback answers enumerate concrete instance IDs instead of count-only impact text.
- Add a test proving impact-style fallback answers mention concrete instance IDs / statuses / milestone data instead of `?????X ?`.
- Add a test proving LLM answer prompt forbids count-only summaries and requires concrete instance IDs / attributes in the answer summary.

**Step 2: Run tests to verify they fail**

Run: `pytest tests/qa/test_template_answering.py tests/instance_qa/test_llm_answer_context_builder.py -q`
Expected: FAIL because current fallback still emits impact-count text and current prompt is too weak.

**Step 3: Write minimal implementation**
- Update `instance_qa/prompts.py` so answer-summary instructions require natural-language, business-trustworthy summaries with concrete instance IDs, statuses, times, and direct evidence-to-conclusion linkage, while forbidding count-only summaries and report-style section headings in the answer text.
- Update `qa/template_answering.py` so non-attribute fallbacks no longer use `impact_summary` counts as the primary summary output.
- Implement compact concrete-summary helpers that synthesize relation / impact / overview summaries from `fact_pack.instances`, `fact_pack.links`, anchor metadata, and important attributes.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/qa/test_template_answering.py tests/instance_qa/test_llm_answer_context_builder.py -q`
Expected: PASS

### Task 2: Run focused regression suite

**Files:**
- Verify only

**Step 1: Run focused regression tests**

Run: `pytest tests/qa/test_template_answering.py tests/instance_qa/test_llm_answer_context_builder.py tests/qa/test_generator.py tests/instance_qa/test_question_router.py -q`
Expected: PASS
