from symmetri.llms.anthropic_llm import Claude
from symmetri.llms.base import LLM
from symmetri.llms.openai_llm import OpenAIGPT

LLM_CONFIG = {
    "openai": {
        "models": ["gpt-4o", "gpt-4o-mini"],
        "embedding": {
            "model": "text-embedding-3-small",
            "vector_length": 1536
        }
    },
    "anthropic": {
        "models": ["claude-3-7-sonnet-latest", "claude-3-5-haiku-latest"],
        "embedding": {
            "model": "voyage-3",
            "vector_length": 1024
        }
    }
}


def get_llm_instance(name: str, model: str) -> LLM:
    llm_config_entry = LLM_CONFIG.get(name, None)
    if llm_config_entry is None:
        raise ValueError("Unknown LLM provider '%s'" % name)

    llm_models = llm_config_entry["models"]
    if model not in llm_models:
        raise ValueError("Unknown model '%s' for LLM '%s'" % (model, name))

    embedding_model = llm_config_entry["embedding"]["model"]

    if name == "openai":
        return OpenAIGPT(
            llm_model=model,
            embedding_model=embedding_model
        )
    elif name == "anthropic":
        return Claude(
            llm_model=model,
            embedding_model=embedding_model
        )
    else:
        raise ValueError("Unknown LLM provider '%s'" % name)
