#!/usr/bin/env python3
"""Start a local HTTP static file server for this project."""

from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local HTTP static server.")
    parser.add_argument("--host", default="localhost", help="Bind host. Default: localhost")
    parser.add_argument("--port", type=int, default=8000, help="Bind port. Default: 8000")
    parser.add_argument(
        "--dir",
        default=".",
        help="Directory to serve. Default: current directory",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    serve_dir = Path(args.dir).resolve()

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *handler_args, **handler_kwargs):
            super().__init__(*handler_args, directory=str(serve_dir), **handler_kwargs)

    server = ThreadingHTTPServer((args.host, args.port), Handler)

    print(f"Serving HTTP from: {serve_dir}")
    print(f"URL: http://{args.host}:{args.port}/")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
