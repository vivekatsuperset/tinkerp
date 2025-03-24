from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from symmetri.utils import sanitize_json_string


class LLMResponse(object):

    def __init__(self, content: str, input_tokens: int, output_tokens: int):
        self.content = content
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class LLMJSONResponse(object):

    def __init__(self, content: dict[str, Any] | list[dict[str, Any]],
                 input_tokens: int, output_tokens: int):
        self.content = content
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class LLM(ABC):

    def __init__(self, name: str, llm_model: str, embedding_model: str):
        self.name = name
        self.llm_model_name = llm_model
        self.embedding_model = embedding_model

    @abstractmethod
    def get_embeddings(self, text: list[str]) -> list[np.array]:
        raise NotImplementedError()

    @abstractmethod
    def get_response(self, user_prompts: list[str], system_prompts: list[str] = None) -> LLMResponse:
        raise NotImplementedError()

    def get_json_response(self, user_prompts: list[str], system_prompts: list[str] = None) -> LLMJSONResponse:
        response = self.get_response(user_prompts, system_prompts)

        return LLMJSONResponse(
            content=sanitize_json_string(response.content.strip()),
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens
        )
