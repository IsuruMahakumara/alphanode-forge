
## Alpha Node-Forge: Project Management (Simons pivot)

### 1. Core Philosophy

- **Headless & no charts:** No PyQt, dashboards, or market watchlists. Runtime is CLI + batch jobs only.
- **Mono-repo & local-first:** Python domain code, Dagster orchestration, and docs in one Git repository.
- **Infrastructure as code:** Models, universes, and data assets defined in code — never configured in a GUI.
- **Systematic ledger:** Positions and fills attributed to `model_id` + `run_id` (`forge/execution`), not discretionary portfolios.
- **Zero-footprint portability:** Parquet, ONNX, and JSON sidecars for cross-cloud moves.

---

### 2. Tech stack

| **Layer** | **Technology** | **Detail** |
|-----------|----------------|------------|
| **Orchestration** | Dagster | OCI Always Free VM; asset graph |
| **Data lake** | S3 / OCI Object Storage | Hive-partitioned Parquet |
| **Analytics** | MotherDuck (DuckDB) | Feature engineering |
| **ML lifecycle** | MLflow | Experiments + registry |
| **Execution DB** | OCI Autonomous DB | Hot layer for C++ engine |
| **Model format** | ONNX | Python train → C++ infer |
| **Version control** | Git + DVC | Code + data/model hashes |
| **Local state** | SQLite (`systematic.db`) | Dev skeleton for runs/positions/fills |

---

### 3. Data & model lineage

Every production model is pinned to:

1. **Code:** Git commit hash.
2. **Data:** DVC hash (Parquet state at train time).
3. **Sidecar:** JSON with feature order and scaling next to `.onnx`.

---

### 4. Computational strategy

- **Brain:** OCI Ampere A1 — Dagster, MLflow.
- **Burst:** GCP Cloud Run via Dagster for heavy train/scrape.
- **Forge:** C++ engine reads signals/models from hot layer + object storage.

---

### 5. Documentation

- **Principles:** `docs/simons-principles.md` — binding project law.
- **Research gate:** `docs/research-gate.md` — notebook → production checklist.
- **Promotions:** Root `CHANGELOG.md` — **metrics + hashes only** (no narrative "why").
- **Operations:** Dagster asset descriptions + MLflow tags for searchable lineage.

Removed: Obsidian links to "philological/trading logic" as a strategy authority.

---

### 6. Safeguards

- **Dagster asset checks** — halt on nulls or anomalous jumps (e.g. CSE corporate actions as data hygiene).
- **Walking skeleton** — local Docker-compose for Dagster/DuckDB offline.
- **Dead man's switch** — Healthchecks.io on OCI VM heartbeat.
- **Promotion gate** — `forge.promotion.passes_gate` before any model touches execution.
