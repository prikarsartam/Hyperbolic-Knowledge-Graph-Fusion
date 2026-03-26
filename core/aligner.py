import logging
import numpy as np
from typing import Dict, Any, List, Tuple
from scipy.spatial.distance import cosine

logger = logging.getLogger("Aligner")

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
        p1 = np.array(new_data["poincare_coord"])
        
        best_match = None
        best_score = 0.0
        
        for sess_id, sess_data in session_graph.nodes(data=True):
            if "lexical_embedding" not in sess_data:
                continue
                
            v2 = sess_data["lexical_embedding"]
            p2 = np.array(sess_data["poincare_coord"])
            
            # 1. Cosine similarity threshold > 0.90
            cos_sim = 1 - cosine(v1, v2)
            if cos_sim > 0.90:
                # 2. Hyperbolic filtering: distance in bounded map
        
                dist = np.linalg.norm(p1 - p2)
                if dist < 0.2:  # Bounding box constraint
                    if cos_sim > best_score:
                        best_score = cos_sim
                        best_match = sess_id
                        
        if best_match is not None:
            mappings.append((new_id, best_match))
            
    logger.info(f"Generated {len(mappings)} equivalence mappings.")
    return mappings
