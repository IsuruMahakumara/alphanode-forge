

## Alpha Node-Forge: Project Management 

### 1. Core Philosophy

- **Mono-repo & Local-First:** All code (Python scrapers/ML, Dagster orchestration, and documentation) lives in a single Git repository.
    
- **Infrastructure as Code:** No manual UI-based configuration. Every model and data asset is defined as code.
    
- **Zero-Footprint Portability:** Use open standards (Parquet, ONNX) to ensure the stack can move between OCI, GCP, and AWS without lock-in.
    

---

### 2. The "Solo-Pro" Tech Stack

|**Layer**|**Technology**|**Implementation Detail**|
|---|---|---|
|**Orchestration**|**Dagster**|Hosted on **OCI Always Free VM**. Manages the Asset Graph.|
|**Data Lake**|**S3 / OCI Object Storage**|Stores raw and cleaned data in **Parquet** (Hive-partitioned).|
|**Analytics Engine**|**MotherDuck (DuckDB)**|Hybrid local/cloud SQL engine for feature engineering and research.|
|**ML Lifecycle**|**MLflow**|Tracks experiments and serves as a Model Registry.|
|**Execution DB**|**OCI Autonomous DB**|The "Hot Layer" for C++ engine access (Free Tier: 2 instances).|
|**Model Format**|**ONNX**|Standardized format for Python training to C++ inference.|
|**Version Control**|**Git + DVC**|Git for code; DVC for tracking data/model artifact hashes.|

---

### 3. Data & Model Lineage Protocol

To prevent "Lineage Failure," every production model must be pinned to specific hashes:

1. **Code Version:** Git commit hash.
    
2. **Data Version:** DVC hash (representing the state of S3 Parquet at training time).
    
3. **Metadata Sidecar:** A JSON file accompanying the `.onnx` artifact containing feature order and scaling parameters (Mean/Std Dev).
    

---

### 4. Computational Strategy

- **Management (The Brain):** Use **OCI Always Free (Ampere A1)** for the Dagster webserver, daemon, and MLflow (24GB RAM / 4 vCPUs).
    
- **Burst Tasks:** Trigger **GCP Cloud Run Jobs** via Dagster for heavy web-scraping or resource-intensive ML training to leverage GCP's free tier credits.
    
- **Execution (The Forge):** High-performance C++ engine pulls signals and models directly from the OCI Hot Layer and Object Storage.
    

---

### 5. Documentation & Decision Logging

- **Technical Docs:** Use **Obsidian** (Markdown) within the `/docs` folder of the mono-repo. Use bidirectional links to connect philological/trading logic to specific strategies.
    
- **Operational Docs:** Utilize **Dagster Asset Descriptions** and **MLflow Tags** to create a living, searchable lineage graph.
    
- **Decision Log:** Maintain a `CHANGELOG.md` at the root. Every model promotion must record the "Why" (reasoning) linked to a Git commit and DVC hash.
    

---

### 6. Boundary Conditions & Safeguards

- **Data Integrity:** Implement **Dagster Asset Checks** to halt pipelines if scrapers return null values or anomalous price jumps (e.g., CSE corporate actions).
    
- **Hardware Failover:** Maintain a local "Walking Skeleton" (Docker-compose) that can run the full Dagster/DuckDB stack offline in case of connectivity issues.
    
- **Monitoring:** Use a "Dead Man's Switch" (e.g., Healthchecks.io) to monitor the OCI VM heartbeat.