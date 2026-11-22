"""Dev server: serves site/ under /portfolio/ like GitHub Pages does."""
from __future__ import annotations

import argparse
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SITE_DIR: Path = Path(__file__).resolve().parent.parent / "site"
BASE_PATH = "/portfolio"
DEFAULT_PORT = 8000


class PagesHandler(SimpleHTTPRequestHandler):
    def _redirect(self, status: HTTPStatus, location: str) -> None:
        self.send_response(status)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def translate_path(self, path: str) -> str:
        # Strip the base path so /portfolio/x maps to site/x.
        return super().translate_path(path[len(BASE_PATH):] or "/")

    def do_GET(self) -> None:
        raw = self.path.split("?", 1)[0].split("#", 1)[0]
        query = self.path[len(raw):]
        if raw == "/":
            self._redirect(HTTPStatus.FOUND, BASE_PATH + "/")
        elif raw == BASE_PATH:
            self._redirect(HTTPStatus.MOVED_PERMANENTLY, BASE_PATH + "/" + query)
        elif raw.startswith(BASE_PATH + "/"):
            super().do_GET()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    do_HEAD = do_GET

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    handler = partial(PagesHandler, directory=str(SITE_DIR))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Serving site/ at http://localhost:{args.port}{BASE_PATH}/")
        server.serve_forever()


if __name__ == "__main__":
    main()
