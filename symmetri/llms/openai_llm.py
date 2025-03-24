import os
import traceback

import numpy as np
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from symmetri.llms.base import LLM, LLMResponse


class OpenAIGPT(LLM):

    def __init__(self, llm_model: str, embedding_model: str):
        super().__init__(name='openai', llm_model=llm_model, embedding_model=embedding_model)
        openai.api_key = os.environ["OPENAI_API_KEY"]
        self.client = openai.OpenAI()

    @retry(wait=wait_random_exponential(min=0.2, max=1), stop=stop_after_attempt(3))
    def get_embeddings(self, text: list[str]) -> list[np.array]:
        formatted_text = [t.replace("\n", " ") for t in text]
        embeddings = list[np.array]()
        try:
            response = self.client.embeddings.create(
                input=formatted_text,
                model=self.embedding_model
            )
            for d in response.data:
                embeddings.append(np.array(d.embedding))
        except openai.BadRequestError as e:
            traceback.print_exc()
            print(text)

        return embeddings

    @retry(wait=wait_random_exponential(min=0.1, max=0.5), stop=stop_after_attempt(3))
    def get_response(self, user_prompts: list[str], system_prompts: list[str] = None) -> LLMResponse:
        messages = self.get_messages_for_llm_request(user_prompts, system_prompts)
        response = self.client.chat.completions.create(
            model=self.llm_model_name,
            messages=messages,
            temperature=0
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens
        )

    def get_messages_for_llm_request(self, user_prompts: list[str], system_prompts: list[str] = None) -> list[dict[str, str]]:
        messages = list[dict[str, str]]()
        if system_prompts is not None and len(system_prompts) > 0:
            [
                messages.append(
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ) for system_prompt in system_prompts
            ]
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
