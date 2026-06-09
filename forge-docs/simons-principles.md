# Simons principles (project law)

These override personal tooling preferences (including any desire for a desktop chart UI).

## Do

- **Statistical edges** — signals from models and panels, validated out-of-sample.
- **Systematic execution** — targets and fills keyed by `model_id` + `run_id`.
- **Lineage** — every production artifact pinned to git commit + DVC hash (+ ONNX sidecar).
- **Headless ops** — Dagster, MLflow, CLI, logs, dead-man switches.
- **Many small bets** — diversified targets; risk from covariance and model, not conviction.
- **Promotion by metrics** — `forge.promotion.passes_gate` and `CHANGELOG.md` entries.

## Do not

- **Charts as product** — no PyQt, no dashboards, no manual refresh watchlists.
- **Narrative strategies** — no "philological" strategy docs or promotion prose.
- **Discretionary ledgers** — no named portfolios or human trade tickets without model attribution.
- **Retail snapshot data** — no `yfinance` tickers-for-display as the data plane.
- **Notebook → production shortcut** — notebooks do not ship; `forge/` does.

## Architecture consequence

`init-pyqt6` was removed on branch `simons-pivot`. The only user-facing runtime is `alpha-forge` CLI.
