# First-Wave Retrieval Optimizations Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve retrieval precision, answer focus, and repeated-query usability without changing the overall architecture.

**Architecture:** Keep the current chunk-first semantic retrieval flow, but tighten the highest-leverage stages: chunk generation, chunk-to-object linking, object/graph ranking, evidence budgeting, and artifact reuse for repeated `ask` calls. The work is intentionally incremental so each task can be shipped and verified independently.

**Tech Stack:** Python 3.11+, dataclasses, argparse, JSON artifacts, pytest, in-memory vector search, existing sample data and integration tests.

---

### Task 1: Make chunking actually honor size and overlap

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/ingestion/chunking.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/defaults.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/ingestion/test_chunking.py`

**Step 1: Write the failing test**

Add assertions covering all three behaviors in `tests/ingestion/test_chunking.py`:

```python
def test_chunk_document_splits_long_sections_with_overlap():
    content = '标题\n\n' + ('A' * 520)
    doc = SourceDocument(id='doc-1', title='sample', content=content, metadata={})

    chunks = chunk_document(doc, max_chars=200, overlap_chars=40)

    assert len(chunks) >= 3
    assert chunks[0].end_offset > chunks[1].start_offset
    assert chunks[1].start_offset < chunks[0].end_offset
    assert chunks[0].metadata['char_len'] <= 200
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ingestion/test_chunking.py -q`
Expected: FAIL because the current implementation only splits on blank lines and does not create overlap windows.

**Step 3: Write minimal implementation**

Implement two-stage chunking in `ingestion/chunking.py`:

```python
def chunk_document(document: SourceDocument, max_chars: int = 400, overlap_chars: int = 60) -> list[DocumentChunk]:
    sections = _split_sections(document.content)
    chunks: list[DocumentChunk] = []
    ordinal = 0
    for section_index, section in enumerate(sections):
        for window_index, (text, start, end, title) in enumerate(
            _window_section(document.content, section, max_chars=max_chars, overlap_chars=overlap_chars)
        ):
            chunks.append(
                DocumentChunk(
                    id=f'{document.id}-chunk-{ordinal}',
                    document_id=document.id,
                    ordinal=ordinal,
                    text=text,
                    start_offset=start,
                    end_offset=end,
                    embedding=None,
                    metadata={
                        'section_index': section_index,
                        'section_title': title,
                        'window_index': window_index,
                        'char_len': len(text),
                        'max_chars': max_chars,
                        'overlap_chars': overlap_chars,
                    },
                )
            )
            ordinal += 1
    return chunks
```

Set more realistic defaults in `defaults.py`:

```python
DEFAULT_CHUNK_SIZE = 400
DEFAULT_CHUNK_OVERLAP = 60
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ingestion/test_chunking.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add ingestion/chunking.py defaults.py tests/ingestion/test_chunking.py
git commit -m "feat: improve chunking granularity and overlap"
```

### Task 2: Make chunk-to-object linking score-aware and less noisy

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/ingestion/linking.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/ingestion/test_linking.py`

**Step 1: Write the failing test**

Add a focused test in `tests/ingestion/test_linking.py`:

```python
def test_link_chunks_to_objects_prefers_exact_name_and_deduplicates():
    chunk = DocumentChunk(
        id='c1', document_id='d1', ordinal=0,
        text='网络开通依赖账号权限审批完成。',
        start_offset=0, end_offset=14,
    )
    graph = OntologyGraph()
    graph.add_object(OntologyObject(id='T1', type='Task', name='网络开通', aliases=['网络准备']))
    graph.add_object(OntologyObject(id='C1', type='Constraint', name='账号权限审批', aliases=['审批']))

    links = link_chunks_to_objects([chunk], graph)

    assert {link.object_id for link in links} == {'T1', 'C1'}
    assert all(link.score >= 0.9 for link in links)
    assert len([link for link in links if link.object_id == 'C1']) == 1
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ingestion/test_linking.py -q`
Expected: FAIL because the current implementation emits flat score `1.0` links and does not record match quality or deduplicate by best match.

**Step 3: Write minimal implementation**

