import logging
import traceback
logging.basicConfig(level=logging.INFO)

from core.extractor import extract_triples
import core.extractor

core.extractor.prompt_template = (
    "Extract scientific triples from the text.\n"
    "Output ONLY a JSON array.\n"
    "Example: [{{\"subject\": \"Electron\", \"predicate\": \"has\", \"object\": \"mass\"}}]\n"
    "Text: {text}\n"
    "JSON:"
)

print("Testing extractor...")
markdown_text = "Quantum computing relies on qubits. Qubits exist in superposition."
try:
    # We patch the chunk code internally by just patching the globals or rewriting.
    # Wait, extract_triples defines `prompt_template` locally! 

markdown_text = "Quantum computing relies on qubits. Qubits exist in superposition."
try:
    triples = extract_triples(markdown_text)
    print("FINAL TRIPLES:", triples)
except Exception as e:
    traceback.print_exc()
