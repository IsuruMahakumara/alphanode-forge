from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel


class Portfolio(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    transactions: list["Transaction"] = Relationship(back_populates="portfolio")


class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    portfolio_id: int = Field(foreign_key="portfolio.id")
    symbol: str
    quantity: float
    price: float
    side: str  # "buy" or "sell"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    portfolio: Portfolio | None = Relationship(back_populates="transactions")

