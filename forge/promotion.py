"""Model promotion gate — metrics and hashes only (no narrative 'why')."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionRecord:
    model_id: str
    git_commit: str
    dvc_hash: str
    oos_sharpe: float
    max_drawdown: float
    turnover: float


def passes_gate(record: PromotionRecord) -> bool:
    """Minimum bar before a model may touch production execution."""
    return (
        record.oos_sharpe > 0
        and record.max_drawdown < 0.25
        and 0 < record.turnover < 5.0
    )
