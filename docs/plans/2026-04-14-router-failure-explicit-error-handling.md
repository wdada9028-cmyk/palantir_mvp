# Router Failure Explicit Error Handling Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** ? router ??????????????????????????????????????????????????????????????????

**Architecture:** ? router ????????? fallback?????????????????????????`question_router.py` ??????????`orchestrator.py` ? router ?????????????`llm_answer_context_builder.py` / `prompts.py` / `qa/template_answering.py` ???????????????`ontology_http_service.py` ? `graph_export.py` ???????????????

**Tech Stack:** Python, pytest, SSE stream payloads, current OpenAI-compatible client path

---

### Task 1: ? router ???????????

**Files:**
- Modify: `tests/instance_qa/test_question_router.py`
- Modify: `instance_qa/question_router.py`

**Step 1: Write the failing test**
- ???????
  - `resolve_question_route(...)` ????? `QuestionRoute | None`
  - ????????
    - `status`
    - `error_type`
    - `error_message`
    - `route`
  - ????? JSON?payload ??????????????

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_router.py -q`
Expected: FAIL because router currently collapses all failures into `None`.

**Step 3: Write minimal implementation**
- ?? `QuestionRouteResolution` dataclass
- ???????
  - `router_not_configured`
  - `router_timeout`
  - `router_connect_error`
  - `router_invalid_json`
  - `router_invalid_payload`
  - `router_validation_failed`
  - `router_unknown_error`
- ????? `route` ??

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_router.py -q`
Expected: PASS

### Task 2: ?? orchestrator?router ???????????

**Files:**
- Modify: `instance_qa/orchestrator.py`
- Modify: `tests/integration/test_instance_qa_stream.py`
- Modify: `tests/instance_qa/test_question_router.py` (if integration helper assertions need adjusting)

**Step 1: Write the failing test**
- ?????????
  - router ??????? fallback `QuestionDSL`
  - ??? fact query
  - ????? `Project`
  - ?????????????

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_instance_qa_stream.py -q`
Expected: FAIL because current orchestrator still falls back to base rule chain.

**Step 3: Write minimal implementation**
- `run_instance_qa(...)` ?? `QuestionRouteResolution`
- router ????
  - ?? `blocked_before_retrieval=True`
  - ?? router diagnostics
  - ?? fact query / reasoning ???
- ????? fallback ?? `Project`

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_instance_qa_stream.py -q`
Expected: PASS

### Task 3: ???????????????

**Files:**
- Modify: `tests/instance_qa/test_llm_answer_context_builder.py`
- Modify: `tests/qa/test_generator.py`
- Modify: `instance_qa/llm_answer_context_builder.py`
- Modify: `instance_qa/prompts.py`

**Step 1: Write the failing test**
- ???
  - ????? router failure diagnostics ??context builder ???????? user payload
  - prompt ??????????
    - ????
    - ????
    - ????
  - prompt ??????
    - ??????
    - ?????????????

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_llm_answer_context_builder.py tests/qa/test_generator.py -q`
Expected: FAIL because prompts currently assume a normal business-answer path.

**Step 3: Write minimal implementation**
- ? `prompts.py` ??????????
- ? `llm_answer_context_builder.py` ??? metadata ? router diagnostics ???????? payload
- ??????????????????????????

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_llm_answer_context_builder.py tests/qa/test_generator.py -q`
Expected: PASS

### Task 4: ?????? fallback answer builder

**Files:**
- Modify: `qa/template_answering.py`
- Modify: `tests/qa/test_template_answering.py`

**Step 1: Write the failing test**
- ???
  - router ??? `build_instance_template_answer(...)` ????????
  - ???????
    - ????
    - ????
    - ????
  - ??? `Project ???????` ??????

**Step 2: Run test to verify it fails**

Run: `pytest tests/qa/test_template_answering.py -q`
Expected: FAIL because template answer currently treats empty fact pack as evidence miss.

**Step 3: Write minimal implementation**
- ? template answering ????? router diagnostics
- ??? router failure?????? error answer ??

**Step 4: Run test to verify it passes**

Run: `pytest tests/qa/test_template_answering.py -q`
Expected: PASS

### Task 5: ??????? SSE ?????

**Files:**
- Modify: `server/ontology_http_service.py`
- Modify: `export/graph_export.py`
- Modify: `tests/integration/test_instance_qa_stream.py`
- Modify: `tests/integration/test_definition_graph_export.py`

**Step 1: Write the failing test**
- ???
  - SSE ? `answer_done` ???????? router diagnostics
  - ?? HTML ??????????
  - ??????????? schema retrieval ???????????

**Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`
Expected: FAIL because diagnostics are not yet surfaced end-to-end.

**Step 3: Write minimal implementation**
- SSE payload ?? `router_diagnostics`
- ?????/?????????????
- ???????????????????????????

**Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`
Expected: PASS

### Task 6: ?????

**Files:**
- Verify only

**Step 1: Run focused regression tests**

Run: `pytest tests/instance_qa/test_question_router.py tests/instance_qa/test_llm_answer_context_builder.py tests/qa/test_template_answering.py tests/qa/test_generator.py tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py -q`
Expected: PASS

**Step 2: Run broader regression tests**

Run: `pytest tests/instance_qa -q`
Expected: PASS

**Step 3: Optional final regression**

Run: `pytest tests/integration/test_instance_qa_stream.py tests/integration/test_definition_graph_export.py tests/qa -q`
Expected: PASS
