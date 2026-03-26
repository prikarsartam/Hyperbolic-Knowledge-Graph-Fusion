import networkx as nx
import gc
import psutil
import logging
from gensim.models.poincare import PoincareModel
from typing import Optional, Dict, Any, List
import numpy as np

logger = logging.getLogger("StateLogger")

class GraphState:
    def __init__(self, ram_limit_gb=10):
        self.G = nx.DiGraph()
        self.poincare_model: Optional[PoincareModel] = None
        self.ram_limit_gb = ram_limit_gb

    def reset(self):
        self.G.clear()
        self.poincare_model = None
        self.enforce_memory_limits()
        logger.info("Session graph completely reset.")

    def enforce_memory_limits(self):
        ram_usage = psutil.virtual_memory().used / (1024 ** 3)
        if ram_usage > self.ram_limit_gb:
            logger.warning(f"RAM limit exceeded ({ram_usage:.2f}GB / {self.ram_limit_gb}GB). Forcing GC.")
            gc.collect()

    def get_graph_data(self) -> Dict[str, Any]:
        """
        Serialize graph to JSON-safe dict for the frontend.
        Explicitly builds nodes and links arrays.
        Strips lexical_embedding (384-dim, not used by frontend).
        Converts all numpy types to native Python types.
        """
        nodes: List[Dict[str, Any]] = []
        for node_id, data in self.G.nodes(data=True):
            # poincare_coord_2d is what the frontend uses for x/y position
            coord_2d = data.get("poincare_coord_2d", (0.0, 0.0))
            if isinstance(coord_2d, np.ndarray):
                coord_2d = (float(coord_2d[0]), float(coord_2d[1]))
            elif isinstance(coord_2d, (list, tuple)) and len(coord_2d) >= 2:
                coord_2d = (float(coord_2d[0]), float(coord_2d[1]))
            else:
                coord_2d = (0.0, 0.0)

            colors = data.get("colors", [1])
            if not isinstance(colors, list):
                colors = [1]

            nodes.append({
                "id": str(node_id),
                "label": str(data.get("label", node_id)),
                "poincare_coord": list(coord_2d),
                "colors": colors,
            })

        links: List[Dict[str, Any]] = []
        for src, dst, edata in self.G.edges(data=True):
            links.append({
                "source": str(src),
                "target": str(dst),
                "label": str(edata.get("label", "")),
            })

        return {
            "directed": True,
            "nodes": nodes,
            "links": links,
        }

# Singleton
session_state = GraphState(ram_limit_gb=12)
