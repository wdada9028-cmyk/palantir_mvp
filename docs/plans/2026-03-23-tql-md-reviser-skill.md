# TQL MD Reviser Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** ???????? skill??? `tql + ?? md` ?????? `parse_definition_markdown()` ? `*.revised.md` ??????

**Architecture:** skill ???? `.agents/skills/tql-md-reviser/`?????????? markdown ???????? TQL ??????????????????????????? parser ???????? traceback ????????

**Tech Stack:** Python 3.11, pathlib, hashlib, argparse, regex, pytest

---

### Task 1: ?????? parser ?????? RED ??

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/tests/skills/test_tql_md_reviser.py`
- Test target: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/.agents/skills/tql-md-reviser/scripts/revise_tql_markdown.py`

**Step 1: Write the failing tests**

?????????
- ?? `md` ??????? hash ??
- ??????? hash ??
- ?? `tql + md` ??? `*.revised.md`
- `*.revised.md` ??? `parse_definition_markdown()`
- parser ?????????????

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/skills/test_tql_md_reviser.py -v
```
Expected: FAIL??? skill ??????????

**Step 3: Commit**

```bash
git add tests/skills/test_tql_md_reviser.py
git commit -m "test: cover tql md reviser skill"
```

### Task 2: ??? skill ???????

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/.agents/skills/tql-md-reviser/SKILL.md`
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/.agents/skills/tql-md-reviser/agents/openai.yaml`
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/.agents/skills/tql-md-reviser/references/parser-contract.md`

**Step 1: Write minimal SKILL.md**

???????
- ????
- ??????
- ????????
- ???? parser-contract
- ???????????????

**Step 2: Write parser-contract.md**

? `parse_definition_markdown()` ????????
- heading ??
- label ???
- property item ??
- relation item ??
- section ????
- backtick ????

**Step 3: Add openai.yaml**

?? UI metadata??? skill ????

**Step 4: Commit**

```bash
git add .agents/skills/tql-md-reviser/SKILL.md .agents/skills/tql-md-reviser/agents/openai.yaml .agents/skills/tql-md-reviser/references/parser-contract.md
git commit -m "feat: scaffold tql md reviser skill"
```

### Task 3: ?? revise_tql_markdown.py ???

**Files:**
- Create: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/.agents/skills/tql-md-reviser/scripts/revise_tql_markdown.py`
- Reuse: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/pipelines/tql_schema_extractor.py`
- Reuse: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/ontology/definition_markdown_parser.py`

**Step 1: Implement structure anchor generation**

???????? stable hash??????
- H2 path
- H3 object heading
- object name
- key property names
- relation triples

**Step 2: Implement revision context builder**

? `tql` ?? facts????? `md` ???????/??/???????????

**Step 3: Implement revised markdown writer**

???
- `current.revised.md`
- `current.revision-report.md`

??????????????

**Step 4: Implement parser traceback capture**

? `parse_definition_markdown()` ??????????
- exception type
- line number
- raw message

**Step 5: Implement minimal repair retry**

???????????????
- ????????/?
- ????????
- ?? 2 ?

**Step 6: Run tests to verify they pass**

Run:
```bash
pytest tests/skills/test_tql_md_reviser.py -v
```
Expected: PASS?

**Step 7: Commit**

```bash
git add .agents/skills/tql-md-reviser/scripts/revise_tql_markdown.py tests/skills/test_tql_md_reviser.py
git commit -m "feat: add tql md reviser script"
```

### Task 4: ??????

**Files:**
- Verify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/typedb_schema_v4.tql`
- Verify: `C:/Users/w00949875/.codex/worktrees/f742/palantir_mvp/[????] ????2?????v2.md`

**Step 1: Run skill script on real files**

Run:
```bash
python .agents/skills/tql-md-reviser/scripts/revise_tql_markdown.py --tql typedb_schema_v4.tql --markdown "[????] ????2?????v2.md"
```
Expected: ?? `.revised.md` ? `.revision-report.md`

**Step 2: Verify parser compatibility**

Run:
```bash
python -c "from pathlib import Path; from cloud_delivery_ontology_palantir.ontology.definition_markdown_parser import parse_definition_markdown; parse_definition_markdown(Path('...revised.md').read_text(encoding='utf-8'))"
```
Expected: PASS?

**Step 3: Run full verification**

Run:
```bash
pytest tests -q
```
Expected: PASS?

**Step 4: Commit**

?? Task 4 ??????/????????
