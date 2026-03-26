import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from gensim.models.poincare import PoincareModel
from api.state import session_state
from core.extractor import get_config

logger = logging.getLogger("Embedder")

model_name = get_config("embedding.model_name", "all-MiniLM-L6-v2")
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
    logger.info(f"Computing embeddings for {len(triples)} triples.")
    
    st_model = get_st_model()
    
    relations = []
    unique_nodes = set()
    node_triples_map = {}
    
    for t in triples:
        subj, obj = t.get("subject", ""), t.get("object", "")
        if subj and obj:
            relations.append((subj, obj))
            unique_nodes.add(subj)
            unique_nodes.add(obj)
            
            if subj not in node_triples_map: node_triples_map[subj] = []
            node_triples_map[subj].append(t)
            
    unique_nodes = list(unique_nodes)
    if not unique_nodes:
        return {}
        
    # 2. Compute Lexical Semantic Embeddings (Vector Space)
    lexical_vectors = st_model.encode(unique_nodes, convert_to_numpy=True)
    lexical_map = {node: vec for node, vec in zip(unique_nodes, lexical_vectors)}
    
    # 3. Compute Hierarchical Poincaré Embeddings
    if session_state.poincare_model is None:
        logger.info(f"Initializing new PoincareModel with {poincare_dims} dims.")
        session_state.poincare_model = PoincareModel(relations, size=poincare_dims, negative=2)
        session_state.poincare_model.train(epochs=50)
    else:
        logger.info("Updating existing PoincareModel vocabulary.")
        session_state.poincare_model.build_vocab(relations, update=True)
        session_state.poincare_model.train(epochs=50)

    # 4. Construct Output Map
    embedded_nodes = {}
    for node in unique_nodes:
        poincare_vec = np.zeros(poincare_dims, dtype=np.float32)
        if node in session_state.poincare_model.kv.key_to_index:
            poincare_vec = np.array(session_state.poincare_model.kv[node], dtype=np.float32)

        embedded_nodes[node] = {
            "lexical_embedding": lexical_map[node],
            "poincare_coord": poincare_vec,                                  # Full N-dim vector for aligner
            "poincare_coord_2d": (float(poincare_vec[0]), float(poincare_vec[1])),  # For WebGL frontend only
            "label": node,
            "triples": node_triples_map.get(node, [])
        }

    return embedded_nodes
