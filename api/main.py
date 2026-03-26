import os
import shutil
import logging
import re
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from pydantic import BaseModel
from typing import Dict, Any
import threading

from api.state import session_state
from core.parser import parse_pdf_to_text
# Removing isolated deprecated extractor import
from core.embedder import compute_embeddings
from core.aligner import align_and_filter
from core.fusion import execute_pushout_fusion

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("API")

app = FastAPI(title="Hyperbolic Knowledge Graph Pushout Engine")
_pipeline_lock = threading.Lock()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/sessions", exist_ok=True)

class PipelineStatus(BaseModel):
    status: str
    message: str

def process_document(file_path: str, filename: str):
    """Sequential blocking pipeline. Lock ensures no concurrent graph corruption."""
    with _pipeline_lock:
        try:
            logger.info(f"Starting processing for {filename}")
            
            markdown_text = parse_pdf_to_text(file_path)
            
            # Incremental pushout updates (Streaming)
            from core.extractor import extract_triples_stream
            for chunk_triples in extract_triples_stream(markdown_text):
                if not chunk_triples:
                    continue
                embedded_nodes = compute_embeddings(chunk_triples)
                if not embedded_nodes:
                    continue
                alignments = align_and_filter(session_state.G, embedded_nodes)
                execute_pushout_fusion(session_state.G, embedded_nodes, alignments)
                
            logger.info("Graph processing fully completed.")
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}", exc_info=True)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
            session_state.enforce_memory_limits()

@app.post("/upload", response_model=PipelineStatus)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Uploads a PDF and queues it for sequential processing."""
    # Sanitize filename: replace spaces with underscores, strip colons and
    # other shell-unsafe characters, keep alphanumerics, dots, dashes, underscores
    safe_name = re.sub(r'[^\w\-.]', '_', file.filename.replace(' ', '_'))
    file_path = f"data/uploads/{safe_name}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    background_tasks.add_task(process_document, file_path, file.filename)
    return JSONResponse(
        status_code=202,
        content={"status": "queued", "message": f"{file.filename} is being processed."}
    )

@app.get("/graph")
def get_graph_state() -> Dict[str, Any]:
    """Returns the serialized JSON of the networkx graph."""
    return session_state.get_graph_data()

@app.post("/reset")
def reset_graph():
    """Resets the continuous session manifold to zero."""
    session_state.reset()
    return {"status": "success", "message": "Graph reset."}

# Mount static frontend
try:
    if os.path.isdir("frontend/dist"):
        app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
    else:
        logger.info("Serving empty static root, compile frontend using 'npm run build'")
except Exception as e:
    logger.error(f"Failed to mount static directory: {e}")
