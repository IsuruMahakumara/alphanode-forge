
# AlphaNode Forge

Native desktop build based on `PyQt6` for portfolio monitoring and transaction entry.

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
│       └── alpha.db
├── forge-docs/
│   └── Project Management.md
├── hub/
│   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   └── services/
│   └── ui/
│       └── main.py
├── pyproject.toml
├── Readme.md
└── uv.lock
```

