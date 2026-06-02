
---

# Project Blueprint: alphanode-forge

This blueprint defines the dual-container architecture for the research, synthesis, and management layers of the AlphaNode project. 

## 1. High-Level Objective
The **Forge** acts as the intelligence center. It transforms raw market data into trading parameters ("Forging the Edge"). To optimize costs and performance, it is split into two specialized containers deployed on different hardware nodes.

## 2. The Two-Container Architecture

### A. Container 1: `forge-scout` (The Engine)
*   **Target Hardware:** Oracle ARM64 (24GB RAM).
*   **Responsibility:** 
    *   **The CLI:** POSIX-style terminal tool for "Homework" tasks (Scanning).
    *   **The Lab:** Jupyter Notebook environment for data visualization.
    *   **The Replay Agent:** C++-driven backtesting engine used to validate signals against historical DuckDB/Parquet data.
    *   **Model Inference:** Loading `.onnx` model artifacts via ONNX Runtime for live signal generation.
    *   **The Calculus:** Numba/NumPy optimized math libraries.
*   **Why here?** Needs proximity to the **Metal** engine for shared data volumes and massive RAM for historical number crunching.

### B. Container 2: `forge-hub` (The Watchtower)
*   **Target Hardware:** Oracle AMD (1GB RAM).
*   **Responsibility:** 
    *   **The API:** FastAPI server managing state and relaying commands.
    *   **The UI:** Svelte 5 (Runes) dashboard for real-time monitoring.
*   **Why here?** Decouples the UI from the heavy math. Even if the Scout is pinning all 4 ARM cores to 100%, the Dashboard remains responsive on the AMD node.


### C. Supporting Infrastructure: The Data & Model Lake
* **Analytical Storage:** **MotherDuck (DuckDB)** + **S3-Compatible Object Storage** (OCI).
    * **Role:** Acts as the "Cold Path" archive for high-volume Parquet data (historical bars, web-scraped CSE data).
* **Model Registry:** **MLflow**.
    * **Role:** The "Lab Notebook" that tracks model weights (`.onnx`), hyperparameters, and performance metrics across experiments.
* **Data Versioning:** **DVC (Data Version Control)**.
    * **Role:** Links specific Git commits to the raw Parquet data used during training to ensure lineage.

---

## 3. Repository Structure

```bash
alphanode-forge/
├── .devcontainer/          # Unified dev environment for Mac (ARM64)
├── docker/
│   ├── scout.Dockerfile    # Builds the heavy math + CLI image
│   └── hub.Dockerfile      # Builds the slim FastAPI + UI image
├── forge/                  # Shared Core Logic
│   ├── calculus/           # Numba-accelerated math (Z-Scores, Cointegration)
│   ├── cli/                # Typer-based CLI commands
│   └── data/               # Oracle DB and IBKR data handlers
│   └── model/              # Local ONNX registry and Metadata Sidecars
├── forge-docs/             # Obsidian-based Markdown documentation
├── hub/                    # The Web Layer
│   ├── api/                # FastAPI endpoints
│   └── ui/                 # Svelte 5 frontend project
├── research/               # The Lab
│   └── notebooks/          # Exploratory analysis (Imports from forge/)
├── pyproject.toml          # Managed by 'uv' (Rust-based dependency manager)
└── docker-compose.yml      # Orchestrates local testing
```

---

## 4. Technical Requirements for the Coding Agent

### I. Communication Pattern
*   **Statelessness:** The Scout and Hub do not talk to each other directly. They communicate via the **Oracle Autonomous Database**.
*   **Scout Action:** Writes optimized pair parameters to the DB.
*   **Hub Action:** Reads those parameters to display on the UI and allows the user to send "Override" flags back to the DB.

### II. Performance Standards
*   **Cold-Path (Hub):** Focus on async non-blocking I/O to keep the 1GB RAM AMD instance stable.
*   **Hot-Path (Scout):** Use **Numba `@jit`** for all iterative math. Pure Python loops are strictly forbidden in the `calculus/` directory.
*   **Environment:** All Python code must be compatible with **Python 3.11+** and **ARM64** architecture.

### III. The "Research-to-Production" Rule
*   Notebooks in `/research` are for **plotting and discovery only**.
*   Any logic that is intended to be used by the CLI or the C++ engine **must** be refactored into the `forge/` core library and imported into the notebook.

### I. Communication Pattern
* **Transactional (Hot Path):** The Scout and Hub use the **Oracle Autonomous Database** for live command relay and real-time parameter overrides.
* **Analytical (Cold Path):** Historical research and complex feature engineering are handled via **MotherDuck**, querying Parquet files stored in **OCI Object Storage**.
* **Lineage Bridge:** Every model promoted to the Oracle DB must be tagged in **MLflow** with a corresponding Git hash and DVC data version.


---

### Summary of the Distribution

| Container | Image Name | Deploy Location | Resource Profile |
| :--- | :--- | :--- | :--- |
| **Scout** | `an-forge-scout` | Oracle ARM (Node A) | High RAM / High CPU |
| **Hub** | `an-forge-hub` | Oracle AMD (Node B) | Low RAM / Low CPU |
