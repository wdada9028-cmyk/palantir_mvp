# Anchor Candidate Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** ??????????????????????????LLM ?????????????????????????? router?

**Architecture:** ???? `exact -> light -> loose` ??????????? `QuestionDSL` ?????? `candidate context builder` ?????????????? `anchor candidate ranker` ????????? `select / ambiguous / reject` ????? `resolution policy` ????????????? orchestrator ???????? `anchor_resolution_payload` ?? router?

**Tech Stack:** Python, pytest, OpenAI SDK-compatible client, current TypeDB read-only query path

---

### Task 1: ??????????????

**Files:**
- Create: `tests/instance_qa/test_anchor_candidate_context_builder.py`
- Reference: `instance_qa/anchor_candidate_resolver.py`
- Reference: `instance_qa/schema_registry.py`

**Step 1: Write the failing test**
- ???????
  - ???????? `iid`
  - `identity.primary_id` ? key attribute ????
  - `core_attributes` ?????????????
  - `business_context` ??? 1-hop ??????? `summary`
  - ???????????????

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_anchor_candidate_context_builder.py -q`
Expected: FAIL because builder module does not exist yet.

**Step 3: Write minimal implementation**
- ???? `PoD` / `Room` / `Project` ?????????????
- ?????????`locator / identity / core_attributes / business_context`

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_anchor_candidate_context_builder.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/instance_qa/test_anchor_candidate_context_builder.py
git commit -m "?????????????"
```

### Task 2: ?????????

**Files:**
- Create: `instance_qa/anchor_candidate_context_builder.py`
- Modify: `instance_qa/anchor_locator_registry.py`
- Modify: `instance_qa/schema_registry.py` (only if needed for light helper reuse; avoid schema shape changes)
- Test: `tests/instance_qa/test_anchor_candidate_context_builder.py`

**Step 1: Write the failing test**
- ? Task 1 ???????????
  - ??????? `*_status`
  - ???????????????
  - ???/??????? `*_model` / `*_name` / `*_code`

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_anchor_candidate_context_builder.py -q`
Expected: FAIL on missing builder logic.

**Step 3: Write minimal implementation**
- ?? `build_anchor_candidate_context(...)`
- ????????schema registry?candidate resolver ????????????? 1-hop ???
- ???
  - `raw_anchor_text`
  - `question`
  - `candidate_entity`
  - `candidates[]`
- ?? candidate ????
  - `candidate_id`
  - `entity`
  - `locator`
  - `identity`
  - `core_attributes`
  - `business_context`
- ?????
  - ??? `iid`
  - ???????
  - `business_context` ?? 2~4 ?

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_anchor_candidate_context_builder.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/anchor_candidate_context_builder.py instance_qa/anchor_locator_registry.py tests/instance_qa/test_anchor_candidate_context_builder.py
git commit -m "?????????"
```

### Task 3: ? LLM ?????????

**Files:**
- Create: `tests/instance_qa/test_anchor_candidate_ranker.py`
- Reference: `instance_qa/question_router.py`

**Step 1: Write the failing test**
- ???????
  - ranker prompt ???????schema markdown?candidate summary payload
  - ?? `select / ambiguous / reject`
  - ?????????? `QWEN_ANCHOR_RANKER_MODEL`
  - ?? OpenAI SDK ???
  - timeout / retries ? router ??

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_anchor_candidate_ranker.py -q`
Expected: FAIL because ranker module does not exist yet.

**Step 3: Write minimal implementation**
- ???? fake client ??
- ???? JSON-only ????

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_anchor_candidate_ranker.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/instance_qa/test_anchor_candidate_ranker.py
git commit -m "???????????"
```

### Task 4: ?? LLM ???

**Files:**
- Create: `instance_qa/anchor_candidate_ranker.py`
- Modify: `instance_qa/question_router.py` (???? client/config helper only if needed; avoid coupling ranker intent logic into router)
- Test: `tests/instance_qa/test_anchor_candidate_ranker.py`

**Step 1: Write the failing test**
- ???????????
  - ranker ?????????? N ?
  - ranker JSON ??????? `None`

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_anchor_candidate_ranker.py -q`
Expected: FAIL on missing implementation details.

**Step 3: Write minimal implementation**
- ?? `AnchorRankDecision` dataclass
- ?? `build_anchor_candidate_ranker_prompt(...)`
- ?? `resolve_anchor_candidate_rank(...)`
- ?????????
  - `QWEN_ANCHOR_RANKER_MODEL`
  - `QWEN_API_BASE`
  - `QWEN_API_KEY`
- ???????`Qwen3.5-35B-A3B`
- ????????
  - `decision`
  - `selected_candidate_id`
  - `confidence`
  - `reason`

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_anchor_candidate_ranker.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/anchor_candidate_ranker.py instance_qa/question_router.py tests/instance_qa/test_anchor_candidate_ranker.py
git commit -m "???????"
```

