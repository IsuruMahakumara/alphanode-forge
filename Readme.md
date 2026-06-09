
# AlphaNode Forge

Local-first stat-arb research factory (Jim Simons–style pivot). **No dashboard** — notebook plots only.

## Run

```bash
uv sync
uv run python ingest/init_db.py
uv run python ingest/jsonl_to_parquet.py
```

## Repository Structure

```bash
alphanode-forge/
├── CHANGELOG.md
├── datalake/               # flat *.jsonl / *.parquet (gitignored)
├── ingest/                 # python ingest scripts
├── forge/                  # features, signals, execution, promotion gate
├── forge-docs/
├── research/               # lab notebooks (flat)
├── pyproject.toml
└── uv.lock
```

See [forge-docs/blueprint.md](forge-docs/blueprint.md) and [forge-docs/simons-principles.md](forge-docs/simons-principles.md).

## Kernel Port Forwarding

```bash
ssh -N -L 8888:localhost:8888 oci-arm
```
