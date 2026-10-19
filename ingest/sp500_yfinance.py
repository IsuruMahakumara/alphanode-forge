#!/usr/bin/env python3
"""Bronze ingest: S&P 500 daily EOD from yfinance → forge_bronze.

Universe: forge_bronze.sp500_constituent (yf_ticker column).

  uv run python ingest/sp500_yfinance.py init-schema
  uv run python ingest/sp500_yfinance.py bootstrap
  uv run python ingest/sp500_yfinance.py bootstrap --from 2026-01-01
  uv run python ingest/sp500_yfinance.py delta

Env: FORGE_MYSQL_*
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterator

import pandas as pd
import pymysql.connections
import yfinance as yf

from db import apply_schema, connect

DATASET = "sp500_eod"
BATCH_SIZE = 64
INSERT_CHUNK = 10_000
RENAME = {
    "Date": "trade_date",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Adj Close": "adj_close",
    "Volume": "volume",
    "Dividends": "dividends",
    "Stock Splits": "stock_splits",
}
COLS = (
    "run_id",
    "yf_ticker",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "dividends",
    "stock_splits",
)
INSERT = f"INSERT INTO forge_bronze.yfinance_equity_eod ({', '.join(COLS)}) VALUES ({', '.join(f'%({c})s' for c in COLS)})"


def say(msg: str) -> None:
    print(msg, flush=True)


def load_yf_tickers(conn: pymysql.connections.Connection) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT yf_ticker FROM forge_bronze.sp500_constituent ORDER BY yf_ticker")
        tickers = [row["yf_ticker"] for row in cur.fetchall()]
    if len(tickers) < 400:
        raise RuntimeError(
            f"forge_bronze.sp500_constituent has {len(tickers)} rows; populate the universe table first"
        )
    return tickers


def window(mode: str, conn: pymysql.connections.Connection, from_d: date | None) -> tuple[date, date]:
    end = date.today()
    if mode == "bootstrap":
        return from_d or date(end.year, 1, 1), end
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT MAX(b.trade_date) AS d
            FROM forge_bronze.yfinance_equity_eod b
            JOIN forge_bronze.ingest_run r ON r.run_id = b.run_id
            WHERE r.dataset = %s AND r.status = 'success'
            """,
            (DATASET,),
        )
        last = cur.fetchone()["d"]
    if not last:
        raise RuntimeError("no bronze SP500 data yet; run bootstrap first")
    start = last + timedelta(days=1)
    if start > end:
        raise RuntimeError(f"already current through {last}")
    return start, end


def _flat_columns(frame: pd.DataFrame) -> pd.DataFrame:
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    return frame


def _batch_slices(raw: pd.DataFrame, tickers: list[str]) -> Iterator[tuple[str, pd.DataFrame]]:
    if raw.empty:
        return
    if len(tickers) == 1:
        yield tickers[0], raw
        return
    if not isinstance(raw.columns, pd.MultiIndex):
        yield tickers[0], raw
        return
    level0 = raw.columns.get_level_values(0)
    for t in tickers:
        if t in level0:
            yield t, raw[t]
        else:
            say(f"  warn: no yfinance data for {t}")


def _rows_from_batch(raw: pd.DataFrame, tickers: list[str], run_id: int, start: date, end: date) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t, sub in _batch_slices(raw, tickers):
        frame = _flat_columns(sub.reset_index()).rename(columns=RENAME)
        for c in ("dividends", "stock_splits"):
            if c not in frame.columns:
                frame[c] = 0.0
        frame["yf_ticker"] = t
        frame["run_id"] = run_id
        frame["trade_date"] = pd.to_datetime(frame["trade_date"]).dt.date
        frame = frame[(frame["trade_date"] >= start) & (frame["trade_date"] <= end)]
        for row in frame[list(RENAME.values()) + ["yf_ticker", "run_id"]].to_dict("records"):
            out.append(
                {
                    k: (None if isinstance(v, float) and v != v else v)
                    for k, v in row.items()
                }
            )
    return out


def download_batch(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    return yf.download(
        tickers,
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        auto_adjust=False,
        actions=True,
        group_by="ticker",
        threads=True,
        progress=False,
    )


def insert_rows(cur: pymysql.connections.Cursor, rows: list[dict[str, Any]]) -> int:
    for i in range(0, len(rows), INSERT_CHUNK):
        cur.executemany(INSERT, rows[i : i + INSERT_CHUNK])
    return len(rows)


def ingest(mode: str, tickers: list[str], start: date, end: date) -> int:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    params = json.dumps({"mode": mode, "start": start.isoformat(), "end": end.isoformat(), "tickers": len(tickers)})
    batches = [tickers[i : i + BATCH_SIZE] for i in range(0, len(tickers), BATCH_SIZE)]
    total_rows = 0

    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO forge_bronze.ingest_run (source, dataset, status, started_at, params_json) "
            "VALUES ('yfinance', %s, 'running', %s, %s)",
            (DATASET, now, params),
        )
        run_id = int(cur.lastrowid)
        conn.commit()
        say(f"ingest run_id={run_id} mode={mode} window={start} → {end} tickers={len(tickers)}")

        try:
            for n, batch in enumerate(batches, start=1):
                say(f"batch {n}/{len(batches)}: downloading {len(batch)} tickers …")
                raw = download_batch(batch, start, end)
                rows = _rows_from_batch(raw, batch, run_id, start, end)
                if not rows:
                    say(f"batch {n}/{len(batches)}: 0 rows, skipped")
                    continue
                inserted = insert_rows(cur, rows)
                conn.commit()
                total_rows += inserted
                say(f"batch {n}/{len(batches)}: inserted {inserted} rows (total {total_rows})")

            cur.execute(
                "UPDATE forge_bronze.ingest_run SET status='success', finished_at=%s, row_count=%s "
                "WHERE run_id=%s",
                (datetime.now(timezone.utc).replace(tzinfo=None), total_rows, run_id),
            )
            conn.commit()
            say(f"done run_id={run_id} rows={total_rows}")
            return total_rows
        except Exception as exc:
            cur.execute(
                "UPDATE forge_bronze.ingest_run SET status='failed', finished_at=%s, error_message=%s "
                "WHERE run_id=%s",
                (datetime.now(timezone.utc).replace(tzinfo=None), str(exc)[:4000], run_id),
            )
            conn.commit()
            say(f"failed run_id={run_id}: {exc}", file=sys.stderr)
            raise


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="S&P 500 yfinance → forge_bronze")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-schema")
    boot = sub.add_parser("bootstrap")
    boot.add_argument("--from", dest="from_d", metavar="DATE", help="default: Jan 1 this year")
    sub.add_parser("delta")
    args = p.parse_args(argv)

    if args.cmd == "init-schema":
        with connect() as conn:
            apply_schema(conn)
        say("schema applied (forge_bronze)")
        return 0

    from_d = date.fromisoformat(args.from_d) if getattr(args, "from_d", None) else None
    with connect() as conn:
        tickers = load_yf_tickers(conn)
        start, end = window(args.cmd, conn, from_d)
    say(f"loaded {len(tickers)} tickers from forge_bronze.sp500_constituent")
    ingest(args.cmd, tickers, start, end)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
