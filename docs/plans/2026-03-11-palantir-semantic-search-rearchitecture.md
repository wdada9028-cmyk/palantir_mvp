# Palantir-Style Ontology Semantic Search Re-architecture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild the current project so retrieval is document-chunk-first semantic search projected into ontology objects, matching the Palantir ontology semantic search pattern instead of direct node-name lexical retrieval.

**Architecture:** Convert the current flat ontology-only pipeline into a layered system with document ingestion, chunking, chunk embeddings, in-memory vector search, chunk-to-object linking, ontology graph expansion, and citation-backed answering. Keep scheduling and graph export as downstream consumers of the ontology object graph, but make chunk KNN retrieval the only primary recall path.

**Tech Stack:** Python 3.11+, dataclasses, argparse, JSON artifacts, OpenAI-compatible chat/embedding APIs, `pytest`, pure-Python cosine similarity, weighted fusion / RRF, and the existing sample delivery dataset.

---

**Execution notes**
- Use `@superpowers/test-driven-development` for every task.
- If any step fails unexpectedly, use `@superpowers/systematic-debugging` before changing code.
- Before claiming the rewrite is done, use `@superpowers/verification-before-completion`.
- Git commands below assume the workspace has been moved into a git-enabled worktree; if it is still outside git, skip only the commit command.

**Acceptance criteria**
- `ask`-style queries search chunks, not ontology object names.
- Every answer includes retrieved chunks, projected ontology objects, and citations.
- Ontology graph expansion happens after chunk retrieval/projector, not before.
- Build artifacts persist document/chunk/link/index metadata alongside ontology/schedule outputs.
- The sample data end-to-end flow still works.

### Task 1: Create the new package skeleton and test harness

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/models/__init__.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ingestion/__init__.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ontology/__init__.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/__init__.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/planning/__init__.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/answering/__init__.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/pipelines/__init__.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/export/__init__.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/conftest.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/test_package_layout.py`

**Step 1: Write the failing test**

```python
from importlib import import_module


def test_new_subpackages_import():
    assert import_module('cloud_delivery_ontology_palantir.models')
    assert import_module('cloud_delivery_ontology_palantir.ingestion')
    assert import_module('cloud_delivery_ontology_palantir.search')
    assert import_module('cloud_delivery_ontology_palantir.pipelines')
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_package_layout.py -q`
Expected: FAIL with `ModuleNotFoundError` for at least one new subpackage import.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/conftest.py
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
PACKAGE_PARENT = WORKSPACE.parent
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))
```

Also create the eight `__init__.py` files listed above as empty files so the imports resolve.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_package_layout.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/test_package_layout.py tests/conftest.py models/__init__.py ingestion/__init__.py ontology/__init__.py search/__init__.py planning/__init__.py answering/__init__.py pipelines/__init__.py export/__init__.py
git commit -m "test: add package skeleton for palantir-style search rewrite"
```

### Task 2: Split shared models and keep a compatibility shim

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/models/documents.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/models/ontology.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/models/retrieval.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/models/schedule.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/models/runtime.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/schema.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/models/test_models_roundtrip.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.models.documents import SourceDocument, DocumentChunk, ChunkObjectLink
from cloud_delivery_ontology_palantir.models.ontology import OntologyObject, OntologyRelation, OntologyGraph
from cloud_delivery_ontology_palantir.schema import OntologyGraph as LegacyOntologyGraph


def test_models_round_trip_and_legacy_shim():
    doc = SourceDocument(id='doc-1', title='????', content='?????', metadata={'source': 'unit'})
    chunk = DocumentChunk(
        id='chunk-1',
        document_id='doc-1',
        ordinal=0,
        text='?????',
        start_offset=0,
        end_offset=5,
        embedding=[0.1, 0.2],
        metadata={'section': '??'},
    )
    link = ChunkObjectLink(chunk_id='chunk-1', object_id='T1', link_type='mentions', score=1.0)
    graph = OntologyGraph()
    graph.add_object(OntologyObject(id='T1', type='Task', name='????'))
    graph.add_relation(OntologyRelation(source_id='T1', target_id='M1', relation='targets_milestone'))
    assert doc.to_dict()['title'] == '????'
    assert chunk.to_dict()['embedding'] == [0.1, 0.2]
    assert link.to_dict()['object_id'] == 'T1'
    assert isinstance(LegacyOntologyGraph(), OntologyGraph)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/models/test_models_roundtrip.py -q`
