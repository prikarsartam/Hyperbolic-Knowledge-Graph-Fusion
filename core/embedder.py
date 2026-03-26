import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from gensim.models.poincare import PoincareModel
from api.state import session_state
from core.extractor import get_config

logger = logging.getLogger("Embedder")

model_name    = get_config("embedding.model_name", "all-MiniLM-L6-v2")
poincare_dims = get_config("embedding.poincare_dims", 10)

_st_model = None
def get_st_model():
    global _st_model
    if _st_model is None:
        logger.info(f"Loading SentenceTransformer: {model_name}")
        _st_model = SentenceTransformer(model_name)
    return _st_model

def compute_embeddings(triples: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    """Calculates Semantic (Euclidean) and Structural (Hyperbolic) embeddings."""
    if not triples:
        logger.warning("No triples received — skipping embedding computation.")
        return {}

    logger.info(f"Computing embeddings for {len(triples)} triples.")
    st_model = get_st_model()

    relations = []
    unique_nodes = set()
    node_triples_map = {}

    for t in triples:
        subj = t.get("subject", "").strip()
        obj  = t.get("object", "").strip()
        if subj and obj and subj != obj:
            relations.append((subj, obj))
            unique_nodes.add(subj)
            unique_nodes.add(obj)
            node_triples_map.setdefault(subj, []).append(t)

    unique_nodes = list(unique_nodes)
    if not unique_nodes:
        logger.warning("All triples had empty subject/object — nothing to embed.")
        return {}

    # Lexical semantic embeddings
    lexical_vectors  = st_model.encode(unique_nodes, convert_to_numpy=True)
    lexical_map      = {node: vec for node, vec in zip(unique_nodes, lexical_vectors)}

    # Poincaré hyperbolic embeddings — only train if we have valid non-trivial relations
    if relations and len(unique_nodes) > 2:
        num_negative = min(2, len(unique_nodes) - 1)
        if session_state.poincare_model is None:
            logger.info(f"Initializing new PoincareModel ({poincare_dims} dims, {len(relations)} relations, neg={num_negative}).")
            session_state.poincare_model = PoincareModel(relations, size=poincare_dims, negative=num_negative)
            session_state.poincare_model.train(epochs=50)
        else:
            logger.info(f"Updating PoincareModel with {len(relations)} new relations.")
            session_state.poincare_model.build_vocab(relations, update=True)
            session_state.poincare_model.train(epochs=50)
    else:
        logger.warning(f"Extracted a trivial graph of {len(unique_nodes)} nodes — Poincaré model not trained this batch.")

    # Build output map
    embedded_nodes = {}
    for node in unique_nodes:
        poincare_vec = np.zeros(poincare_dims, dtype=np.float32)
        if (session_state.poincare_model is not None
                and node in session_state.poincare_model.kv.key_to_index):
            raw = session_state.poincare_model.kv[node]
            poincare_vec = np.array(raw, dtype=np.float32)

        # Add small jitter if vector is zero to prevent all nodes collapsing to origin
        if np.allclose(poincare_vec, 0.0):
            poincare_vec = np.random.uniform(-0.05, 0.05, poincare_dims).astype(np.float32)

        coord_2d = (float(poincare_vec[0]), float(poincare_vec[1]))

        embedded_nodes[node] = {
            "lexical_embedding": lexical_map[node],   # kept for aligner; stripped by state.py serializer
            "poincare_coord":    poincare_vec,
            "poincare_coord_2d": coord_2d,
            "label":             node,
            "triples":           node_triples_map.get(node, []),
        }

    logger.info(f"Embedded {len(embedded_nodes)} nodes.")
    return embedded_nodes
