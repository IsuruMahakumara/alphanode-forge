# Data warehouse: MySQL / HeatWave medallion

Local **MySQL** (`localhost:3309`) is the write path and dev catalog. **OCI MySQL HeatWave** is the analytics replica (same protocol, columnar acceleration on silver/gold).

Medallion layers: **bronze** (immutable raw), **silver** (conformed dimensions + facts), **gold** (research-ready panels). Schema is the contract — get it right before writing ingest code.

---

## Topology

```
yfinance (bootstrap) ──► Polars ETL ──► forge_bronze.*
                              │
                              ▼ SQL transforms / upserts
                         forge_silver.*
                              │
                              ▼ SQL views / materialized facts
                          forge_gold.*
                              │
                              ▼ replication (OCI)
                      HeatWave (analytics)
```

| Environment | Role | Port / notes |
|-------------|------|--------------|
| Local MySQL | Ingest, DDL, incremental loads | `3309` (see `native/common/connect_db.hpp`) |
| OCI HeatWave | Cross-asset joins, notebook SQL, large scans | Same `libmysqlclient` wire protocol |

**Time zone:** all `DATETIME` columns are UTC. Every session runs `SET time_zone = '+00:00'`.

**Identifiers:** tickers are *source* symbols (what yfinance expects). Canonical symbols live in `silver.dim_security`. Never join gold tables on raw yfinance strings alone — always resolve through `security_id`.

---

## Medallion rules

| Layer | Database | Mutability | Contents |
|-------|----------|------------|----------|
| **Bronze** | `forge_bronze` | Append-only per `run_id` | Raw vendor shapes, ingest lineage |
| **Silver** | `forge_silver` | Upsert / merge | Conformed instruments, cleaned EOD facts |
| **Gold** | `forge_gold` | Rebuild or incremental | Returns, panels, features for `research/` and `forge/` |

**Promotion direction:** bronze → silver → gold. Notebooks and models read **gold** (or silver for debugging). Bronze is never queried in production research.

---

## Schema

Three MySQL **schemas** (databases). DDL below is the v1 contract for S&P 500 bootstrap via yfinance; FX, commodities, and macro extend the same pattern with new `dim_*` / `fact_*` tables — not new layering rules.

### Naming conventions

| Element | Rule | Example |
|---------|------|---------|
| Schema | `forge_{layer}` | `forge_silver` |
| Dimension | `dim_{entity}` | `dim_security` |
| Fact | `fact_{domain}_{grain}` | `fact_equity_eod` |
| Surrogate key | `{entity}_id` `BIGINT UNSIGNED` | `security_id` |
| Natural key (silver+) | `UNIQUE` constraint | `(security_id, trade_date)` |
| Money / prices | `DECIMAL(18,6)` | avoids float drift |
| Volume | `BIGINT UNSIGNED` | |
| Dates | `DATE` for market days | never `DATETIME` for EOD bars |

---

### `forge_bronze` — raw ingest

Bronze preserves vendor field names and supports reprocessing. One ingest execution = one `ingest_run` row.

```sql
CREATE DATABASE IF NOT EXISTS forge_bronze
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- ── Lineage ────────────────────────────────────────────────────────────────

CREATE TABLE forge_bronze.ingest_run (
  run_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  source         VARCHAR(32)     NOT NULL COMMENT 'yfinance | fred | fmp | ...',
  dataset        VARCHAR(64)     NOT NULL COMMENT 'sp500_eod | fx_g10_eod | ...',
  status         ENUM('running','success','failed') NOT NULL DEFAULT 'running',
  started_at     DATETIME(6)     NOT NULL,
  finished_at    DATETIME(6)     NULL,
  row_count      BIGINT UNSIGNED NULL,
  params_json    JSON            NULL COMMENT 'from, to, ticker_count, git_commit, ...',
  error_message  TEXT            NULL,
  PRIMARY KEY (run_id),
  KEY idx_ingest_run_dataset_started (dataset, started_at)
) ENGINE=InnoDB;

-- ── yfinance S&P 500 daily bars (bootstrap) ───────────────────────────────

CREATE TABLE forge_bronze.yfinance_equity_eod (
  run_id         BIGINT UNSIGNED NOT NULL,
  yf_ticker      VARCHAR(24)     NOT NULL COMMENT 'symbol passed to yfinance e.g. BRK-B',
  trade_date     DATE            NOT NULL,
  open           DECIMAL(18,6)   NULL,
  high           DECIMAL(18,6)   NULL,
  low            DECIMAL(18,6)   NULL,
  close          DECIMAL(18,6)   NULL,
  adj_close      DECIMAL(18,6)   NULL,
  volume         BIGINT UNSIGNED NULL,
  dividends      DECIMAL(18,8)   NOT NULL DEFAULT 0,
  stock_splits   DECIMAL(18,8)   NOT NULL DEFAULT 0,
  ingested_at    DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (run_id, yf_ticker, trade_date),
  KEY idx_yf_ticker_date (yf_ticker, trade_date),
  CONSTRAINT fk_bronze_eod_run
    FOREIGN KEY (run_id) REFERENCES forge_bronze.ingest_run (run_id)
) ENGINE=InnoDB;
```

