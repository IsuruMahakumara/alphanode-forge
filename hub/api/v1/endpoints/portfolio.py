from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session
from hub.api.core.db import get_session
from hub.api.services.portfolio_service import add_transaction, get_portfolios_with_totals

router = APIRouter()


class TransactionCreate(BaseModel):
    portfolio_id: int
    symbol: str
    quantity: float
    price: float
    side: str


@router.get("/portfolio")
def list_portfolios(session: Session = Depends(get_session)):
    return get_portfolios_with_totals(session)


@router.post("/portfolio/transaction")
def create_transaction(tx: TransactionCreate, session: Session = Depends(get_session)):
    return add_transaction(session, tx.portfolio_id, tx.symbol, tx.quantity, tx.price, tx.side)

