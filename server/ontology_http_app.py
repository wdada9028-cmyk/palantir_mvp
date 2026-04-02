from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from ..export.graph_export import build_graph_payload, build_interactive_graph_html
from ..instance_qa.orchestrator import run_instance_qa
from ..ontology.definition_graph_builder import build_definition_graph
from ..ontology.definition_markdown_parser import parse_definition_markdown
from ..pipelines.input_file_resolver import resolve_input_to_markdown
from .ontology_http_service import iter_qa_events


def create_app(*, input_file: Path) -> FastAPI:
    input_path = Path(input_file)
    resolved_input_path = resolve_input_to_markdown(input_path)
    text = resolved_input_path.read_text(encoding='utf-8')
    spec = parse_definition_markdown(text, source_file=str(resolved_input_path))
    graph = build_definition_graph(spec)
    graph_payload = build_graph_payload(graph)
    html = build_interactive_graph_html(graph, title=graph.metadata.get('title', 'Ontology Graph'))

    app = FastAPI()
    app.state.input_file = input_path
    app.state.resolved_input_file = resolved_input_path
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
        result = run_instance_qa(q, app.state.graph)
        return StreamingResponse(iter_qa_events(result), media_type='text/event-stream')

    return app