### Task 5: ??????????????

**Files:**
- Create: `tests/instance_qa/test_anchor_resolution_policy.py`

**Step 1: Write the failing test**
- ???
  - ??? `select` ????
  - ??? `select` ?????
  - ??? `select` ??? ambiguous
  - `reject` ???
  - `ambiguous` ???

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_anchor_resolution_policy.py -q`
Expected: FAIL because policy module does not exist yet.

**Step 3: Write minimal implementation**
- ????????
  - `>= 0.80` high
  - `0.60 - 0.79` medium
  - `< 0.60` low

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_anchor_resolution_policy.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/instance_qa/test_anchor_resolution_policy.py
git commit -m "??????????????"
```

### Task 6: ??????????

**Files:**
- Create: `instance_qa/anchor_resolution_policy.py`
- Test: `tests/instance_qa/test_anchor_resolution_policy.py`

**Step 1: Write the failing test**
- ????????
  - ? deterministic ?? exact/light ??????????? ranker
  - ? ranker ?? `None` ??policy ???? deterministic payload ?? payload

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_anchor_resolution_policy.py -q`
Expected: FAIL on missing integration logic.

**Step 3: Write minimal implementation**
- ?? `apply_anchor_resolution_policy(...)`
- ???deterministic result?candidate summary?rank decision
- ?????? `anchor_resolution_payload`
- ???? router ?????????
  - `raw_anchor_text`
  - `match_stage`
  - `selection`
  - `selected`
  - `candidates`

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_anchor_resolution_policy.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/anchor_resolution_policy.py tests/instance_qa/test_anchor_resolution_policy.py
git commit -m "???????????"
```

### Task 7: ?? orchestrator ???

**Files:**
- Modify: `instance_qa/orchestrator.py`
- Modify: `instance_qa/anchor_candidate_resolver.py` (only if result shape needs a small helper)
- Test: `tests/integration/test_instance_qa_stream.py`
- Test: `tests/instance_qa/test_question_router.py`

**Step 1: Write the failing test**
- ?????????
  - ???? orchestrator ??? candidate summary ??? ranker
  - ranker ??? select ??router ??? `selection` ? payload
  - ambiguous ? router ?????????
  - exact/light ???????? ranker

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_router.py tests/integration/test_instance_qa_stream.py -q`
Expected: FAIL because orchestrator does not yet orchestrate summary + rank + policy.

**Step 3: Write minimal implementation**
- ? `_resolve_anchor_resolution_payload(...)` ??????????
  - deterministic recall
  - candidate summary build
  - conditional ranker call
  - policy apply
- ?? `QuestionDSL` ??
- ????? fact query / reasoning ????

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_router.py tests/integration/test_instance_qa_stream.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/orchestrator.py instance_qa/anchor_candidate_resolver.py tests/instance_qa/test_question_router.py tests/integration/test_instance_qa_stream.py
git commit -m "?????????????"
```

### Task 8: ?? router ???????? selection payload

**Files:**
- Modify: `instance_qa/question_router.py`
- Test: `tests/instance_qa/test_question_router.py`

**Step 1: Write the failing test**
- ?? router prompt ???
  - ? `selection.decision=select` ??????prompt ???????? selected
  - ? `selection.decision=ambiguous` ??prompt ????????

**Step 2: Run test to verify it fails**

Run: `pytest tests/instance_qa/test_question_router.py -q`
Expected: FAIL because prompt constraints are not updated yet.

**Step 3: Write minimal implementation**
- ? prompt ????
  - `selection` ????
  - ???????
  - ???????
- ?????????????????? prompt ?????

**Step 4: Run test to verify it passes**

Run: `pytest tests/instance_qa/test_question_router.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add instance_qa/question_router.py tests/instance_qa/test_question_router.py
git commit -m "???????????????"
```

### Task 9: ???????????

**Files:**
- Modify: `docs/plans/2026-04-14-anchor-candidate-phase2.md` (append verification notes only if useful)
- Verify only

**Step 1: Run focused regression tests**

Run: `pytest tests/instance_qa/test_anchor_normalizer.py tests/instance_qa/test_anchor_candidate_resolver.py tests/instance_qa/test_anchor_candidate_context_builder.py tests/instance_qa/test_anchor_candidate_ranker.py tests/instance_qa/test_anchor_resolution_policy.py tests/instance_qa/test_question_router.py tests/integration/test_instance_qa_stream.py -q`
Expected: PASS

**Step 2: Run broader regression tests**

Run: `pytest tests/instance_qa -q`
Expected: PASS

**Step 3: Record final notes**
- ???
  - ?????? `Qwen3.5-35B-A3B`
  - ???? ranker
  - ???? ambiguous

**Step 4: Commit**

```bash
git add docs/plans/2026-04-14-anchor-candidate-phase2.md
git commit -m "????????????????"
```