Refactor `link_chunks_to_objects()` so it:
- ignores very short aliases
- evaluates exact primary-name match, exact alias match, and boundary/token match separately
- keeps only the best match per `(chunk_id, object_id)`
- writes `match_type`, `matched_text`, and `matched_alias` into `metadata`

Use a helper like:

```python
def _score_match(haystack: str, obj: OntologyObject) -> tuple[float, dict[str, str]] | None:
    ...
```

and return links with differentiated scores such as `1.0`, `0.9`, `0.75`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ingestion/test_linking.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add ingestion/linking.py tests/ingestion/test_linking.py
git commit -m "feat: add score-aware chunk object linking"
```

### Task 3: Re-rank projected objects and cap graph expansion noise

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/search/projector.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/search/graph_expander.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/defaults.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/search/test_semantic_retriever.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/search/test_projector.py`

**Step 1: Write the failing tests**

Create `tests/search/test_projector.py`:

```python
def test_project_chunks_to_objects_accumulates_supporting_evidence():
    chunk_hits = [
        ChunkHit(chunk_id='c1', fused_score=0.8),
        ChunkHit(chunk_id='c2', fused_score=0.7),
    ]
    links = [
        ChunkObjectLink(chunk_id='c1', object_id='T1', link_type='mentions', score=1.0),
        ChunkObjectLink(chunk_id='c2', object_id='T1', link_type='mentions', score=0.9),
    ]
    graph = OntologyGraph(objects={'T1': OntologyObject(id='T1', type='Task', name='网络开通')})

    hits = project_chunks_to_objects(chunk_hits, links, graph, top_k=5)

    assert hits[0].object_id == 'T1'
    assert len(hits[0].supporting_chunk_ids) == 2
    assert hits[0].score > 0.8
```

Extend `tests/search/test_semantic_retriever.py` with a bound on expanded result size:

```python
assert len(result.object_hits) <= 10
assert len(result.relations) <= 12
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/search/test_projector.py tests/search/test_semantic_retriever.py -q`
Expected: FAIL because the projector currently uses max score only and graph expansion has no final cap.

**Step 3: Write minimal implementation**

In `search/projector.py`, replace the max-only rule with bounded accumulation:

```python
contribution = chunk_score * link.score
current.score = round(min(current.score + contribution * decay_factor, 1.5), 4)
```

In `search/graph_expander.py`, add:
- per-node expansion limit
- final object cap
- final relation cap

For example:

```python
MAX_EXPANDED_OBJECTS = 10
MAX_EXPANDED_RELATIONS = 12
MAX_RELATIONS_PER_OBJECT = 3
```

Apply those caps before returning.

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/search/test_projector.py tests/search/test_semantic_retriever.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add search/projector.py search/graph_expander.py defaults.py tests/search/test_projector.py tests/search/test_semantic_retriever.py
git commit -m "feat: tighten object ranking and graph expansion"
```

### Task 4: Limit the evidence budget sent to the answer prompt

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/answering/advisor.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/prompts.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/answering/test_advisor_resilience.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/integration/test_cli_reporting.py`

**Step 1: Write the failing tests**

Add a test that verifies the prompt-facing evidence is capped:

```python
def test_advice_engine_caps_prompt_evidence(monkeypatch):
    captured = {}

    class RecordingLLM:
        def answer_text(self, system_prompt, user_prompt):
            captured['prompt'] = user_prompt
            return 'ok'

    ...
    result = AdviceEngine(RecordingLLM()).answer(query='上线影响', artifacts=artifacts, retrieval_bundle=bundle)
    assert 'supporting_objects' in captured['prompt']
    assert captured['prompt'].count('object_id') <= 8
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/answering/test_advisor_resilience.py tests/integration/test_cli_reporting.py -q`
Expected: FAIL because all objects and relations are currently serialized into the prompt evidence.

**Step 3: Write minimal implementation**

In `answering/advisor.py`, keep the full return payload for debugging, but build a smaller prompt payload:

```python
prompt_evidence_bundle = {
    'intent': retrieval_bundle.intent,
    'retrieved_chunks': retrieved_chunks[:5],
    'supporting_objects': supporting_objects[:8],
    'citations': citations[:5],
    'relations': relations[:12],
}
```

