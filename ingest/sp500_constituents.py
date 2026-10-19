#!/usr/bin/env python3
"""Fetch S&P 500 constituents from FMP once → forge_bronze.sp500_constituent.

Run manually when the index membership changes (or before first price bootstrap):

  uv run python ingest/sp500_constituents.py init-schema   # first time only
  uv run python ingest/sp500_constituents.py refresh

API key: ingest/.env (fmp=...) or FMP_API_KEY env. MySQL: FORGE_MYSQL_* or ingest/.env
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from db import apply_schema, connect, ingest_env

LOG = logging.getLogger(__name__)
FMP_URL = "https://financialmodelingprep.com/stable/sp500-constituent"
DATASET = "sp500_constituent"

INSERT = """
    INSERT INTO forge_bronze.sp500_constituent
      (symbol, yf_ticker, name, sector, sub_sector, refreshed_at)
    VALUES (%(symbol)s, %(yf_ticker)s, %(name)s, %(sector)s, %(sub_sector)s, %(refreshed_at)s)
"""


def yf_ticker(symbol: str) -> str:
    return symbol.strip().upper().replace(".", "-")


def fmp_api_key() -> str:
    key = ingest_env("FMP_API_KEY") or ingest_env("fmp")
    if not key:
        raise RuntimeError("set fmp= in ingest/.env or export FMP_API_KEY")
    return key


def fetch_constituents() -> list[dict[str, Any]]:
    url = f"{FMP_URL}?{urlencode({'apikey': fmp_api_key()})}"
    req = Request(url, headers={"User-Agent": "alphanode-forge/0.2"})
    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")[:500]
        raise RuntimeError(f"FMP HTTP {exc.code}: {body}") from exc
    if not isinstance(data, list) or len(data) < 400:
        raise RuntimeError(f"unexpected FMP response: {len(data) if isinstance(data, list) else type(data)}")
    return data


def refresh() -> int:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = [
        {
            "symbol": r["symbol"].strip().upper(),
            "yf_ticker": yf_ticker(r["symbol"]),
            "name": r.get("name"),
            "sector": r.get("sector"),
            "sub_sector": r.get("subSector") or r.get("sub_sector"),
            "refreshed_at": now,
        }
        for r in fetch_constituents()
    ]
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO forge_bronze.ingest_run (source, dataset, status, started_at, params_json) "
            "VALUES ('fmp', %s, 'running', %s, %s)",
            (DATASET, now, json.dumps({"count": len(rows)})),
        )
        run_id = int(cur.lastrowid)
        conn.commit()
        try:
            cur.execute("DELETE FROM forge_bronze.sp500_constituent")
            cur.executemany(INSERT, rows)
            cur.execute(
                "UPDATE forge_bronze.ingest_run SET status='success', finished_at=%s, row_count=%s "
                "WHERE run_id=%s",
                (now, len(rows), run_id),
            )
            conn.commit()
            LOG.info("refreshed %d constituents (run_id=%s)", len(rows), run_id)
            return len(rows)
        except Exception as exc:
            cur.execute(
                "UPDATE forge_bronze.ingest_run SET status='failed', finished_at=%s, error_message=%s "
                "WHERE run_id=%s",
                (now, str(exc)[:4000], run_id),
            )
            conn.commit()
            raise


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FMP S&P 500 constituents → forge_bronze")
    p.add_argument("-v", "--verbose", action="count", default=0)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-schema")
    sub.add_parser("refresh")
    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose > 1 else logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(message)s",
    )
    if args.cmd == "init-schema":
        with connect() as conn:
            apply_schema(conn)
        LOG.info("schema applied")
        return 0
    refresh()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
