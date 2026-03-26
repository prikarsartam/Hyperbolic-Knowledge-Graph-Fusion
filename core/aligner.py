import logging
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.spatial.distance import cosine

logger = logging.getLogger("Aligner")

def poincare_distance(p1: np.ndarray, p2: np.ndarray) -> float:
    """Correct hyperbolic geodesic distance in the Poincaré ball model."""
    norm1_sq = float(np.dot(p1, p1))
    norm2_sq = float(np.dot(p2, p2))
    diff_sq  = float(np.dot(p1 - p2, p1 - p2))
    denom = max((1.0 - norm1_sq) * (1.0 - norm2_sq), 1e-8)
    arg   = max(1.0 + 2.0 * diff_sq / denom, 1.0)  # Clamp for arccosh domain
    return float(np.arccosh(arg))

def align_and_filter(session_graph, embedded_nodes: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
    """Generates equivalence sets based on UMEAD-style dual-space metric overlaps."""
    mappings = []
    
    if len(session_graph.nodes) == 0:
        logger.info("Session graph empty. No alignment matrix needed.")
        return mappings

    logger.info("Computing UMEAD-style cosine and poincaré alignments.")
    
    # Simple linear scan. For 1000s of nodes we'd use FAISS or Annoy, but we have strict CPU limits.
    for new_id, new_data in embedded_nodes.items():
        v1 = new_data["lexical_embedding"]
        p1 = np.asarray(new_data["poincare_coord"], dtype=np.float32)
        
        best_match = None
        best_score = 0.0
        
        for sess_id, sess_data in session_graph.nodes(data=True):
            if "lexical_embedding" not in sess_data:
                continue
                
            v2 = sess_data["lexical_embedding"]
            p2 = np.asarray(sess_data["poincare_coord"], dtype=np.float32)
            if p1.shape != p2.shape:
                continue
            
            # 1. Cosine similarity threshold > 0.90
            cos_sim = 1 - cosine(v1, v2)
            if cos_sim > 0.90:
                # 2. Hyperbolic filtering: distance in bounded map
        
                dist = poincare_distance(p1, p2)
                if dist < 0.5:  # Threshold in hyperbolic distance units
                    if cos_sim > best_score:
                        best_score = cos_sim
                        best_match = sess_id
                        
        if best_match is not None:
            mappings.append((new_id, best_match))
            
    logger.info(f"Generated {len(mappings)} equivalence mappings.")
    return mappings