**yfinance mapping notes**

| yfinance output | Bronze column | Silver handling |
|-----------------|---------------|-----------------|
| `Open` | `open` | pass-through |
| `High` | `high` | pass-through |
| `Low` | `low` | pass-through |
| `Close` | `close` | unadjusted close |
| `Adj Close` | `adj_close` | preferred for returns |
| `Volume` | `volume` | pass-through |
| `Dividends` | `dividends` | corporate-action flag |
| `Stock Splits` | `stock_splits` | corporate-action flag |
| Index name / ticker | `yf_ticker` | map → `dim_security.yf_ticker` |

Rows with all OHLC `NULL` (delisted / halted / bad pull) stay in bronze for audit; silver excludes them.

---

### `forge_silver` — conformed warehouse

Silver is the **system of record** for instruments and cleaned daily prices.

```sql
CREATE DATABASE IF NOT EXISTS forge_silver
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- ── Instrument registry ───────────────────────────────────────────────────

CREATE TABLE forge_silver.dim_security (
  security_id    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  yf_ticker      VARCHAR(24)     NOT NULL COMMENT 'primary yfinance symbol',
  canonical_symbol VARCHAR(24)   NOT NULL COMMENT 'internal stable symbol',
  exchange       VARCHAR(16)     NULL     COMMENT 'NYSE | NASDAQ | ...',
  currency       CHAR(3)         NOT NULL DEFAULT 'USD',
  asset_class    ENUM('equity','etf','index','fx','commodity','crypto','macro')
                 NOT NULL DEFAULT 'equity',
  name           VARCHAR(256)    NULL,
  is_active      TINYINT(1)      NOT NULL DEFAULT 1,
  valid_from     DATE            NOT NULL DEFAULT (CURRENT_DATE),
  valid_to       DATE            NULL,
  created_at     DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at     DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                               ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (security_id),
  UNIQUE KEY uq_dim_security_yf_ticker (yf_ticker),
  UNIQUE KEY uq_dim_security_canonical (canonical_symbol),
  KEY idx_dim_security_asset_active (asset_class, is_active)
) ENGINE=InnoDB;

-- S&P 500 membership (point-in-time universe for backtests)
CREATE TABLE forge_silver.dim_index_constituent (
  index_code     VARCHAR(16)     NOT NULL DEFAULT 'SP500',
  security_id    BIGINT UNSIGNED NOT NULL,
  effective_from DATE            NOT NULL,
  effective_to   DATE            NULL COMMENT 'NULL = current member',
  source         VARCHAR(32)     NOT NULL DEFAULT 'bootstrap_static',
  PRIMARY KEY (index_code, security_id, effective_from),
  KEY idx_constituent_asof (index_code, effective_from, effective_to),
  CONSTRAINT fk_constituent_security
    FOREIGN KEY (security_id) REFERENCES forge_silver.dim_security (security_id)
) ENGINE=InnoDB;

-- ── Cleaned EOD prices (one row per security per trade date) ──────────────

CREATE TABLE forge_silver.fact_equity_eod (
  security_id    BIGINT UNSIGNED NOT NULL,
  trade_date     DATE            NOT NULL,
  open           DECIMAL(18,6)   NULL,
  high           DECIMAL(18,6)   NULL,
  low            DECIMAL(18,6)   NULL,
  close          DECIMAL(18,6)   NULL,
  adj_close      DECIMAL(18,6)   NULL,
  volume         BIGINT UNSIGNED NULL,
  dividends      DECIMAL(18,8)   NOT NULL DEFAULT 0,
  stock_splits   DECIMAL(18,8)   NOT NULL DEFAULT 0,
  source         VARCHAR(32)     NOT NULL DEFAULT 'yfinance',
  source_run_id  BIGINT UNSIGNED NULL COMMENT 'provenance: forge_bronze.ingest_run.run_id',
  updated_at     DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
                               ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (security_id, trade_date),
  KEY idx_fact_equity_eod_date (trade_date),
  KEY idx_fact_equity_eod_source_run (source_run_id),
  CONSTRAINT fk_fact_equity_security
    FOREIGN KEY (security_id) REFERENCES forge_silver.dim_security (security_id)
) ENGINE=InnoDB;
```

