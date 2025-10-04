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


BOOLEAN_FIELDS = [
    "criminal_history",
    "addiction_history",
    "addiction_current",
    "disability",
    "mental_illness_history",
    "high_school_ed",
    "work_history",
    "higher_ed",
    "veteran",
    "dependents",
]

NON_ID_FIELDS = [
    "first_name",
    "last_name",
    "date_of_birth",
    "address",
    "zip",
    *BOOLEAN_FIELDS,
]

EXPECTED_COLUMNS = {"id"} | set(NON_ID_FIELDS)

CREATE_TABLE_SQL = """
    CREATE TABLE people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        date_of_birth TEXT,
        address TEXT,
        zip TEXT,
        criminal_history INTEGER,
        addiction_history INTEGER,
        addiction_current INTEGER,
        disability INTEGER,
        mental_illness_history INTEGER,
        high_school_ed INTEGER,
        work_history INTEGER,
        higher_ed INTEGER,
        veteran INTEGER,
        dependents INTEGER
    )
"""


def ensure_schema(conn: sqlite3.Connection) -> None:
    existing_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='people'"
    ).fetchone()

    if not existing_table:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
        return

    column_rows = conn.execute("PRAGMA table_info(people)").fetchall()
    existing_columns = {row[1] for row in column_rows}

    if existing_columns != EXPECTED_COLUMNS:
        conn.execute("DROP TABLE IF EXISTS people")
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()


def init_db() -> None:
    with get_connection() as conn:
        ensure_schema(conn)
        if conn.execute("SELECT COUNT(*) FROM people").fetchone()[0] == 0:
            conn.executemany(
                """
                INSERT INTO people (
                    first_name,
                    last_name,
                    date_of_birth,
                    address,
                    zip,
                    criminal_history,
                    addiction_history,
                    addiction_current,
                    disability,
                    mental_illness_history,
                    high_school_ed,
                    work_history,
                    higher_ed,
                    veteran,
                    dependents
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "Ada",
                        "Lovelace",
                        "1815-12-10",
                        "12 St James's Square, London",
                        "20500",
                        0,
                        0,
                        0,
                        0,
                        0,
                        1,
                        1,
                        1,
                        0,
                        1,
                    ),
                    (
                        "Alan",
                        "Turing",
                        "1912-06-23",
                        "Kings Parade, Cambridge",
                        "02142",
                        0,
                        0,
                        0,
                        0,
                        1,
                        1,
                        1,
                        1,
                        1,
                        0,
                    ),
                    (
                        "Grace",
                        "Hopper",
                        "1906-12-09",
                        "11 Wall Street, New York",
                        "10001",
                        0,
                        0,
                        0,
                        0,
                        0,
                        1,
                        1,
                        1,
                        1,
                        0,
                    ),
                ],
            )
            conn.commit()


def normalize_person_row(row: sqlite3.Row) -> Dict[str, object]:
    person = dict(row)
    for field in BOOLEAN_FIELDS:
        if person[field] is None:
            person[field] = None
        else:
            person[field] = bool(person[field])
    return person


def list_people() -> List[Dict[str, object]]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                date_of_birth,
                address,
                zip,
                criminal_history,
                addiction_history,
                addiction_current,
                disability,
                mental_illness_history,
                high_school_ed,
                work_history,
                higher_ed,
                veteran,
                dependents
            FROM people
            ORDER BY id
            """
        )
        return [normalize_person_row(row) for row in cursor.fetchall()]


def parse_tristate_value(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(bool(value))
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"", "null", "none"}:
            return None
        if normalized in {"1", "true", "yes", "on"}:
            return 1
        if normalized in {"0", "false", "no", "off"}:
            return 0
    return None


def create_person(payload: Dict[str, object]) -> Dict[str, object]:
    zip_raw = payload.get("zip")
    zip_value: str | None
    if zip_raw in (None, ""):
        zip_value = None
    else:
        zip_str = str(zip_raw).strip()
        if not (len(zip_str) == 5 and zip_str.isdigit()):
            raise ValueError("ZIP code must be exactly 5 digits")
        zip_value = zip_str

    sanitized: Dict[str, object] = {
        "first_name": str(payload.get("first_name", "")).strip(),
        "last_name": str(payload.get("last_name", "")).strip(),
        "date_of_birth": str(payload.get("date_of_birth", "")).strip(),
        "address": str(payload.get("address", "")).strip(),
        "zip": zip_value,
    }

    for field in BOOLEAN_FIELDS:
        sanitized[field] = parse_tristate_value(payload.get(field))

    if not sanitized["first_name"] or not sanitized["last_name"]:
        raise ValueError("Missing required fields")

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO people (
                first_name,
                last_name,
                date_of_birth,
                address,
                zip,
                criminal_history,
                addiction_history,
                addiction_current,
                disability,
                mental_illness_history,
                high_school_ed,
                work_history,
                higher_ed,
                veteran,
                dependents
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(sanitized[field] for field in NON_ID_FIELDS),
        )
        conn.commit()
        person = {"id": cursor.lastrowid, **sanitized}
        for field in BOOLEAN_FIELDS:
            if person[field] is None:
                continue
            person[field] = bool(person[field])
        return person


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

        required_fields = ["first_name", "last_name"]
        missing = [
            field
            for field in required_fields
            if payload.get(field) in (None, "")
        ]
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

        try:
            person = create_person(payload)
        except ValueError as error:
            self._set_json_headers(HTTPStatus.BAD_REQUEST)
            self.wfile.write(json.dumps({"error": str(error)}).encode("utf-8"))
            return

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
