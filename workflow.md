# Hyperbolic KG Pipeline Workflow

## Full Build Workflow

1. Initialize Ubuntu environment:
   ```bash
   sudo apt install -y build-essential cmake openjdk-21-jdk wget curl unzip xxd
   ```
2. Fetch and validate LLM: `bash scripts/fetch_models.sh`
3. Build GROBID (Gradle, uses cached deps on re-run): `bash scripts/install_grobid.sh`
4. Install frontend packages: `cd frontend && npm install && cd ..`
5. Launch all services: `./start.sh`

## Data Flow

- **Input:** PDF file uploaded via browser UI at `http://localhost:8000`.
  POST to `/upload` queues document for background processing.
- **Parse:** PDF sent to GROBID daemon at `localhost:8070/api/processFulltextDocument`.
  Returns TEI XML. Parser extracts `<body>` sections and `<formula>` blocks,
  wrapping equations in `$$ ... $$` markers.
- **Extraction:** Markdown batched into 250-word chunks. Each chunk submitted
  sequentially to DeepSeek-R1-1.5B (Q4_K_M, 4-bit GGUF) via `llama-cpp-python`.
  LLM extracts `{"subject", "predicate", "object"}` JSON arrays.
  Model is explicitly `del`-ed and `gc.collect()`-ed after each document.
- **Embedding:** Subject/object terms encoded by `MiniLM-L6-v2` SentenceTransformer
  into 384-dim Euclidean vectors. Gensim `PoincareModel` trains on SPO relations
  in Riemannian hyperbolic space (10 dims). Full 10-dim Poincaré vector stored
  per node; only dims [0,1] sent to frontend for 2D rendering.
- **Fusion:** Dual-space aligner scans session graph for equivalences:
  cosine similarity > 0.90 AND hyperbolic geodesic distance < 0.5.
  Equivalent nodes merged via categorical pushout: `nx.relabel_nodes` +
  `nx.compose`. Fused nodes receive blended color arrays.
- **Rendering:** Frontend polls `/graph` every 3 seconds. Sigma.js renders nodes
  at Poincaré coordinates scaled to [-100, 100]. Fused nodes (colors.length > 1)
  render pink at size 15; unique nodes render blue at size 8.

## Poincaré Geodesic Distance

The aligner uses the true hyperbolic geodesic metric in the Poincaré ball:

```
d_H(x, y) = arccosh(1 + 2‖x−y‖² / ((1−‖x‖²)(1−‖y‖²)))
```

This is strictly greater than Euclidean distance for all interior points and
diverges to infinity near the boundary of the unit disk, correctly encoding
the exponential growth of hyperbolic space.

## Categorical Pushout

The session graph update is a pushout (colimit) over the span:

```
G_session ← G_overlap → G_new
```

where `G_overlap` is identified by the dual-space aligner. This is implemented
as `nx.relabel_nodes(G_new, equivalence_map)` followed by `nx.compose(G_session, G_new_remapped)`,
which is the correct graph-theoretic realization of the colimit.

## Thread Safety

All document processing is serialized by `_pipeline_lock` (threading.Lock) in
`api/main.py`. Concurrent uploads are accepted by FastAPI but processed strictly
one at a time to prevent concurrent mutation of the session graph singleton.

## RAM Budget (16GB system)

| Component | Peak RAM |
|---|---|
| Ubuntu OS + misc | ~1.5 GB |
| GROBID JVM | ~3–4 GB |
| SentenceTransformer (MiniLM) | ~0.3 GB |
| DeepSeek-R1-1.5B Q4_K_M (n_ctx=1024) | ~1.2 GB |
| Gensim PoincareModel | ~0.2 GB |
| NetworkX session graph | ~0.1–0.5 GB |
| **Total peak** | **~7–10 GB** |

The `ram_limit_gb: 12` soft cap in `settings.yaml` triggers GC before the system
hits actual OOM. The LLM is never resident simultaneously with GROBID XML parsing —
the pipeline is strictly sequential per document.

## File Structure

| Path | Responsibility |
|---|---|
| `core/parser.py` | GROBID HTTP client, TEI XML → Markdown |
| `core/extractor.py` | llama-cpp-python SPO triple extraction |
| `core/embedder.py` | MiniLM + Poincaré dual-space embedding |
| `core/aligner.py` | Hyperbolic geodesic dual-space entity alignment |
| `core/fusion.py` | Categorical pushout graph fusion |
| `api/main.py` | FastAPI server, background task queue, thread lock |
| `api/state.py` | Singleton session graph + RAM monitor |
| `configs/settings.yaml` | All runtime parameters (n_ctx, n_threads, paths) |
| `scripts/fetch_models.sh` | GGUF download + magic byte validation |
| `scripts/install_grobid.sh` | GROBID clone + Gradle build (idempotent) |
| `start.sh` | Full system orchestrator |
