import json
import logging
import gc
import yaml
import os
import re
from typing import List, Dict, Any, Iterator
from llama_cpp import Llama

logger = logging.getLogger("Extractor")

def get_config(key: str, default: Any) -> Any:
    """Load a nested value from settings.yaml using dot-notation key."""
    try:
        with open("configs/settings.yaml", "r") as f:
            config = yaml.safe_load(f)
        keys = key.split(".")
        val = config
        for k in keys:
            val = val[k]
        return val
    except Exception:
        pass
    return default

def chunk_text(text: str, chunk_size: int = 120) -> List[str]:
    """Split text into chunks of approximately chunk_size words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))
    return [c for c in chunks if c.strip()]

def _parse_llm_json(raw: str) -> List[Dict[str, str]]:
    """
    Robustly extract JSON triple arrays from raw LLM output.
    Handles truncated output, extra prose, markdown code fences.
    """
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()

    # Try full parse first
    try:
        start = raw.find('[')
        end = raw.rfind(']')
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(raw[start:end + 1])
            if isinstance(parsed, list):
                return [t for t in parsed
                        if isinstance(t, dict)
                        and "subject" in t and "predicate" in t and "object" in t]
    except Exception:
        pass

    # Fallback: extract individual {...} objects using regex
    triples = []
    for match in re.finditer(r'\{[^{}]+\}', raw):
        try:
            obj = json.loads(match.group())
            if "subject" in obj and "predicate" in obj and "object" in obj:
                triples.append(obj)
        except Exception:
            continue
    return triples

def extract_triples(markdown_text: str) -> Iterator[Dict[str, Any]]:
    """Extracts a list of subject/predicate/object structures using DeepSeek JSON generation iteratively."""
    model_path = get_config("llm.model_path", "./data/models/DeepSeek-R1-1.5B-Q4_K_M.gguf")
    n_ctx      = get_config("llm.n_ctx", 1024)
    import multiprocessing
    # Auto-detect optimal CPU cores, preserving system max
    detected_cores = max(1, multiprocessing.cpu_count() - 1)
    n_threads  = get_config("system.n_threads", detected_cores)
    n_batch    = get_config("llm.n_batch", 256)

    if not os.path.exists(model_path):
        logger.warning(f"Model file {model_path} not found. Returning mock data.")
        yield {"triples": [{"subject": "Model", "predicate": "is", "object": "missing"}], "current_chunk": 1, "total_chunks": 1}
        return

    # 120 words ≈ 160 tokens. Prompt template ≈ 80 tokens. Total ≈ 240 tokens.
    # max_tokens=400 leaves ample room within n_ctx=1024.
    chunks = chunk_text(markdown_text, chunk_size=120)
    total_len = len(chunks)
    if not chunks:
        logger.warning("Empty text passed for extraction.")
        return

    logger.info(f"Loading LLM {model_path} into memory for extraction with {n_threads} threads.")
    llm = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_batch=n_batch,
        n_threads=n_threads,
        verbose=False,
    )

    prompt_template = (
        "List the key subject-predicate-object relationships from this physics text as JSON.\n"
        "Output only a JSON array with keys subject, predicate, object. No prose.\n"
        "Text: {text}\n"
        "JSON:"
    )

    for idx, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {idx + 1}/{total_len}")
        prompt = prompt_template.format(text=chunk)
        
        try:
            response = llm(
                prompt,
                max_tokens=400,
                stop=["Text:", "Extract ", "---"],
                echo=False,
                temperature=0.0,   # Greedy — maximally deterministic JSON output
            )
            raw_output = response['choices'][0]['text'].strip()
            triples = _parse_llm_json(raw_output)
            if triples:
                logger.info(f"  Chunk {idx + 1}: extracted {len(triples)} triples.")
            else:
                logger.warning(f"  Chunk {idx + 1}: no valid triples parsed. Raw: {raw_output[:120]}")
                
            yield {"triples": triples, "current_chunk": idx + 1, "total_chunks": total_len}
        except Exception as e:
            logger.warning(f"  Chunk {idx + 1}: inference failed: {e}")
            yield {"triples": [], "current_chunk": idx + 1, "total_chunks": total_len}

    logger.info("Extraction stream complete. Unloading LLM.")
    del llm
    gc.collect()