Expected: FAIL with import errors because the new model modules do not exist yet.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/models/documents.py
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SourceDocument:
    id: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {'id': self.id, 'title': self.title, 'content': self.content, 'metadata': dict(self.metadata)}
```

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/schema.py
from .models.documents import *  # noqa: F401,F403
from .models.ontology import *  # noqa: F401,F403
from .models.retrieval import *  # noqa: F401,F403
from .models.schedule import *  # noqa: F401,F403
from .models.runtime import *  # noqa: F401,F403
```

Implement the remaining dataclasses in the new `models` files with `to_dict()` helpers and `OntologyGraph.add_object() / add_relation()` methods.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/models/test_models_roundtrip.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add models/documents.py models/ontology.py models/retrieval.py models/schedule.py models/runtime.py schema.py tests/models/test_models_roundtrip.py
git commit -m "feat: split shared models for chunk-first search architecture"
```

### Task 3: Implement document ingestion and chunking

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ingestion/documents.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ingestion/chunking.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/ingestion/test_chunking.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.ingestion.chunking import chunk_document
from cloud_delivery_ontology_palantir.models.documents import SourceDocument


def test_chunk_document_preserves_offsets_and_order():
    doc = SourceDocument(id='doc-1', title='????', content='????

????', metadata={})
    chunks = chunk_document(doc, max_chars=6, overlap_chars=0)
    assert [chunk.ordinal for chunk in chunks] == [0, 1]
    assert chunks[0].text == '????'
    assert doc.content[chunks[1].start_offset:chunks[1].end_offset] == '????'
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ingestion/test_chunking.py -q`
Expected: FAIL with `ImportError` or `NameError` for `chunk_document`.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ingestion/chunking.py
from cloud_delivery_ontology_palantir.models.documents import DocumentChunk, SourceDocument


