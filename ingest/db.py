"""Shared MySQL connection for ingest scripts."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import pymysql
import pymysql.cursors
from pymysql.connections import Connection

SQL_FILE = Path(__file__).parent / "sql" / "warehouse.sql"
ENV_FILE = Path(__file__).parent / ".env"


def ingest_env(name: str) -> str | None:
    if val := os.environ.get(name):
        v = val.strip()
        return v or None
    if not ENV_FILE.is_file():
        return None
    keys = {name, name.lower()}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        k, _, v = s.partition("=")
        if k.strip() in keys:
            out = v.strip()
            return out or None
    return None


def db_config() -> dict[str, Any]:
    return {
        "host": os.environ.get("FORGE_MYSQL_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_MYSQL_PORT", "3309")),
        "user": os.environ.get("FORGE_MYSQL_USER", "root"),
        "password": os.environ.get("FORGE_MYSQL_PASSWORD", "wtf333"),
        "charset": "utf8mb4",
        "autocommit": False,
        "cursorclass": pymysql.cursors.DictCursor,
    }


@contextmanager
def connect() -> Generator[Connection, None, None]:
    conn = pymysql.connect(**db_config())
    try:
        with conn.cursor() as cur:
            cur.execute("SET time_zone = '+00:00'")
        conn.commit()
        yield conn
    finally:
        conn.close()


def apply_schema(conn: Connection) -> None:
    with conn.cursor() as cur:
        for stmt in SQL_FILE.read_text(encoding="utf-8").split(";"):
            if s := stmt.strip():
                cur.execute(s)
    conn.commit()
