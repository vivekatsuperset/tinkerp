import os

import anthropic
import numpy as np
import voyageai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from symmetri.llms.base import LLM, LLMResponse


class Claude(LLM):

    def __init__(self, llm_model: str, embedding_model: str):
        super().__init__(name='anthropic', llm_model=llm_model, embedding_model=embedding_model)
        self.client = anthropic.Anthropic(
            api_key=os.environ['CLAUDE_API_KEY'],
        )
        self.voyage_client = voyageai.Client(
            api_key=os.environ['VOYAGEAI_API_KEY']
        )

    @retry(wait=wait_random_exponential(min=0.2, max=1), stop=stop_after_attempt(3))
    def get_embeddings(self, text: list[str]) -> list[np.array]:
        formatted_text = [t.replace("\n", " ") for t in text]
        result = self.voyage_client.embed(
            formatted_text,
            model=self.embedding_model,
            input_type='document'
        )
        embeddings = list[np.array]()
        for embedding in result.embeddings:
            embeddings.append(np.array(embedding))
        return embeddings

    @retry(wait=wait_random_exponential(min=0.1, max=0.5), stop=stop_after_attempt(3))
    def get_response(self, user_prompts: list[str], system_prompts: list[str] = None) -> LLMResponse:
        messages = self.get_messages_for_llm_request(user_prompts)
        response_message = self.client.messages.create(
            model=self.llm_model_name,
            max_tokens=1024*4,
            messages=messages,
            system='\n'.join(system_prompts) if system_prompts is not None else None
        )
        final_response = []
        for c in response_message.content:
            if c.type == "text":
                final_response.append(c.text)
        return LLMResponse(
            content='\n'.join(final_response),
            input_tokens=response_message.usage.input_tokens,
            output_tokens=response_message.usage.output_tokens
        )

    def get_messages_for_llm_request(self, user_prompts: list[str]) -> list[dict[str, str]]:
        messages = list[dict[str, str]]()
        if user_prompts is not None and len(user_prompts) > 0:
            [
                messages.append(
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ) for user_prompt in user_prompts
            ]
        return messages
