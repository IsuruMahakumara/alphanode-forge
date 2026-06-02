
---

# Project Blueprint: alphanode-forge

This blueprint reflects the current **PyQt desktop** architecture. The project is no longer centered on a browser UI or containerized web dashboard.

## 1. High-Level Objective

AlphaNode Forge is a local-first trading workstation:

- ingest and manage portfolio/transaction data,
- run domain logic from shared Python modules,
- present operational workflows through a native `PyQt6` desktop interface,
- support exploratory analysis in Python notebooks (the Lab).

## 2. Current Architecture (Desktop-First)

### A. UI Layer: `hub/ui` (PyQt6)

- Entry point: `hub/ui/main.py`
- Responsibility:
  - render portfolio and transaction workflows in a native desktop window,
  - capture user actions (create/update operations),
  - call backend services/modules directly within the Python runtime.

### B. Service/Domain Layer: `hub/api` and `forge`

- `hub/api` contains application services, models, and core orchestration logic.
- `forge` contains shared domain/data assets used across the project.
- Responsibility:
  - validate business operations,
  - execute portfolio and transaction logic,
  - persist and query data.

### C. Persistence Layer

- Local data path exists under `forge/data` (for example `alpha.db`).
- The desktop app and service layer use this storage for operational state.

### D. The Lab: `research/notebooks`

- Jupyter notebooks for plotting, discovery, and ad-hoc analysis.
- Notebooks import from `forge/` and `hub/api` where possible; they are not the production runtime.
- **Research-to-production:** logic intended for the desktop app or shared libraries must live in `forge/` (or `hub/api` when app-specific), then be imported into notebooks—not copied the other way around.

## 3. Repository Structure (Current)

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
├── research/               # The Lab (not shipped with the desktop app)
│   └── notebooks/          # Jupyter; imports from forge/
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
- Browser-only dashboard assumptions are deprecated.
- Docker-based two-container split (`scout`/`hub`) is deprecated for the current operating model.
