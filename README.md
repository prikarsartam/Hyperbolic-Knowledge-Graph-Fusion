# Hyperbolic Knowledge Graph Fusion

A localized asynchronous knowledge graph extraction and pushout engine designed
for resource-constrained 16GB CPU-only Ubuntu Linux servers. Converts theoretical
physics PDFs into structured knowledge graphs embedded in hyperbolic space.


---

in progress

---

## System Architecture

The pipeline executes four sequential stages:

1. **Parser Phase**: Academic PDFs → HTTP POST to local `GROBID` server →
   Structured Markdown retaining LaTeX formula blocks.
2. **Extraction Phase**: Markdown chunks (250 words) → 4-bit GGUF quantized
   `DeepSeek-R1-1.5B` via `llama-cpp-python` → Strict JSON
   Subject-Predicate-Object triples. LLM is loaded and unloaded per document
   to enforce RAM bounds.
3. **Embedding Phase**: Node terms encoded by `SentenceTransformer (MiniLM-L6-v2)`
   into 384-dim Euclidean vectors. Structural hierarchy mapped into a 10-dim
   Poincaré ball via `Gensim PoincareModel` using Riemannian SGD.
4. **Fusion Phase**: Categorical pushout (colimit) over the session graph.
   Equivalent nodes identified via dual-space alignment (cosine similarity > 0.90
   AND hyperbolic geodesic distance < 0.5) are contracted into equivalence classes
   via `nx.relabel_nodes` + `nx.compose`.

## Resource Requirements

- **OS**: Ubuntu Linux 24.04 (Debian)
- **RAM**: 16 GB minimum. Pipeline is tuned for 12–16 GB active usage.
- **CPU**: x86-64, 4+ cores recommended. GPU not required or used.
- **Java**: OpenJDK 21 JDK (not just JRE) — required to build GROBID from source.
- **Python**: 3.10+
- **Node.js**: 18+

## Installation

### Step 1: Install system dependencies
```bash
sudo apt update
sudo apt install -y build-essential cmake openjdk-21-jdk wget curl unzip xxd
```

### Step 2: Download the LLM model
```bash
bash scripts/fetch_models.sh
```
This downloads `DeepSeek-R1-1.5B-Q4_K_M.gguf` (~900 MB) from HuggingFace and
validates its GGUF magic bytes before accepting it. Re-running is safe and
idempotent — corrupt or missing files are automatically re-fetched.

### Step 3: Build GROBID from source
```bash
bash scripts/install_grobid.sh
```
Clones GROBID and builds via Gradle. Uses `-x` flags to skip Maven publication
tasks that are incompatible with Gradle 9 (`getDependencyProject()` removal).
Re-running is idempotent — skips clone and build if artifacts already exist.

> **Note on Java:** GROBID's build requires JDK 21 (`javac`), not just the JRE.
> If you have `java` but not `javac`, run: `sudo apt install openjdk-21-jdk`

### Step 4: Install frontend dependencies and build
```bash
cd frontend && npm install && cd ..
```

### Step 5: Launch everything
```bash
./start.sh
```
This script:
1. Validates the model file integrity
2. Checks GROBID JAR exists (builds if not)
3. Runs `npm run build` to compile the Vite/TypeScript frontend
4. Creates a Python venv and installs all pip dependencies
5. Starts GROBID on `:8070` and polls `/api/isalive` until ready
6. Starts FastAPI on `:8000` via `python -m uvicorn` (venv-safe invocation)

## Usage

1. Open `http://localhost:8000` in a browser.
2. Select a theoretical physics PDF and click **"Ingest & Pushout"**.
3. The pipeline queues the document for processing. The Sigma.js graph updates
   automatically via 3-second polling once nodes appear.
4. Fused nodes (appearing in multiple documents) are rendered in pink. Unique
   nodes are blue. Node position reflects Poincaré coordinates.
5. Click **Reset** (POST `/reset`) to clear the session graph.

## Troubleshooting

### LLM fails with `invalid magic characters`
The model file is corrupt. Delete it and re-run `bash scripts/fetch_models.sh`.
The script now validates GGUF magic bytes automatically.

### `ModuleNotFoundError: No module named 'fastapi'`
You are calling the system `uvicorn` binary instead of the venv one. Always use:
```bash
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### GROBID build fails: `getDependencyProject()`
This is a Gradle 9 / GROBID dev branch incompatibility. Run:
```bash
cd grobid
./gradlew clean install --no-daemon \
  -x :grobid-trainer:generatePomFileForMavenJavaPublication \
  -x :grobid-trainer:publishMavenJavaPublicationToMavenLocal
```

### RAM limit hit / SIGKILL 9
Reduce `n_ctx` in `configs/settings.yaml` from `1024` to `512`. Also ensure
GROBID is not running a concurrent document while the LLM is loaded — the
`_pipeline_lock` in `api/main.py` serializes this automatically.

### GROBID Gradle shows `94% EXECUTING` forever
This is normal. Gradle's `run` task stays "executing" for the lifetime of the
server process. GROBID is running correctly.