**Silver merge rule (bronze → silver):** for each `(yf_ticker, trade_date)`, take the row from the latest successful `run_id` where `adj_close IS NOT NULL`. Upsert into `fact_equity_eod` on `(security_id, trade_date)`.

---

### `forge_gold` — research-ready

Gold holds derived, query-optimized objects for notebooks (`research/`) and library code (`forge/features`).

```sql
CREATE DATABASE IF NOT EXISTS forge_gold
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- Daily simple & log returns on adjusted close
CREATE TABLE forge_gold.fact_equity_returns_daily (
  security_id       BIGINT UNSIGNED NOT NULL,
  trade_date        DATE            NOT NULL,
  adj_close         DECIMAL(18,6)   NOT NULL,
  return_simple     DECIMAL(18,10)  NULL COMMENT '(P_t - P_{t-1}) / P_{t-1}',
  return_log        DECIMAL(18,10)  NULL COMMENT 'ln(P_t / P_{t-1})',
  PRIMARY KEY (security_id, trade_date),
  KEY idx_returns_date (trade_date),
  CONSTRAINT fk_returns_security
    FOREIGN KEY (security_id) REFERENCES forge_silver.dim_security (security_id)
) ENGINE=InnoDB;

-- Long-format panel: SP500 universe, ready for Polars / SQL pivot
CREATE TABLE forge_gold.panel_sp500_eod (
  trade_date        DATE            NOT NULL,
  security_id       BIGINT UNSIGNED NOT NULL,
  canonical_symbol  VARCHAR(24)     NOT NULL,
  adj_close         DECIMAL(18,6)   NOT NULL,
  volume            BIGINT UNSIGNED NULL,
  return_log        DECIMAL(18,10)  NULL,
  PRIMARY KEY (trade_date, security_id),
  KEY idx_panel_symbol_date (canonical_symbol, trade_date)
) ENGINE=InnoDB;
```

**Gold build (SQL sketch):**

```sql
-- panel_sp500_eod: SP500 members only, adjusted close + log return
INSERT INTO forge_gold.panel_sp500_eod (trade_date, security_id, canonical_symbol, adj_close, volume, return_log)
SELECT
  f.trade_date,
  f.security_id,
  s.canonical_symbol,
  f.adj_close,
  f.volume,
  r.return_log
FROM forge_silver.fact_equity_eod f
JOIN forge_silver.dim_security s ON s.security_id = f.security_id
JOIN forge_silver.dim_index_constituent c
  ON c.security_id = f.security_id
 AND c.index_code = 'SP500'
 AND f.trade_date >= c.effective_from
 AND (c.effective_to IS NULL OR f.trade_date <= c.effective_to)
LEFT JOIN forge_gold.fact_equity_returns_daily r
  ON r.security_id = f.security_id AND r.trade_date = f.trade_date
WHERE f.adj_close IS NOT NULL;
```

---

### Entity relationship (bootstrap scope)

```
ingest_run ──< yfinance_equity_eod          [bronze]

dim_security ──< dim_index_constituent      [silver]
      │
      └──< fact_equity_eod
                │
                ├──> fact_equity_returns_daily   [gold]
                └──> panel_sp500_eod             [gold]
```

---

### Future tables (same pattern, not yet DDL)

| Asset class (see `Strategy.md`) | Silver fact | Gold panel |
|---------------------------------|-------------|------------|
| FX G10/EM | `fact_fx_eod` | `panel_fx_eod` |
| Commodities | `fact_commodity_eod` | `panel_commodity_eod` |
| Crypto | `fact_crypto_eod` | `panel_crypto_eod` |
| US macro / consumer | `fact_macro_series` (long) | `panel_macro_daily` (aligned) |

