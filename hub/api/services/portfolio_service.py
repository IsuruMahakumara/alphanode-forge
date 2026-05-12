from sqlmodel import Session, select
from hub.api.models import Portfolio, Transaction


def get_portfolios_with_totals(session: Session) -> list[dict]:
    portfolios = session.exec(select(Portfolio)).all()
    result = []
    for p in portfolios:
        positions: dict[str, float] = {}
        total_value = 0.0
        for t in p.transactions:
            qty = t.quantity if t.side == "buy" else -t.quantity
            positions[t.symbol] = positions.get(t.symbol, 0) + qty
            total_value += t.quantity * t.price * (1 if t.side == "buy" else -1)
        result.append({"id": p.id, "name": p.name, "positions": positions, "total_value": total_value})
    return result


def add_transaction(session: Session, portfolio_id: int, symbol: str, quantity: float, price: float, side: str) -> Transaction:
    # Create portfolio if not exists
    portfolio = session.get(Portfolio, portfolio_id)
    if not portfolio:
        portfolio = Portfolio(id=portfolio_id, name=f"Portfolio {portfolio_id}")
        session.add(portfolio)
        session.commit()
    
    tx = Transaction(portfolio_id=portfolio_id, symbol=symbol, quantity=quantity, price=price, side=side)
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return tx