def chunk_document(document: SourceDocument, max_chars: int = 800, overlap_chars: int = 80) -> list[DocumentChunk]:
    pieces = [part for part in document.content.split('

') if part.strip()]
    chunks: list[DocumentChunk] = []
    cursor = 0
    for ordinal, piece in enumerate(pieces):
        start = document.content.index(piece, cursor)
        end = start + len(piece)
        chunks.append(
            DocumentChunk(
                id=f'{document.id}-chunk-{ordinal}',
                document_id=document.id,
                ordinal=ordinal,
                text=piece,
                start_offset=start,
                end_offset=end,
                embedding=None,
                metadata={},
            )
        )
        cursor = end
    return chunks
```

Add `ingestion/documents.py` helpers to build `SourceDocument` objects from raw text and optional metadata.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ingestion/test_chunking.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add ingestion/documents.py ingestion/chunking.py tests/ingestion/test_chunking.py
git commit -m "feat: add source document and chunking pipeline"
```

### Task 4: Refactor ontology extraction and object graph building

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ingestion/extraction.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ontology/registry.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ontology/mapper.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ontology/builder.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/extractor.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ontology.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ontology_mapper.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ontology_registry.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/ontology/test_builder.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.ingestion.extraction import normalize_extraction_payload
from cloud_delivery_ontology_palantir.ontology.builder import OntologyBuilder
from cloud_delivery_ontology_palantir.sample_data import SAMPLE_EXTRACTION_PAYLOAD


def test_builder_creates_task_and_risk_objects_from_sample_payload():
    payload = normalize_extraction_payload(SAMPLE_EXTRACTION_PAYLOAD)
    graph = OntologyBuilder().build_from_extraction(payload)
    task_names = {obj.name for obj in graph.objects.values() if obj.type == 'Task'}
    relations = {(rel.source_id, rel.relation, rel.target_id) for rel in graph.relations}
    assert '????' in task_names
    assert any(rel[1] == 'has_risk' for rel in relations)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ontology/test_builder.py -q`
Expected: FAIL because the new builder modules do not exist yet.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ontology/builder.py
from cloud_delivery_ontology_palantir.ingestion.extraction import normalize_extraction_payload
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation


class OntologyBuilder:
    def build_from_extraction(self, payload: dict, source_id: str = 'delivery-instruction') -> OntologyGraph:
        data = normalize_extraction_payload(payload)
        graph = OntologyGraph()
        # Port the current node/edge creation logic here, but emit OntologyObject/OntologyRelation.
        return graph
```

Move the current registry, mapper, and normalization logic into the new package modules. Keep the four existing root-level modules as one-line wrappers that import from the new locations until CLI and pipelines are migrated.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ontology/test_builder.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add ingestion/extraction.py ontology/registry.py ontology/mapper.py ontology/builder.py extractor.py ontology.py ontology_mapper.py ontology_registry.py tests/ontology/test_builder.py
git commit -m "feat: move ontology extraction and building into layered packages"
```

### Task 5: Implement chunk-to-object linking

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ingestion/linking.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/ingestion/test_linking.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.ingestion.chunking import chunk_document
from cloud_delivery_ontology_palantir.ingestion.linking import link_chunks_to_objects
from cloud_delivery_ontology_palantir.models.documents import SourceDocument
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject


def test_link_chunks_to_objects_matches_names_and_aliases():
    document = SourceDocument(id='doc-1', title='????', content='?????????????', metadata={})
    chunks = chunk_document(document, max_chars=20, overlap_chars=0)
    graph = OntologyGraph()
    graph.add_object(OntologyObject(id='T1', type='Task', name='????', aliases=['????']))
    graph.add_object(OntologyObject(id='C1', type='Constraint', name='??????', aliases=['????']))
    links = link_chunks_to_objects(chunks, graph)
    assert {(link.chunk_id, link.object_id) for link in links} == {(chunks[0].id, 'T1'), (chunks[0].id, 'C1')}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ingestion/test_linking.py -q`
Expected: FAIL because `link_chunks_to_objects` does not exist yet.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/ingestion/linking.py
from cloud_delivery_ontology_palantir.models.documents import ChunkObjectLink, DocumentChunk
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph


def link_chunks_to_objects(chunks: list[DocumentChunk], graph: OntologyGraph) -> list[ChunkObjectLink]:
    links: list[ChunkObjectLink] = []
    for chunk in chunks:
        haystack = chunk.text.casefold()
        for obj in graph.objects.values():
            names = {obj.name, *(obj.aliases or [])}
            if any(name.casefold() in haystack for name in names if name):
                links.append(ChunkObjectLink(chunk_id=chunk.id, object_id=obj.id, link_type='mentions', score=1.0))
    return links
```

Keep the first version purely rule-based. Do not add LLM-assisted link inference until the rule-based path is stable and tested.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ingestion/test_linking.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add ingestion/linking.py tests/ingestion/test_linking.py
git commit -m "feat: add chunk to ontology object linking"
```

### Task 6: Implement embeddings and the in-memory vector index

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/embeddings.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/vector_index.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/defaults.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/search/test_vector_index.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.search.vector_index import InMemoryVectorIndex


def test_vector_index_returns_nearest_chunk_ids():
    index = InMemoryVectorIndex()
    index.add('doc-1-chunk-0', [1.0, 0.0])
    index.add('doc-1-chunk-1', [0.0, 1.0])
    hits = index.search([0.9, 0.1], top_k=1)
    assert hits[0].item_id == 'doc-1-chunk-0'
    assert hits[0].score > 0.9
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/search/test_vector_index.py -q`
Expected: FAIL because `InMemoryVectorIndex` does not exist yet.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/vector_index.py
from dataclasses import dataclass
from math import sqrt


@dataclass(slots=True)
class VectorHit:
    item_id: str
    score: float


class InMemoryVectorIndex:
    def __init__(self) -> None:
        self._vectors: dict[str, list[float]] = {}

    def add(self, item_id: str, vector: list[float]) -> None:
        self._vectors[item_id] = vector

    def search(self, query_vector: list[float], top_k: int = 5) -> list[VectorHit]:
        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            na = sqrt(sum(x * x for x in a)) or 1.0
            nb = sqrt(sum(y * y for y in b)) or 1.0
            return dot / (na * nb)
        hits = [VectorHit(item_id=item_id, score=cosine(query_vector, vector)) for item_id, vector in self._vectors.items()]
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:top_k]
```

Add `search/embeddings.py` with `EmbeddingClient` protocol, `FakeEmbeddingClient`, and `OpenAICompatibleEmbeddingClient`. Extend `defaults.py` with chunking and retrieval constants such as `DEFAULT_CHUNK_SIZE`, `DEFAULT_CHUNK_OVERLAP`, and `DEFAULT_SEMANTIC_TOP_K`.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/search/test_vector_index.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add search/embeddings.py search/vector_index.py defaults.py tests/search/test_vector_index.py
git commit -m "feat: add embedding client abstraction and vector index"
```

### Task 7: Implement chunk-first semantic retrieval, fusion, projection, and graph expansion

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/lexical_index.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/hybrid_fusion.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/projector.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/graph_expander.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/semantic_retriever.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/retriever.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/search/test_semantic_retriever.py`

**Step 1: Write the failing test**

```python
from cloud_delivery_ontology_palantir.models.documents import SourceDocument
from cloud_delivery_ontology_palantir.pipelines.build_pipeline import build_project_artifacts
from cloud_delivery_ontology_palantir.sample_data import SAMPLE_EXTRACTION_PAYLOAD, SAMPLE_DELIVERY_TEXT
from cloud_delivery_ontology_palantir.search.embeddings import FakeEmbeddingClient
from cloud_delivery_ontology_palantir.search.semantic_retriever import SemanticRetriever


def test_semantic_retriever_returns_chunk_hits_then_object_hits():
    artifacts = build_project_artifacts(
        documents=[SourceDocument(id='doc-1', title='sample', content=SAMPLE_DELIVERY_TEXT, metadata={})],
        extraction_payload=SAMPLE_EXTRACTION_PAYLOAD,
        embedding_client=FakeEmbeddingClient(),
        project_start_date='2026-03-10',
    )
    result = SemanticRetriever().retrieve('??????????????', artifacts, top_k=3)
    assert result.chunk_hits
    assert result.object_hits
    assert result.citations
    assert result.object_hits[0].supporting_chunk_ids
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/search/test_semantic_retriever.py -q`
Expected: FAIL because the retriever stack does not yet exist.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/search/semantic_retriever.py
class SemanticRetriever:
    def retrieve(self, query: str, artifacts, top_k: int = 5):
        # 1. Embed query
        # 2. Search chunk vector index
        # 3. Optionally run lexical chunk search
        # 4. Fuse chunk scores
        # 5. Project chunks to ontology objects via ChunkObjectLink
        # 6. Expand ontology graph using intent-aware relations
        # 7. Return RetrievalBundle with chunk_hits, object_hits, citations, and relations
        return ...
```

`retriever.py` should become a wrapper that imports and re-exports `SemanticRetriever`, or be deleted only after all imports are migrated. Do not keep the current node-name lexical retriever as the primary execution path.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/search/test_semantic_retriever.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add search/lexical_index.py search/hybrid_fusion.py search/projector.py search/graph_expander.py search/semantic_retriever.py retriever.py tests/search/test_semantic_retriever.py
git commit -m "feat: replace node lexical retrieval with chunk-first semantic retrieval"
```

### Task 8: Rewrite the build/query pipelines and move scheduling downstream of ontology objects

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/planning/scheduler.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/pipelines/build_pipeline.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/pipelines/query_pipeline.py`
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/answering/advisor.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/scheduler.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/pipeline.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/advisor.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/prompts.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/pipelines/test_build_pipeline.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/pipelines/test_query_pipeline.py`

**Step 1: Write the failing tests**

```python
from cloud_delivery_ontology_palantir.models.documents import SourceDocument
from cloud_delivery_ontology_palantir.pipelines.build_pipeline import build_project_artifacts
from cloud_delivery_ontology_palantir.pipelines.query_pipeline import answer_query
from cloud_delivery_ontology_palantir.sample_data import SAMPLE_EXTRACTION_PAYLOAD, SAMPLE_DELIVERY_TEXT
from cloud_delivery_ontology_palantir.search.embeddings import FakeEmbeddingClient


def test_build_pipeline_emits_documents_chunks_links_and_schedule():
    artifacts = build_project_artifacts(
        documents=[SourceDocument(id='doc-1', title='sample', content=SAMPLE_DELIVERY_TEXT, metadata={})],
        extraction_payload=SAMPLE_EXTRACTION_PAYLOAD,
        embedding_client=FakeEmbeddingClient(),
        project_start_date='2026-03-10',
    )
    assert artifacts.documents
    assert artifacts.chunks
    assert artifacts.chunk_links
    assert artifacts.vector_index is not None
    assert artifacts.schedule.project_end_date == '2026-03-22'


def test_query_pipeline_returns_citation_backed_answer():
    artifacts = build_project_artifacts(
        documents=[SourceDocument(id='doc-1', title='sample', content=SAMPLE_DELIVERY_TEXT, metadata={})],
        extraction_payload=SAMPLE_EXTRACTION_PAYLOAD,
        embedding_client=FakeEmbeddingClient(),
        project_start_date='2026-03-10',
    )
    result = answer_query('??????????????', artifacts, llm_client=None)
    assert result['retrieved_chunks']
    assert result['supporting_objects']
    assert result['citations']
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/pipelines/test_build_pipeline.py tests/pipelines/test_query_pipeline.py -q`
Expected: FAIL because the new pipelines do not exist yet.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/pipelines/build_pipeline.py
from cloud_delivery_ontology_palantir.ingestion.chunking import chunk_document
from cloud_delivery_ontology_palantir.ingestion.linking import link_chunks_to_objects
from cloud_delivery_ontology_palantir.ontology.builder import OntologyBuilder
from cloud_delivery_ontology_palantir.planning.scheduler import Scheduler


def build_project_artifacts(documents, extraction_payload, embedding_client, project_start_date='2026-03-10'):
    # Build SourceDocument -> chunks -> ontology graph -> chunk links -> embeddings -> vector index -> schedule.
    return ...
```

Refactor the root-level `pipeline.py`, `scheduler.py`, and `advisor.py` into shims that call the new package implementations. Update `prompts.py` so the answer prompt can include citations and chunk text.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/pipelines/test_build_pipeline.py tests/pipelines/test_query_pipeline.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add planning/scheduler.py pipelines/build_pipeline.py pipelines/query_pipeline.py answering/advisor.py scheduler.py pipeline.py advisor.py prompts.py tests/pipelines/test_build_pipeline.py tests/pipelines/test_query_pipeline.py
git commit -m "feat: wire chunk-first retrieval into build and query pipelines"
```

### Task 9: Migrate the CLI, artifact writing, and public exports; then run full verification

**Files:**
- Create: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/export/graph_export.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/graph_export.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/cli.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/__init__.py`
- Modify: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/sample_data.py`
- Test: `D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/tests/integration/test_cli.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

from cloud_delivery_ontology_palantir.cli import main


def test_cli_build_and_ask_with_sample(tmp_path: Path):
    output_dir = tmp_path / 'output'
    assert main(['build', '--sample', '--output-dir', str(output_dir)]) == 0
    assert (output_dir / 'ontology.json').exists()
    assert (output_dir / 'chunks.json').exists()
    assert main(['ask', '??????????????', '--sample']) == 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/test_cli.py -q`
Expected: FAIL because the CLI still uses the old flat pipeline and does not emit chunk artifacts.

**Step 3: Write minimal implementation**

```python
# D:/学习资料/AI应用使能组/本体检索代码/cloud_delivery_ontology_palantir/cli.py
# Update the build command to write:
# - ontology.json
# - schedule.json
# - schedule.csv
# - documents.json
# - chunks.json
# - chunk_links.json
# - semantic_index_manifest.json
# Update the ask command to call the new query pipeline and print citation-backed answers.
```

Move the export helpers into `export/graph_export.py`, leave `graph_export.py` as a wrapper during the migration, and update `__init__.py` to export the new pipeline entry points.

**Step 4: Run test to verify it passes and then run the full suite**

Run: `python -m pytest tests/integration/test_cli.py -q`
Expected: PASS.

Run: `python -m pytest tests -q`
Expected: PASS.

Run: `python -m cloud_delivery_ontology_palantir.cli build --sample --output-dir output`
Expected: exit code `0` and files `output/ontology.json`, `output/chunks.json`, and `output/chunk_links.json` created.

Run: `python -m cloud_delivery_ontology_palantir.cli ask "??????????????" --sample`
Expected: exit code `0` and a citation-backed answer printed to stdout.

**Step 5: Commit**

```bash
git add export/graph_export.py graph_export.py cli.py __init__.py sample_data.py tests/integration/test_cli.py
git commit -m "feat: expose palantir-style semantic search through cli and public api"
```

### Final cleanup notes
- After Task 9 passes, remove any legacy root-level wrappers that no longer have callers.
- Do not delete a wrapper until `python -m pytest tests -q` passes without it.
- Before merging or handing off, run `@superpowers/verification-before-completion` and capture the exact commands and outputs in the session log.
