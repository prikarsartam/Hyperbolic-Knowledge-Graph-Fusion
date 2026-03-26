import pytest
import numpy as np
import networkx as nx
import json
from core.aligner import poincare_distance, align_and_filter
from core.fusion import execute_pushout_fusion
from core.extractor import chunk_text
from api.state import GraphState

# Helper: build a mock embedded_nodes dict
def make_node(name, vec=None, poincare=None):
    vec = vec if vec is not None else np.zeros(384, dtype=np.float32)
    poincare = poincare if poincare is not None else np.zeros(10, dtype=np.float32)
    return {
        "lexical_embedding": vec,
        "poincare_coord": poincare,
        "poincare_coord_2d": (float(poincare[0]), float(poincare[1])),
        "label": name,
        "triples": [{"subject": name, "predicate": "relates_to", "object": "Physics"}],
        "colors": [1]
    }

# ---- poincare_distance ----
def test_poincare_distance_self_is_zero():
    p = np.array([0.1, 0.2] + [0.0]*8, dtype=np.float32)
    assert poincare_distance(p, p) == pytest.approx(0.0, abs=1e-5)

def test_poincare_distance_symmetry():
    p1 = np.array([0.1, 0.2] + [0.0]*8, dtype=np.float32)
    p2 = np.array([0.3, 0.1] + [0.0]*8, dtype=np.float32)
    assert poincare_distance(p1, p2) == pytest.approx(poincare_distance(p2, p1), rel=1e-5)

def test_poincare_distance_exceeds_euclidean():
    p1 = np.array([0.5, 0.0] + [0.0]*8, dtype=np.float32)
    p2 = np.array([0.0, 0.5] + [0.0]*8, dtype=np.float32)
    assert poincare_distance(p1, p2) > float(np.linalg.norm(p1 - p2))

def test_poincare_distance_near_boundary_is_large():
    p1 = np.array([0.99, 0.0] + [0.0]*8, dtype=np.float32)
    p2 = np.array([-0.99, 0.0] + [0.0]*8, dtype=np.float32)
    assert poincare_distance(p1, p2) > 5.0

# ---- chunk_text ----
def test_chunk_text_exact_split():
    text = " ".join(["word"] * 500)
    chunks = chunk_text(text, chunk_size=250)
    assert len(chunks) == 2
    assert all(len(c.split()) <= 250 for c in chunks)

def test_chunk_text_small_input_single_chunk():
    text = "Quantum mechanics governs atomic scale behavior."
    assert len(chunk_text(text, chunk_size=250)) == 1

# ---- execute_pushout_fusion ----
def test_fusion_empty_session_populates_graph():
    G = nx.DiGraph()
    nodes = {"Hamiltonian": make_node("Hamiltonian"), "Quantum System": make_node("Quantum System")}
    nodes["Hamiltonian"]["triples"] = [{"subject": "Hamiltonian", "predicate": "describes", "object": "Quantum System"}]
    execute_pushout_fusion(G, nodes, [])
    assert "Hamiltonian" in G.nodes
    assert G.has_edge("Hamiltonian", "Quantum System")

def test_fusion_merges_equivalent_nodes():
    G = nx.DiGraph()
    G.add_node("Hamiltonian", **make_node("Hamiltonian"), colors=[1])
    new_nodes = {"H_op": make_node("H_op")}
    new_nodes["H_op"]["colors"] = [2]
    execute_pushout_fusion(G, new_nodes, [("H_op", "Hamiltonian")])
    assert "Hamiltonian" in G.nodes
    assert 2 in G.nodes["Hamiltonian"].get("colors", [])
    assert "H_op" not in G.nodes

# ---- GraphState JSON serialization ----
def test_get_graph_data_is_json_serializable():
    state = GraphState(ram_limit_gb=16)
    state.G.add_node("Node1", **make_node("Node1"))
    data = state.get_graph_data()
    serialized = json.dumps(data)  # Must not raise
    assert "Node1" in serialized

def test_get_graph_data_no_numpy_in_output():
    state = GraphState(ram_limit_gb=16)
    state.G.add_node("Node1", **make_node("Node1"))
    data = state.get_graph_data()
    for node in data["nodes"]:
        for val in node.values():
            assert not isinstance(val, np.ndarray), f"numpy array found in serialized output for key"
