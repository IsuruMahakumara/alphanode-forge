
# AlphaNode Forge

Native desktop build based on `PyQt6`. Crypto summaries from Yahoo Finance (`yfinance`).

## Run Desktop UI

```bash
uv sync
uv run python -m hub.ui.main
```

## Repository Structure

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
├── pyproject.toml
├── Readme.md
└── uv.lock
```
