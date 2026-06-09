
---

# Project Blueprint: alphanode-forge (Simons pivot)

Headless **research factory + execution state**. No charts, no desktop UI, no retail watchlists.

## 1. High-Level Objective

AlphaNode Forge is a local-first **quant pipeline**:

- ingest and feature-engineer panel data (Parquet / DuckDB upstream),
- train and register models (MLflow + DVC lineage),
- emit **systematic signals** and **target positions** only,
- record fills and runs in a model-attributed ledger (`forge/execution`).

Humans improve models and infrastructure; they do **not** watch markets in a GUI.

## 2. Architecture (Headless)

### A. Runtime CLI: `hub/cli.py`

- Sole shipped entry: `alpha-forge` (no PyQt, no `yfinance` dashboards).
- Commands: `status`, `init-db`.

### B. Production domain: `forge/`

| Package | Role |
|---------|------|
| `forge/features/` | Feature definitions from cleaned panels |
| `forge/signals/` | Model outputs → tradable signals |
| `forge/execution/` | `TargetPosition`, `Fill`, `ModelRun` (SQLModel) |
| `forge/promotion.py` | OOS metrics gate before production |
| `forge/data/` | Local SQLite (`systematic.db`); Parquet via DVC in object storage |

### C. Orchestration (planned, not in-repo yet)

- Dagster asset graph on OCI; MLflow registry; ONNX → C++ execution per `forge-docs/`.

### D. The Lab: `research/notebooks`

- **Non-production.** Reusable logic moves `forge/` → notebooks import it, never the reverse.
- No charts as a product surface; notebooks may print tables/stats for validation only.

## 3. Repository Structure

```bash
alphanode-forge/
├── CHANGELOG.md          # model promotions (metrics + hashes)
├── blueprint.md
├── docs/
│   ├── research-gate.md
│   └── simons-principles.md
├── forge/
│   ├── data/             # systematic.db (gitignored)
│   ├── execution/
│   ├── features/
│   ├── signals/
│   └── promotion.py
├── forge-docs/
│   └── Project Management.md
├── hub/
│   └── cli.py
├── research/
│   └── notebooks/
├── pyproject.toml
├── Readme.md
└── uv.lock
```

## 4. Runtime

```bash
uv sync
uv run alpha-forge status
uv run alpha-forge init-db
```

Notebooks: same `uv` env; `research/notebooks/` on kernel or local.

## 5. Explicitly Removed (init-pyqt6 → simons-pivot)

- `hub/ui/` (PyQt6 crypto dashboard)
- `hub/crypto_market.py` (Yahoo Finance watchlist)
- `forge/data/alpha.db` (discretionary `portfolio` / `transaction` ledger)

## 6. Research-to-Production Path

1. Notebook experiments → extract functions into `forge/features` or `forge/signals`.
2. Backtest + out-of-sample metrics logged in MLflow.
3. `PromotionRecord` passes `forge.promotion.passes_gate`.
4. Append row to `CHANGELOG.md` (metrics + git + DVC only).
5. Dagster promotes ONNX artifact; C++ engine reads hot layer.
