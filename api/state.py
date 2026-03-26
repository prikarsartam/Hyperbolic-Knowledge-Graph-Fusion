import networkx as nx
import gc
import psutil
import logging
from gensim.models.poincare import PoincareModel
from typing import Optional

logger = logging.getLogger("StateLogger")

class GraphState:
    def __init__(self, ram_limit_gb=10):
        self.G = nx.DiGraph()
        self.poincare_model: Optional[PoincareModel] = None
        self.ram_limit_gb = ram_limit_gb
        
    def reset(self):
        """Wipes the session graph state completely."""
        self.G.clear()
        self.poincare_model = None
        self.enforce_memory_limits()
        logger.info("Session graph completely reset.")

    def enforce_memory_limits(self):
        """Check system RAM and force garbage collection if limits exceeded."""
        ram_usage = psutil.virtual_memory().used / (1024 ** 3)
        if ram_usage > self.ram_limit_gb:
            logger.warning(f"RAM limit exceeded ({ram_usage:.2f}GB / {self.ram_limit_gb}GB). Forcing GC.")
            gc.collect()
            
    def get_graph_data(self):
        """Serialize the continuous NetworkX Graph into a generic JSON struct for Sigma.js."""
        data = nx.node_link_data(self.G)
        return data

# Singleton State instance
session_state = GraphState(ram_limit_gb=12)
