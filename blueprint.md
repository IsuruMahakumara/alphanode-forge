
---

# Project Blueprint: alphanode-forge

This blueprint reflects the current **PyQt desktop** architecture. The project is no longer centered on a browser UI or containerized web dashboard.

## 1. High-Level Objective

AlphaNode Forge is a local-first trading workstation:

- show live crypto market summaries in a native desktop UI,
- run domain logic from shared Python modules,
- support exploratory analysis in Python notebooks (the Lab).

## 2. Current Architecture (Desktop-First)

### A. UI Layer: `hub/ui` (PyQt6)

- Entry point: `hub/ui/main.py`
- `hub/ui/crypto_dashboard.py` — table UI, background fetch, manual refresh.

### B. Market Data: `hub/crypto_market.py`

- Yahoo Finance fetch via `yfinance` for a fixed list of major crypto tickers.
- No HTTP API layer; UI imports this module directly.

### C. Shared Assets: `forge/`

- Data files and shared domain assets for notebooks and future features.

### D. The Lab: `research/notebooks`

- Jupyter notebooks for plotting, discovery, and ad-hoc analysis.
- Notebooks import from `forge/` and `hub/` where useful; they are not the production runtime.
- **Research-to-production:** reusable logic belongs in `forge/` or `hub/`, then is imported into notebooks—not copied the other way around.

## 3. Repository Structure (Current)

```bash
alphanode-forge/
├── blueprint.md
├── forge/
│   └── data/
├── forge-docs/
├── hub/
│   ├── crypto_market.py
│   └── ui/
│       ├── crypto_dashboard.py
│       └── main.py
├── research/               # The Lab (not shipped with the desktop app)
│   └── notebooks/
├── pyproject.toml
├── Readme.md
└── uv.lock
```

## 4. Runtime and Development Notes

- Primary runtime is local Python via `uv`.
- Desktop launch command:

```bash
uv sync
uv run python -m hub.ui.main
```

- Notebooks: use the same `uv` environment; open `research/notebooks/` in Jupyter or VS Code.
