# Hyperbolic KG Pipeline Workflow

## Full Build Workflow
1. Initialize a blank Ubuntu environment.
2. `sudo apt-get update && sudo apt-get install build-essential cmake openjdk-11-jdk wget curl unzip`
3. Run the installation script: `./install.sh`
4. Start daemons: `./start.sh`

## Data Flow
- **Input:** Single byte-stream POST to `/upload` FastAPI.
- **Parse:** Passed to `localhost:8070` GROBID daemon. Returned as structured XML. Parser isolates `<formula>` logic blocks wrapping them in LaTeX.
- **Extraction:** Raw Markdown batched into 250 word semantic fragments. Submitted sequentially to a Q4 parameter quantized instance `llama-cpp`. GGUF structure parsed out into `{"subject": "A", "predicate": "B", "object": "C"}` JSON arrays.
- **Embedding:** Node subjects/objects instantiated. MiniLM model bounds them lexically in Euclidean mappings. Gensim initializes Riemannian Poincare geometry dynamically.
- **Fusion:** Disjoint-set maps over existing `$G_{session}$` network space matching high similarities (>0.90 cosine) inside bounding Poincare radiuses. Disjoint nodes generated -> equivalences unified by quotient pushout mappings. Shaders blend colors array dynamically.

## Agent Decision Flow
- **New nodes vs Matched nodes**: If a node aligns strictly via the dual-space aligner, the disjoint union merges them explicitly assigning equivalence. If unique, the semantic hierarchy pushes the Poincare coordinate peripherally.

## File Structure & Math Maps
- Top level category theoretic topology -> `core/fusion.py`
- Neural Euclidean/Hyperbolic mapping -> `core/embedder.py`
- Zero-shot linguistic abstraction extraction -> `core/extractor.py`

## Updating Mechanism
Any sequential update (`update=True`) invokes Gensim's Riemann SGD algorithm mathematically retaining foundational centroid physics embeddings while allowing new terminology nodes to structure safely radially outwards without breaking existing vectors.

## Mathematical Notes

### Poincaré Geodesic Distance
The aligner uses the true geodesic distance in the Poincaré ball model:

$$d_H(x, y) = \cosh^{-1} \!\left( 1 + \frac{2\|x - y\|^2}{(1 - \|x\|^2)(1 - \|y\|^2)} \right)$$

All alignment thresholds are in hyperbolic distance units. The threshold `0.5`
was empirically calibrated on physics entity pairs.

### Pushout Fusion
The session graph update implements a categorical pushout (colimit) over the span:
  G_session ← G_overlap → G_new
where G_overlap is identified by the dual-space aligner. Equivalent nodes are
contracted via nx.relabel_nodes followed by nx.compose — the correct graph-
theoretic implementation of the pushout colimit.

### Full-Dimensional Poincaré Embeddings
The Poincaré model trains with poincare_dims=10. All 10 dimensions are stored in
`poincare_coord` and used by the aligner for geometric proximity filtering.
Only `poincare_coord_2d = (vec[0], vec[1])` is forwarded to the WebGL frontend.

### Thread Safety
Document processing is serialized by _pipeline_lock (threading.Lock). Concurrent
uploads are accepted by FastAPI but processed strictly sequentially to protect
the mutable session graph singleton.
