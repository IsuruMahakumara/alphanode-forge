# Simons principles (project law)

These override personal tooling preferences (including any desire for a desktop chart UI).

## Do

- **Statistical edges** — market-neutral, non-directional signals from panels; validated out-of-sample.
- **Unsupervised first** — clustering, factors, residuals on spreads; supervised only on neutralized targets.
- **Systematic execution** — targets and fills keyed by `model_id` + `run_id`.
- **Lineage** — every production artifact pinned to git commit + data hash.
- **Local data plane** — flat `datalake/` (JSONL + Parquet); MySQL catalog when wired.
- **Many small bets** — diversified neutral baskets; risk from covariance, not conviction.
- **Promotion by metrics** — `forge.promotion.passes_gate` and `CHANGELOG.md` entries.

## Do not

- **Dashboard as product** — no PyQt, no web dashboards, no manual refresh watchlists.
- **Narrative strategies** — no essay strategy docs or promotion prose.
- **Discretionary ledgers** — no named portfolios or human trade tickets without model attribution.
- **Retail snapshot data** — no `yfinance` tickers-for-display as the data plane.
- **Notebook → production shortcut** — notebooks do not ship; `forge/` does.

## Architecture consequence

`hub/` and PyQt were removed on the Simons pivot. Runtime is `ingest/` scripts + notebooks + `forge/`.
