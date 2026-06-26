
## Alpha Node-Forge: Project Management (Simons pivot)

### 1. Core Philosophy

- **No dashboard:** Notebook plots OK; no PyQt, web UI, or watchlists.
- **Mono-repo & local-first:** Python ingest, notebooks, and `forge/` in one Git repo.
- **Flat layout:** `datalake/`, `ingest/`, `research/` — no deep nesting.
- **Systematic ledger:** Positions and fills attributed to `model_id` + `run_id` (`forge/execution`).
- **Stat arb focus:** Market-neutral, unsupervised-first research.

---

### 2. Tech stack (v1)

| **Layer** | **Technology** | **Detail** |
|-----------|----------------|------------|
| **Data lake** | `datalake/` | Flat JSONL + Parquet (gitignored) |
| **Ingest** | `ingest/*.py` | JSONL → Parquet, DB init |
| **Analytics** | Polars + notebooks | Research in `research/` |
| **ML** | scikit-learn (dev) | Unsupervised clustering / PCA |
| **Local state** | SQLite (`systematic.db`) | Runs, positions, fills |
| **Catalog** | MySQL `:3309` | Planned metadata store |

Cloud orchestration (Dagster, MLflow, S3, ONNX) is **out of v1 scope**.

---

### 3. Data & model lineage

Every promoted model is pinned to:

1. **Code:** Git commit hash.
2. **Data:** Parquet snapshot path or hash at train time.

---

### 4. Documentation

- **Principles:** `forge-docs/simons-principles.md`
- **Research gate:** `forge-docs/research-gate.md`
- **Notebook naming:** `research/ipynb-naming.md`
- **Promotions:** root `CHANGELOG.md` — metrics + hashes only

---

### 5. Safeguards

- **Promotion gate** — `forge.promotion.passes_gate` before execution.
- **Research gate** — no notebook → production without OOS metrics.
