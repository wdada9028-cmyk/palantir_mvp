from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from ..export.graph_export import build_graph_payload, build_interactive_graph_html
from ..ontology.definition_graph_builder import build_definition_graph
from ..ontology.definition_markdown_parser import parse_definition_markdown
from ..qa.template_answering import build_template_answer
from ..search.ontology_query_engine import retrieve_ontology_evidence
from .ontology_http_service import iter_qa_events


def create_app(*, input_file: Path) -> FastAPI:
    input_path = Path(input_file)
    text = input_path.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(input_path))
    graph = build_definition_graph(spec)
    graph_payload = build_graph_payload(graph)
    html = build_interactive_graph_html(graph, title=graph.metadata.get('title', 'Ontology Graph'))

    app = FastAPI()
    app.state.input_file = input_path
    app.state.graph = graph
    app.state.graph_payload = graph_payload
    app.state.graph_html = html

    @app.get('/ontology', response_class=HTMLResponse)
    def ontology_page() -> str:
        return app.state.graph_html

    @app.get('/api/graph', response_class=JSONResponse)
    def graph_payload_api() -> dict[str, object]:
        return app.state.graph_payload

    @app.get('/api/qa/stream')
    def qa_stream(q: str = Query(..., min_length=1)) -> StreamingResponse:
        bundle = retrieve_ontology_evidence(app.state.graph, q)
        fallback_answer = build_template_answer(bundle)
        return StreamingResponse(iter_qa_events(bundle, fallback_answer), media_type='text/event-stream')

    return app
