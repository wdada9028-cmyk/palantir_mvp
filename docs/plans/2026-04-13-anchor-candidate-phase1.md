# Anchor Candidate Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a phase-1 anchor candidate resolution layer before the router so ID/code/type/name style instance references can be matched more robustly without polluting the core `QuestionDSL` structure.

**Architecture:** Introduce a small pre-router anchor pipeline: normalize candidate phrases, build entity locator config, perform exact/light/loose candidate matching, and pass only an auxiliary resolution payload into the router prompt/orchestrator metadata. Keep `QuestionDSL` unchanged and avoid fallback-specific branching.

**Tech Stack:** Python, pytest

---

### Task 1: Add deterministic normalization utilities

**Files:**
- Create: `instance_qa/anchor_normalizer.py`
- Test: `tests/instance_qa/test_anchor_normalizer.py`

**Step 1: Write the failing tests**
- Add tests for exact/light/loose normalization behavior.
- Cover case changes, whitespace, dash changes, and token compaction.

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_anchor_normalizer.py -q`
Expected: FAIL because module does not exist yet.

**Step 3: Write minimal implementation**
- Add `normalize_anchor_text_light(...)`
- Add `normalize_anchor_text_loose(...)`
- Keep rules minimal and deterministic.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_anchor_normalizer.py -q`
Expected: PASS

### Task 2: Add locator registry and candidate resolver

**Files:**
- Create: `instance_qa/anchor_locator_registry.py`
- Create: `instance_qa/anchor_candidate_resolver.py`
- Test: `tests/instance_qa/test_anchor_candidate_resolver.py`

**Step 1: Write the failing tests**
- Add tests for:
  - exact raw match wins
  - light-normalized unique match wins
  - loose normalization returns multiple candidates instead of auto-selecting
  - lookup fields vary by entity config

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_anchor_candidate_resolver.py -q`
Expected: FAIL because registry/resolver do not exist yet.

**Step 3: Write minimal implementation**
- Add entity locator config for `PoD`, `Project`, `Room`
- Add candidate dataclasses/result dataclasses
- Add deterministic resolution pipeline: exact -> light -> loose candidates
- Do not invoke LLM in phase 1

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_anchor_candidate_resolver.py -q`
Expected: PASS

### Task 3: Integrate resolver into orchestrator/router without changing QuestionDSL

**Files:**
- Modify: `instance_qa/orchestrator.py`
- Modify: `instance_qa/question_router.py`
- Test: `tests/instance_qa/test_question_router.py`
- Test: `tests/integration/test_instance_qa_stream.py`

**Step 1: Write the failing tests**
- Add router prompt test proving anchor resolution payload is included when present.
- Add stream/integration test for `pod-001???????` resolving to `PoD / pod_id / POD-001` when candidate resolver provides a confident exact/light match.

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_router.py tests/integration/test_instance_qa_stream.py -q`
Expected: FAIL because orchestrator/router do not yet pass or consume anchor resolution payload.

**Step 3: Write minimal implementation**
- In orchestrator, resolve anchor candidates before router invocation.
- Pass an auxiliary `anchor_resolution_payload` into router prompt.
- Keep `QuestionDSL` unchanged.
- If resolver returns a single high-confidence exact/light match, let router see that context and prefer it.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_router.py tests/integration/test_instance_qa_stream.py -q`
Expected: PASS

### Task 4: Run focused regression suite

**Files:**
- Verify only

**Step 1: Run regression tests**

Run: `pytest tests/instance_qa/test_anchor_normalizer.py tests/instance_qa/test_anchor_candidate_resolver.py tests/instance_qa/test_question_router.py tests/integration/test_instance_qa_stream.py -q`
Expected: PASS