Add rows to `dim_security` with the correct `asset_class`; do not overload `fact_equity_eod` for non-equities.

---

## Bootstrap: S&P 500 via yfinance

**Scope:** one-time YTD daily pull (e.g. `2026-01-01` → today), ~500 tickers.

### Steps

1. **Seed `dim_security`** — load current S&P 500 tickers; set `yf_ticker` = Yahoo symbol (`BRK-B` not `BRK.B`).
2. **Seed `dim_index_constituent`** — `effective_from = '2026-01-01'`, `effective_to = NULL` for bootstrap (refine with point-in-time later).
3. **Open `ingest_run`** — `source='yfinance'`, `dataset='sp500_eod'`, stash `params_json`.
4. **Polars pull** — `yf.download(tickers, start=..., end=..., auto_adjust=False, actions=True)` → normalize columns → bulk insert `forge_bronze.yfinance_equity_eod`.
5. **SQL silver merge** — upsert `fact_equity_eod` from latest bronze run.
6. **SQL gold build** — recompute `fact_equity_returns_daily`, refresh `panel_sp500_eod`.
7. **Close `ingest_run`** — `status='success'`, `row_count`, `finished_at`.

### yfinance → bronze column map (Polars)

```python
# Expected normalized frame before MySQL insert
# columns: run_id, yf_ticker, trade_date, open, high, low, close,
#          adj_close, volume, dividends, stock_splits
```

Use `auto_adjust=False` so `close` and `adj_close` stay distinct in bronze; gold uses `adj_close` for returns.

---

## Polars vs SQL — recommendation

**Use both. Default split:**

| Concern | Tool | Why |
|---------|------|-----|
| DDL, keys, indexes, FKs | **SQL** | Schema is the contract; enforce in MySQL |
| Bronze load from yfinance | **Polars** | Already in `pyproject.toml`; fast vectorized reshape of wide yfinance frames |
| Bronze → silver dedupe/upsert | **SQL** | `INSERT ... ON DUPLICATE KEY UPDATE`, window functions, auditable in HeatWave |
| Silver → gold returns/panels | **SQL** | Set-based, runs on HeatWave columnar store |
| Notebook EDA, feature prototyping | **Polars** | `pl.read_database_uri(...)` on gold; matches `research/` notebooks |
| ORM / execution ledger | **SQLModel** | Stays on SQLite (`forge/execution/state.py`) — separate from warehouse |

**Practical rule:** Polars **ingests and explores**; SQL **defines, merges, and serves**. Do not implement merge logic in Polars if it belongs in a repeatable SQL job — HeatWave cannot run your Python.

**Connect Polars to MySQL** (ingest scripts): `connectorx` or `read_database_uri` / `write_database` with a MySQL URI (`mysql://user:pass@127.0.0.1:3309/forge_bronze`). Batch inserts in chunks (e.g. 50k rows) to avoid packet limits.

**When to prefer SQL only:** incremental daily append (one new `trade_date`), constituent filters, cross-asset joins across fact tables on HeatWave.

**When to prefer Polars only:** ad-hoc transforms in `research/` notebooks, validation checks before promoting logic to `forge/features`.

---

## HeatWave notes

- Replicate **`forge_silver`** and **`forge_gold`** to OCI; bronze can stay local (reprocess from files if needed).
- Load gold fact tables with **primary key `(security_id, trade_date)`** or `(trade_date, security_id)` aligned to filter patterns.
- Run analytics notebooks against HeatWave; keep ingest on local MySQL to limit egress and API coupling.
- Enable HeatWave auto-parallel query for wide `panel_*` scans (Kalman / mean-reversion panels in `Strategy.md`).

---

## Operational checklist

- [ ] Create schemas + DDL (sections above)
- [ ] Seed `dim_security` + `dim_index_constituent` for SP500
- [ ] Bootstrap bronze via yfinance + Polars
- [ ] Run silver merge + gold build SQL
- [ ] Configure HeatWave replication for silver/gold
- [ ] Document `run_id` and `params_json` in `CHANGELOG.md` when promoting ingest to `ingest/`

---

## Related docs

- `forge-docs/Strategy.md` — target asset universe
- `forge-docs/blueprint.md` — ingest → research → `forge/` pipeline
- `native/common/connect_db.hpp` — local MySQL connection defaults