Use `prompt_evidence_bundle` in `build_answer_prompt(...)`, while still returning the full `retrieved_chunks`, `supporting_objects`, `citations`, and `relations` in the API result.

In `prompts.py`, make the instruction explicit:

```python
system_prompt = (
    'You answer questions about cloud delivery scheduling and risks. '
    'Only use the provided top-ranked evidence. Do not infer unsupported relations. '
    'If evidence is missing, say so clearly.'
)
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/answering/test_advisor_resilience.py tests/integration/test_cli_reporting.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add answering/advisor.py prompts.py tests/answering/test_advisor_resilience.py tests/integration/test_cli_reporting.py
git commit -m "feat: cap llm evidence budget for answers"
```

### Task 5: Reuse built artifacts for repeated ask calls

**Files:**
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/pipeline.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/cli.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/integration/test_cli.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/pipelines/test_build_and_query_pipeline.py`

**Step 1: Write the failing tests**

Extend `tests/pipelines/test_build_and_query_pipeline.py`:

```python
def test_load_project_artifacts_rehydrates_vector_index(tmp_path):
    built = build_project_artifacts(...)
    write_project_artifacts(tmp_path, built['ontology'], built['schedule'], artifacts=built['artifacts'])

    loaded = load_project_artifacts(tmp_path)

    assert loaded.chunks
    assert loaded.vector_index is not None
    assert loaded.embedding_client is None
```

Extend `tests/integration/test_cli.py`:

```python
def test_cli_ask_can_use_existing_artifacts(tmp_path: Path):
    output_dir = tmp_path / 'output'
    assert main(['build', '--sample', '--output-dir', str(output_dir)]) == 0
    assert main(['ask', '账号权限审批会不会影响上线？', '--artifacts-dir', str(output_dir), '--sample']) == 0
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/pipelines/test_build_and_query_pipeline.py tests/integration/test_cli.py -q`
Expected: FAIL because there is no `load_project_artifacts()` yet and `ask` does not accept `--artifacts-dir`.

**Step 3: Write minimal implementation**

In `pipeline.py`, implement:

```python
def load_project_artifacts(output_dir: str | Path) -> ProjectArtifacts:
    ...
    for chunk in chunks:
        if chunk.embedding is not None:
            vector_index.add(chunk.id, chunk.embedding)
    return ProjectArtifacts(...)
```

In `cli.py`, add:

```python
ask_parser.add_argument('--artifacts-dir', type=str, help='Load existing build artifacts instead of rebuilding')
```

and branch ask execution so that `--artifacts-dir` loads artifacts first, only rebuilding if no artifact directory is provided.

**Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/pipelines/test_build_and_query_pipeline.py tests/integration/test_cli.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add pipeline.py cli.py tests/pipelines/test_build_and_query_pipeline.py tests/integration/test_cli.py
git commit -m "feat: reuse persisted artifacts for repeated queries"
```

### Task 6: Full regression verification before claiming completion

**Files:**
- No source changes expected
- Verify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir2/tests/...`

**Step 1: Run the targeted suite**

Run:
```bash
python -m pytest tests/ingestion/test_chunking.py tests/ingestion/test_linking.py tests/search/test_projector.py tests/search/test_semantic_retriever.py tests/answering/test_advisor_resilience.py tests/pipelines/test_build_and_query_pipeline.py tests/integration/test_cli.py tests/integration/test_cli_reporting.py -q
```
Expected: PASS.

**Step 2: Run the full suite**

Run:
```bash
python -m pytest -q
```
Expected: PASS.

**Step 3: Do a manual smoke test**

Run:
```bash
python -m cloud_delivery_ontology_palantir.cli build --sample --output-dir output_verify
python -m cloud_delivery_ontology_palantir.cli ask "账号权限审批会不会影响上线？" --artifacts-dir output_verify --sample
```
Expected: build writes artifacts successfully; ask returns a focused answer with shorter evidence.

**Step 4: Commit verification-only follow-up if needed**

```bash
git status
```
Expected: clean working tree, or only intentional doc/test updates.
