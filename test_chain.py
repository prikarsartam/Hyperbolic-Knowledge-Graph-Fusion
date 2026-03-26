import logging
logging.basicConfig(level=logging.INFO)

from core.parser import parse_pdf_to_text
from core.extractor import extract_triples
from core.embedder import compute_embeddings
from core.aligner import align_and_filter
from core.fusion import execute_pushout_fusion
from api.state import GraphState

import sys
file_path = "data/uploads/PyPhi__A_toolbox_for_integrated_information.pdf"

try:
    text = parse_pdf_to_text(file_path)
    print(f"Parsed {len(text)} characters.")
except Exception as e:
    print(f"Parse error: {e}")
    sys.exit(1)

text = text[:1000] # just process a small part for speed

try:
    triples = extract_triples(text)
    print(f"Extracted {len(triples)} triples.")
except Exception as e:
    print(f"Extraction error: {e}")
    sys.exit(1)

try:
    nodes = compute_embeddings(triples)
    print(f"Embedded {len(nodes)} nodes.")
except Exception as e:
    print(f"Embedding error: {e}")
    sys.exit(1)

print("SUCCESS!")
