from __future__ import annotations

import json
import sqlite3
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import TCPServer
from typing import Dict, List

APP_ROOT = Path(__file__).resolve().parent
STATIC_DIR = APP_ROOT / "static"
DB_PATH = APP_ROOT / "people.db"
HOST = "0.0.0.0"
PORT = 5000


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                zip_code TEXT NOT NULL
            )
            """
        )
        if conn.execute("SELECT COUNT(*) FROM people").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO people (first_name, last_name, zip_code) VALUES (?, ?, ?)",
                [
                    ("Ada", "Lovelace", "20500"),
                    ("Alan", "Turing", "02142"),
                    ("Grace", "Hopper", "10001"),
                ],
            )
            conn.commit()


def list_people() -> List[Dict[str, str]]:
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT id, first_name, last_name, zip_code FROM people ORDER BY id"
        )
        return [dict(row) for row in cursor.fetchall()]


def create_person(payload: Dict[str, str]) -> Dict[str, str]:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO people (first_name, last_name, zip_code) VALUES (?, ?, ?)",
            (
                payload["first_name"].strip(),
                payload["last_name"].strip(),
                payload["zip_code"].strip(),
            ),
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "first_name": payload["first_name"].strip(),
            "last_name": payload["last_name"].strip(),
            "zip_code": payload["zip_code"].strip(),
        }


class DirectoryRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:  # pragma: no cover
        # Quieter output while running in the demo environment.
        return

    def _set_json_headers(self, status: HTTPStatus) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802 (keep http.server naming)
        if self.path == "/api/people":
            people = list_people()
            payload = json.dumps({"people": people}).encode("utf-8")
            self._set_json_headers(HTTPStatus.OK)
            self.wfile.write(payload)
            return

        if self.path == "/":
            self.path = "/index.html"

        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/people":
            self.send_error(HTTPStatus.NOT_FOUND, "Endpoint not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)

        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._set_json_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(
                json.dumps({"error": "Invalid JSON payload"}).encode("utf-8")
            )
            return

        required_fields = ["first_name", "last_name", "zip_code"]
        missing = [field for field in required_fields if not payload.get(field)]
        if missing:
            self._set_json_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(
                json.dumps(
                    {
                        "error": "Missing required fields",
                        "details": missing,
                    }
                ).encode("utf-8")
            )
            return

        person = create_person(payload)
        self._set_json_headers(HTTPStatus.CREATED)
        self.wfile.write(json.dumps(person).encode("utf-8"))


def run_server() -> None:
    init_db()
    with TCPServer((HOST, PORT), DirectoryRequestHandler) as httpd:
        print(f"Serving on http://{HOST}:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:  # pragma: no cover
            print("\nShutting down...")


if __name__ == "__main__":
    run_server()
