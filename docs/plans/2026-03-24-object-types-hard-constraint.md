# Object Types Hard-Constraint Renderer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make TQL-to-markdown generation produce hard-constrained Object Types output with fixed top-level headings, no implicit grouping, deterministic Chinese labels/attribute glosses, and optional explicit grouping metadata support.

**Architecture:** Move Object Types generation to a deterministic renderer path instead of relying on LLM wording. Extend TQL extraction models so entity/attribute metadata can carry optional structured comment directives (`group`, `zh`, `semantic`). Keep parser backward compatible with both legacy markdown and the new compact format. Skip Object Types enhancement in the runtime enhancer so hard constraints remain intact.

**Tech Stack:** Python, existing TQL extractor/renderer/parser pipeline, pytest.

---

### Task 1: Lock the new markdown contract with failing tests

**Files:**
- Modify: `tests/pipelines/test_input_file_resolver.py`
- Modify: `tests/ontology/test_definition_markdown_parser.py`
- Test: `tests/pipelines/test_input_file_resolver.py`
- Test: `tests/ontology/test_definition_markdown_parser.py`

**Step 1: Write the failing tests**
- Add a renderer/integration expectation that `.tql -> .converted.md` uses:
  - `# <tql stem>`
  - `## Object Types????`
  - `## Link Types????`
- Add expectations that default entity output is flat under Object Types, with no synthetic category headings.
- Add expectations that object descriptions/semantic/attribute lines obey the new strict format.
- Add a parser test proving the new markdown format parses successfully.

**Step 2: Run tests to verify they fail**
Run: `pytest tests/pipelines/test_input_file_resolver.py tests/ontology/test_definition_markdown_parser.py -q`
Expected: FAIL on old heading/group/field format.

### Task 2: Extend extracted schema metadata for future explicit grouping/labels

**Files:**
- Modify: `pipelines/tql_schema_models.py`
- Modify: `pipelines/tql_schema_extractor.py`
- Test: `tests/pipelines/test_input_file_resolver.py`

**Step 1: Add metadata fields**
- Add optional structured metadata fields to entity/attribute specs:
  - entity: `group_label`, `zh_label`, `semantic_definition`
  - attribute: `zh_label`
- Keep defaults empty so old callers still work.

**Step 2: Parse structured comment directives minimally**
- Support immediately preceding comment directives:
  - `# group: <...>`
  - `# zh: <...>`
  - `# semantic: <...>`
- Attribute-level `# zh:` applies to the next attribute declaration.
- Entity-level directives apply to the next entity declaration.
- If parent is abstract, allow that parent to act as explicit group metadata.

**Step 3: Run focused tests**
Run: `pytest tests/pipelines/test_input_file_resolver.py -q`
Expected: PASS once extraction remains stable.

### Task 3: Rebuild the renderer for deterministic Object Types output

**Files:**
- Modify: `pipelines/tql_schema_renderer.py`
- Test: `tests/pipelines/test_input_file_resolver.py`

**Step 1: Implement fixed headings**
- H1 becomes source stem/title-safe value, e.g. `typedb_schema_v4`.
- H2 headings become exactly:
  - `## Object Types????`
  - `## Link Types????`

**Step 2: Render Object Types deterministically**
- No synthetic grouping by default.
- If explicit group metadata exists, render grouped output only then.
- For flat mode, render entities directly in source order.
- Chinese description:
  - explicit TQL metadata first
  - otherwise deterministic business-aware translation
- Semantic definition:
  - explicit TQL metadata only
  - otherwise omit the section
- Key properties format exactly:
  - `- `english_name`???`

**Step 3: Keep relation rendering compatible**
- Preserve existing relation triples and parser compatibility.

**Step 4: Run focused tests**
Run: `pytest tests/pipelines/test_input_file_resolver.py -q`
Expected: PASS.

### Task 4: Make parser and enhancer compatible with the new format

**Files:**
- Modify: `ontology/definition_markdown_parser.py`
- Modify: `pipelines/tql_markdown_enhancer.py`
- Test: `tests/ontology/test_definition_markdown_parser.py`
- Test: `tests/pipelines/test_tql_markdown_enhancer.py`

**Step 1: Parser compatibility**
- Accept both legacy headings and new headings.
- Accept flat Object Types format.
- Accept optional explicit groups without breaking legacy parsing.

**Step 2: Preserve hard constraints at runtime**
- Disable Object Types enhancement or project it back so object structure/content rules cannot be broken.
- Keep Link Types enhancement path working.

**Step 3: Run focused tests**
Run: `pytest tests/ontology/test_definition_markdown_parser.py tests/pipelines/test_tql_markdown_enhancer.py -q`
Expected: PASS.

### Task 5: Verify end-to-end conversion and service behavior

**Files:**
- Modify: `typedb_schema_v4.converted.md` (generated artifact)
- Test: `tests/pipelines/test_input_file_resolver.py`
- Test: `tests/integration/test_build_ontology_cli.py`
- Test: `tests/server/test_ontology_http_app.py`

**Step 1: Run regression suite**
Run: `pytest tests/pipelines/test_input_file_resolver.py tests/integration/test_build_ontology_cli.py tests/server/test_ontology_http_app.py -q`
Expected: PASS.

**Step 2: Run full suite**
Run: `pytest tests -q`
Expected: PASS.

**Step 3: Real conversion check**
Run a real `typedb_schema_v4.tql -> typedb_schema_v4.converted.md` conversion and inspect the Object Types section.

**Step 4: Service smoke**
Start `serve-ontology` with the `.tql` input and verify `/api/graph` returns `200`.
