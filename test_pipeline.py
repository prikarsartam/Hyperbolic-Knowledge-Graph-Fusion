import logging
logging.basicConfig(level=logging.INFO)
import api.main
from api.state import session_state

pdf_path = "data/uploads/PyPhi__A_toolbox_for_integrated_information.pdf"
api.main.process_document(pdf_path, "PyPhi.pdf")

print("GRAPH DATA:")
import json
print(json.dumps(session_state.get_graph_data(), indent=2))
