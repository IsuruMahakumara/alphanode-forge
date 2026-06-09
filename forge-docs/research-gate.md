# Research gate (notebook → production)

## Stages

| Stage | Location | Ships? |
|-------|----------|--------|
| Experiment | `research/` | No |
| Ingest | `ingest/` | Yes (scripts) |
| Library | `forge/features`, `forge/signals` | Yes (after gate) |
| Execution | `forge/execution` | Yes |

## Promotion checklist

1. Feature code lives in `forge/`, imported by notebook (not copied out of notebook).
2. Backtest + OOS metrics recorded.
3. `PromotionRecord` passes `forge.promotion.passes_gate`.
4. `CHANGELOG.md` entry with git + data hash + three metrics.

## Rejected patterns

- Plot-driven discovery without OOS stats.
- Manual UI configuration of models or universes.
- Promotion justified by markdown essay instead of metrics.
