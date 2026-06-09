# Research gate (notebook → production)

## Stages

| Stage | Location | Ships? |
|-------|----------|--------|
| Experiment | `research/notebooks/` | No |
| Library | `forge/features`, `forge/signals` | Yes (after gate) |
| Registry | MLflow + DVC | Yes |
| Execution | C++ + `forge/execution` | Yes |

## Promotion checklist

1. Feature code lives in `forge/`, imported by notebook (not copied out of notebook).
2. Backtest + OOS metrics recorded in MLflow.
3. `PromotionRecord` passes `forge.promotion.passes_gate`.
4. `CHANGELOG.md` entry with git + DVC + three metrics.
5. Dagster asset check green; ONNX sidecar written.

## Rejected patterns

- Plot-driven discovery without OOS stats.
- Manual UI configuration of models or universes.
- Promotion justified by markdown essay instead of metrics.
