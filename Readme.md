
# AlphaNode Forge

Headless quant research factory (Jim Simons–style pivot). **No charts, no PyQt.**

## Run

```bash
uv sync
uv run alpha-forge status
uv run alpha-forge init-db   # create forge/data/systematic.db schema
```

## Repository Structure

```bash
alphanode-forge/
├── CHANGELOG.md
├── blueprint.md
├── docs/
├── forge/                  # features, signals, execution, promotion gate
├── forge-docs/
├── hub/                    # CLI only
├── research/notebooks/     # Lab (non-production)
├── pyproject.toml
└── uv.lock
```

See [blueprint.md](blueprint.md) and [docs/simons-principles.md](docs/simons-principles.md).

## Kernel Port Forwarding

```bash
ssh -N -L 8888:localhost:8888 oci-arm
```
