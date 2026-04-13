# Router OpenAI Client Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the router's raw httpx call path with the same OpenAI SDK client family used by the answer chain, while preserving router semantics.

**Architecture:** Keep the existing router prompt, JSON parsing, and QuestionRoute validation unchanged. Only swap the transport layer from manual httpx POST to a synchronous OpenAI client configured with retries and a longer timeout.

**Tech Stack:** Python, OpenAI SDK, pytest

---

### Task 1: Lock the desired router client behavior with tests

**Files:**
- Modify: `tests/instance_qa/test_question_router.py`
- Modify: `instance_qa/question_router.py`

**Step 1: Write the failing test**
- Add a test proving router client construction uses OpenAI SDK with `max_retries=2` and timeout `120.0`.
- Add a test proving `resolve_question_route(...)` calls the OpenAI client instead of raw httpx and still parses a valid route.

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_router.py -q`
Expected: FAIL because router still uses `get_http_client()` and 30 second timeout assumptions.

**Step 3: Write minimal implementation**
- Remove raw httpx POST transport usage from `instance_qa/question_router.py`.
- Add synchronous OpenAI client construction helper.
- Keep existing prompt/route parsing/validation logic.
- Raise default router timeout to `120.0`.

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_router.py -q`
Expected: PASS

**Step 5: Run focused regression suite**

Run: `pytest tests/instance_qa/test_question_router.py tests/instance_qa/test_llm_answer_context_builder.py tests/qa/test_generator.py -q`
Expected: PASS
