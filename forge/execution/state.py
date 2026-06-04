"""Systematic ledger: every row ties to model_id and run_id (not named portfolios)."""

from datetime import datetime
from pathlib import Path

from sqlmodel import Field, SQLModel, create_engine

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "systematic.db"


class ModelRun(SQLModel, table=True):
    """One training or inference run pinned to lineage hashes."""

    id: int | None = Field(default=None, primary_key=True)
    model_id: str = Field(index=True)
    git_commit: str
    dvc_hash: str | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)


class TargetPosition(SQLModel, table=True):
    """Model-emitted target weight; not a human trade ticket."""

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="modelrun.id", index=True)
    symbol: str = Field(index=True)
    target_weight: float
    as_of: datetime = Field(default_factory=datetime.utcnow)


class Fill(SQLModel, table=True):
    """Execution feedback linked to the run that produced the target."""

    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="modelrun.id", index=True)
    symbol: str = Field(index=True)
    quantity: float
    price: float
    side: str
    filled_at: datetime = Field(default_factory=datetime.utcnow)


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}")
    SQLModel.metadata.create_all(engine)
