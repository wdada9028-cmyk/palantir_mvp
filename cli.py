from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipelines.build_ontology_pipeline import build_ontology_from_markdown


def _configure_console_output() -> None:
    for stream_name in ('stdout', 'stderr'):
        stream = getattr(sys, stream_name, None)
        if stream is None or not hasattr(stream, 'reconfigure'):
            continue
        try:
            stream.reconfigure(encoding='utf-8')
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    _configure_console_output()
    parser = argparse.ArgumentParser(description='Build ontology definition graph from markdown')
    subparsers = parser.add_subparsers(dest='command', required=True)

    build_parser = subparsers.add_parser('build-ontology', help='Build ontology definition graph artifacts from markdown')
    build_parser.add_argument('--input-file', type=str, required=True, help='Path to the ontology definition markdown file')
    build_parser.add_argument('--output-dir', type=str, default='output', help='Directory to write generated artifacts')
    build_parser.add_argument('--html', dest='generate_html', action='store_true', default=True, help='Generate interactive HTML output')
    build_parser.add_argument('--no-html', dest='generate_html', action='store_false', help='Skip interactive HTML output')
    build_parser.add_argument('--pdf', dest='generate_pdf', action='store_true', default=False, help='Generate PDF output')

    serve_parser = subparsers.add_parser('serve-ontology', help='Serve ontology HTTP page locally')
    serve_parser.add_argument('--input-file', type=str, required=True, help='Path to the ontology definition markdown file')
    serve_parser.add_argument('--host', type=str, default='127.0.0.1', help='Host interface for the local HTTP server')
    serve_parser.add_argument('--port', type=int, default=8000, help='Port for the local HTTP server')

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1

    if args.command == 'build-ontology':
        result = build_ontology_from_markdown(
            input_file=Path(args.input_file),
            output_dir=Path(args.output_dir),
            generate_html=args.generate_html,
            generate_pdf=args.generate_pdf,
        )
        for key in ('ontology_json', 'schema_summary_json', 'ontology_html', 'ontology_pdf'):
            path = result.get(key)
            if path is not None:
                print(f'{key}: {path}')
        return 0

    if args.command == 'serve-ontology':
        import uvicorn

        from .server.ontology_http_app import create_app

        app = create_app(input_file=Path(args.input_file))
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    return 1


if __name__ == '__main__':
    raise SystemExit(main())
