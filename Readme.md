# 🚀 AlphaNode API (alpha-node-api)

**Project Goal:** A high-performance Machine Learning trading backend.  
**Architecture:** Decoupled Backend-only (FastAPI) to be paired with a React-Vite-TSX frontend.

---

## 🛠 Tech Stack
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **ORM:** [SQLModel](https://sqlmodel.tiangolo.com/) (Pydantic + SQLAlchemy integration)
- **Database:** SQLite (Phase 1)
- **Containerization:** Docker & Docker Compose
- **Environment Management:** `uv` 

---

## 📂 Project Structure
Agent should follow this modular layout to ensure scalability:

```text
alpha-node-api/
├── src/
│   ├── main.py             # Entry point & CORS configuration
│   ├── api/                # API Versioning
│   │   └── v1/
│   │       ├── endpoints/  # Route logic
│   │       └── router.py   # Router hub
│   ├── core/               # DB Engine & Global Config
│   ├── models/             # SQLModel Database Tables
│   ├── schemas/            # Pydantic Request/Response Models
│   └── services/           # Business logic & ML Inference
├── data/                   # SQLite persistence (Volume Mount)
├── Dockerfile              # Production-ready Python image
└── docker-compose.yml      # Orchestration for API & Persistence


#### FastAPI Endpoints

- `GET /portfolio` → Returns list of portfolios with positions and totals
- `POST /portfolio/transaction` → Adds a new buy/sell transaction



##🤖 AI Agent Instructions

### 1. Initialize FastAPI
- Create the app instance in `src/main.py` using: `app = FastAPI(title="AlphaNode API")`.
- Configure `CORSMiddleware` specifically to allow `http://localhost:5173` (the default React-Vite origin). 
- Ensure `allow_credentials=True`, `allow_methods=["*"]`, and `allow_headers=["*"]` are set for local development.

### 2. SQLModel Startup & Database
- Define a `create_db_and_tables()` function in `src/core/db.py` that calls `SQLModel.metadata.create_all(engine)`.
- Use the `@app.on_event("startup")` decorator (or the more modern `lifespan` yield context manager) in `main.py` to trigger this function.
- **SQLite Configuration:** Use `sqlite:////app/data/alpha.db` as the connection string. Set `connect_args={"check_same_thread": False}` in the engine creation to support FastAPI's async nature.

### 3. Dependency Injection
- Implement a `get_session` generator function in `src/core/db.py` that yields a `Session(engine)`.
- Apply this as a dependency in all route handlers: `session: Session = Depends(get_session)`.

### 4. Logic Isolation (Services Layer)
- **Constraint:** Route handlers in `src/api/v1/endpoints/` must NOT perform math or complex filtering.
- All "Total Positions" or "Portfolio Valuation" logic must be written as async functions within `src/services/portfolio_service.py`.
- The route handler should call the service, and the service should interact with the database session.

### 5. Dockerization & Permissions
- **Base Image:** Use `python:3.12-slim`.
- **User Security:** Create a non-root user in the Dockerfile.
- **Persistence:** Explicitly `RUN mkdir -p /app/data && chown -R user:user /app/data` to ensure the SQLite driver has write access to the volume-mounted database file.
- **Execution:** Use `uvicorn` or `fastapi run` to serve the app on `0.0.0.0:8000`.