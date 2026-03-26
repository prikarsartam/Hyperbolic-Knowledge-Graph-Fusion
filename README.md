# Hyperbolic Knowledge Graph Fusion

This localized asynchronous knowledge graph extraction and pushout engine is designed strictly for resource-constrained 16GB CPU-only Ubuntu Linux servers. It converts theoretical physics PDFs into structured knowledge graphs embedded in hyperbolic space.

## System Architecture

The pipeline consists of four localized stages executing sequentially:
1. **Parser Phase**: Academic PDFs -> HTTP POST to `GROBID` -> Strict JSON mapping of LaTeX structural formulas.
2. **Extraction Phase**: Markdown Text Chunks -> 4-Bit GGUF Small Language Model inference via `llama-cpp-python` -> Strict Subject-Predicate-Object (SPO) components. RAM is immediately garbage collected.
3. **Embedding Phase**: Lexical sentence extraction by `SentenceTransformer (MiniLM)` -> Mapping relationships directly into a Riemannian Hyperbolic space via `Gensim PoincareModel`.
4. **Fusion Phase**: Mathematical graph construction via Category Theoretic Pushout -> Equivalence classes contracted over nodes.

## Resource Requirements
- **OS**: Ubuntu Linux (Debian)
- **Engine execution constraints**: CPU-only. Max RAM bound: 16 GB.
- **Dependencies**: Python 3.10+, Java OpenJDK 11+, GCC/CMake.

## Installation Instructions

1. Run the unified installation orchestrator to initialize models, grobid daemon, frontend dependencies, and the python virtual environment:
   ```bash
   ./install.sh
   ```
2. Check `configs/settings.yaml` to modulate memory. Default runs 4 CPU Threads and hard-caps execution at an empirically tested threshold of 12-16GB.

## Usage Guide
Run the orchestrator bash file:
```bash
./start.sh
```
1. Open up `http://localhost:8000` or `http://localhost:3000` depending on the binding.
2. Supply a document and click "Ingest & Pushout".
3. The API queues standard processing internally, parsing via JVM GROBID, passing logic to Llama API, mapping equations via Gensim, and pushing to the WebGL graph.

## Troubleshooting Memory Limit Hits
If the local worker executes `SIGKILL 9` and you observe out-of-bounds termination:
- Lower the inference context size: Change `n_ctx` in `settings.yaml` from 2048 downhill to 1024.
