#!/usr/bin/env python3
"""Bronze ingest: FX spot daily EOD from yfinance → forge_bronze.

  uv run python ingest/fx_yfinance.py init-schema
  uv run python ingest/fx_yfinance.py bootstrap
  uv run python ingest/fx_yfinance.py bootstrap --from 2026-01-01
  uv run python ingest/fx_yfinance.py delta

Env: FORGE_MYSQL_*
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import polars as pl
import pymysql.connections
import yfinance as yf

from db import apply_schema, connect

LOG = logging.getLogger(__name__)
DATASET = "fx_eod"
PAIRS = {
    # "EUR/USD": "EURUSD=X",
    # "USD/JPY": "USDJPY=X",
    # "USD/CNY": "USDCNY=X",
    # "GBP/USD": "GBPUSD=X",
    # "USD/SGD": "USDSGD=X",
    "USD/LKR": "USDLKR=X",
   # "USD/INR": "USDINR=X",
}
RENAME = {
    "Date": "trade_date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
}
COLS = ("run_id", "yf_ticker", "pair", "trade_date", "open", "high", "low", "close", "adj_close")
INSERT = f"INSERT INTO forge_bronze.yfinance_fx_eod ({', '.join(COLS)}) VALUES ({', '.join(f'%({c})s' for c in COLS)})"


def window(mode: str, conn: pymysql.connections.Connection, from_d: date | None) -> tuple[date, date]:
    end = date.today()
    if mode == "bootstrap":
        return from_d or date(end.year, 1, 1), end
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT MAX(b.trade_date) AS d
            FROM forge_bronze.yfinance_fx_eod b
            JOIN forge_bronze.ingest_run r ON r.run_id = b.run_id
            WHERE r.dataset = %s AND r.status = 'success'
            """,
            (DATASET,),
        )
        last = cur.fetchone()["d"]
    if not last:
        raise RuntimeError("no bronze data; run bootstrap first")
    start = last + timedelta(days=1)
    if start > end:
        raise RuntimeError(f"already current through {last}")
    return start, end


def download(start: date, end: date) -> pl.DataFrame:
    end_excl = (end + timedelta(days=1)).isoformat()
    parts: list[pd.DataFrame] = []
    for pair, ticker in PAIRS.items():
        raw = yf.download(
            ticker,
            start=start.isoformat(),
            end=end_excl,
            auto_adjust=False,
            actions=False,
            progress=False,
            multi_level_index=False,
        )
        if raw.empty:
            LOG.warning("no data for %s (%s)", pair, ticker)
            continue
        frame = raw.reset_index().rename(columns=RENAME)
        frame["yf_ticker"] = ticker
        frame["pair"] = pair
        parts.append(frame[list(RENAME.values()) + ["yf_ticker", "pair"]])

    if not parts:
        return pl.DataFrame()
    return (
        pl.from_pandas(pd.concat(parts, ignore_index=True), include_index=False)
        .with_columns(pl.col("trade_date").cast(pl.Date))
        .filter(pl.col("trade_date").is_between(start, end))
        .unique(subset=["yf_ticker", "trade_date"], keep="last")
        .sort("pair", "trade_date")
    )


def ingest(mode: str, from_d: date | None = None) -> int:
    with connect() as conn:
        start, end = window(mode, conn, from_d)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        params = json.dumps({"mode": mode, "start": start.isoformat(), "end": end.isoformat()})
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO forge_bronze.ingest_run (source, dataset, status, started_at, params_json) "
            "VALUES ('yfinance', %s, 'running', %s, %s)",
            (DATASET, now, params),
        )
        run_id = int(cur.lastrowid)
        conn.commit()
        try:
            frame = download(start, end).with_columns(pl.lit(run_id).alias("run_id"))
            rows = [
                {k: (None if isinstance(v, float) and v != v else v) for k, v in r.items()}
                for r in frame.select(COLS).to_dicts()
            ]
            for i in range(0, len(rows), 10_000):
                cur.executemany(INSERT, rows[i : i + 10_000])
            conn.commit()
            cur.execute(
                "UPDATE forge_bronze.ingest_run SET status='success', finished_at=%s, row_count=%s "
                "WHERE run_id=%s",
                (datetime.now(timezone.utc).replace(tzinfo=None), len(rows), run_id),
            )
            conn.commit()
            LOG.info("run_id=%s rows=%d", run_id, len(rows))
            return len(rows)
        except Exception as exc:
            cur.execute(
                "UPDATE forge_bronze.ingest_run SET status='failed', finished_at=%s, error_message=%s "
                "WHERE run_id=%s",
                (datetime.now(timezone.utc).replace(tzinfo=None), str(exc)[:4000], run_id),
            )
            conn.commit()
            raise


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="FX spot yfinance → forge_bronze")
    p.add_argument("-v", "--verbose", action="count", default=0)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-schema")
    boot = sub.add_parser("bootstrap")
    boot.add_argument("--from", dest="from_d", metavar="DATE", help="default: Jan 1 this year")
    sub.add_parser("delta")
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

    from_d = date.fromisoformat(args.from_d) if getattr(args, "from_d", None) else None
    ingest(args.cmd, from_d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
