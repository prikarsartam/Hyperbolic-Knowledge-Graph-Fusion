import logging
from llama_cpp import Llama

logging.basicConfig(level=logging.INFO)
llm = Llama(model_path="./data/models/DeepSeek-R1-1.5B-Q4_K_M.gguf", n_ctx=1024, verbose=False)
prompt = "Format: [{\"subject\": \"X\", \"predicate\": \"Y\", \"object\": \"Z\"}]\nText: Physics is a science.\nJSON:"
try:
    response = llm(prompt, max_tokens=100, temperature=0.0)
    print("LLM RESPONSE:", response)
    print("FINAL PARSED TEXT:", response['choices'][0]['text'])
except Exception as e:
    import traceback
    traceback.print_exc()
