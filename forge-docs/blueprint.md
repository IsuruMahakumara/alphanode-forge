
---

# Project Blueprint: alphanode-forge (Simons pivot)

Local-first **stat-arb research factory**. No dashboard — notebook plots only.

## 1. High-Level Objective

AlphaNode Forge is a quant pipeline for **market-neutral, non-directional** research:

- ingest raw feeds into flat `datalake/` (JSONL → Parquet via `ingest/`),
- explore in `research/` notebooks (mostly unsupervised),
- promote reusable logic into `forge/` (features, signals, execution ledger).

## 2. Architecture

### A. Ingest: `ingest/`

- Python scripts: `init_db.py`, `jsonl_to_parquet.py`, and future collectors.
- C++ ingest optional later; not required for v1.

### B. Production domain: `forge/`

| Package | Role |
|---------|------|
| `forge/features/` | Feature definitions from cleaned panels |
| `forge/signals/` | Model outputs → neutral weights / spread signals |
| `forge/execution/` | `TargetPosition`, `Fill`, `ModelRun` (SQLModel) |
| `forge/promotion.py` | OOS metrics gate before production |
| `forge/data/` | Local SQLite (`systematic.db`) |

### C. Data: `datalake/`

- Flat files only: `*.jsonl`, `*.parquet` (gitignored).
- MySQL at `localhost:3309` for catalog/metadata — planned, not wired yet.

### D. The Lab: `research/`

- **Non-production.** Flat notebooks; prefix naming per `ipynb-naming.md`.
- Plots in notebooks OK; tables and OOS metrics gate promotion.

## 3. Repository Structure

```bash
alphanode-forge/
├── CHANGELOG.md
├── datalake/
├── ingest/
├── forge/
│   ├── data/             # systematic.db (gitignored)
│   ├── execution/
│   ├── features/
│   ├── signals/
│   └── promotion.py
├── forge-docs/
├── research/
├── pyproject.toml
├── Readme.md
└── uv.lock
```

## 4. Runtime

```bash
uv sync
uv run python ingest/init_db.py
uv run python ingest/jsonl_to_parquet.py datalake/execution.jsonl
```

Notebooks: same `uv` env; kernel local or remote.

## 5. Explicitly Removed (init-pyqt6 → simons-pivot)

- `hub/` (`alpha-forge` CLI)
- `hub/ui/` (PyQt6 crypto dashboard)
- `hub/crypto_market.py` (Yahoo Finance watchlist)
- `forge/data/alpha.db` (discretionary ledger)

## 6. Research-to-Production Path

1. Notebook experiments → extract functions into `forge/features` or `forge/signals`.
2. Backtest + out-of-sample metrics recorded.
3. `PromotionRecord` passes `forge.promotion.passes_gate`.
4. Append row to `CHANGELOG.md` (metrics + git + data hash only).
