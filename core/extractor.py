import json
import logging
import gc
from typing import List, Dict, Any
from llama_cpp import Llama
import os

logger = logging.getLogger("Extractor")

def get_config(key: str, default: Any) -> Any:
    """Simple text parsing of settings.yaml since pyyaml is omitted."""
    try:
        with open("configs/settings.yaml", "r") as f:
            for line in f:
                if f"{key}:" in line:
                    val = line.split(":", 1)[1].split("#")[0].strip()
                    if val.isdigit(): return int(val)
                    if val.startswith('"') or val.startswith('\''): return val[1:-1]
                    return val
    except Exception:
        pass
    return default

def chunk_text(text: str, chunk_size: int = 150) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def extract_triples(markdown_text: str) -> List[Dict[str, str]]:
    """Loads SLM, extracts SPO JSON triples, then aggressively unloads SLM."""
    model_path = get_config("model_path", "./data/models/DeepSeek-R1-1.5B-Q4_K_M.gguf")
    n_ctx = get_config("n_ctx", 2048)
    n_threads = get_config("n_threads", 4)
    
    if not os.path.exists(model_path):
        logger.warning(f"Model file {model_path} not found. Returning mock data.")
        return [{"subject": "Model", "predicate": "is", "object": "missing"}]
        
    logger.info(f"Loading LLM {model_path} into memory for extraction.")
    llm = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        verbose=False,
    )
    
    chunks = chunk_text(markdown_text, chunk_size=250)
    all_triples = []
    
    prompt_template = """You are a strictly formal Subject-Predicate-Object JSON extractor. 
Given the physics text, extract the key theoretical relationships as a valid JSON array of objects with keys: "subject", "predicate", "object".
Do NOT output anything other than JSON.
Text: {text}
JSON:"""

    for idx, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {idx+1}/{len(chunks)}")
        prompt = prompt_template.format(text=chunk)
        
        response = llm(
            prompt,
            max_tokens=300,
            stop=["```", "Text:"],
            echo=False
        )
        
        raw_output = response['choices'][0]['text'].strip()
        try:
            start_idx = raw_output.find('[')
            end_idx = raw_output.rfind(']') + 1
            if start_idx != -1 and end_idx != -1:
                triples = json.loads(raw_output[start_idx:end_idx])
                if isinstance(triples, list):
                    for t in triples:
                        if "subject" in t and "predicate" in t and "object" in t:
                            all_triples.append(t)
        except Exception as e:
            logger.warning(f"Failed to parse JSON from SLM: {e}")
            
    # CRITICAL: Resource optimization constraint Section 5.
    logger.info("Unloading SLM and running Garbage Collection.")
    del llm
    gc.collect()
    
    return all_triples
