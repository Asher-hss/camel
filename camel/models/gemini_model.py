# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
import os
import time
import uuid
from typing import Any, Dict, Optional

import google.generativeai as genai

from camel.configs import Gemini_API_PARAMS, Gemini_Config_PARAMS
from camel.messages import ContentsType
from camel.models import BaseModelBackend
from camel.types import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
    GenerateContentResponse,
    ModelType,
)
from camel.utils import (
    BaseTokenCounter,
    GeminiTokenCounter,
    model_api_key_required,
)


class GeminiModel(BaseModelBackend):
    r"""Gemini API in a unified BaseModelBackend interface."""

    def __init__(
        self,
        model_type: ModelType,
        model_config_dict: Dict[str, Any],
        api_key: Optional[str] = None,
    ) -> None:
        r"""Constructor for Gemini backend.

        Args:
            model_type (ModelType): Model for which a backend is created,
                Gemini-1.5-flash or Gemini-1.5-pro.
            model_config_dict (Dict[str, Any]): A dictionary that will
                be fed into generate_content().
            api_key (Optional[str]): The API key for authenticating with the
                gemini service. (default: :obj:`None`)
        """
        super().__init__(model_type, model_config_dict, api_key)
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        genai.configure(api_key=self._api_key)
        self._client = genai.GenerativeModel(model_type.value)
        self._token_counter: Optional[BaseTokenCounter] = None
        keys = list(self.model_config_dict.keys())
        generation_config_dict = {
            k: self.model_config_dict.pop(k)
            for k in keys
            if k in Gemini_Config_PARAMS
        }
        generation_config = genai.types.GenerationConfig(
            **generation_config_dict
        )
        self.model_config_dict["generation_config"] = generation_config

    @property
    def token_counter(self) -> BaseTokenCounter:
        if not self._token_counter:
            self._token_counter = GeminiTokenCounter(self.model_type)
        return self._token_counter

    @model_api_key_required
    def run(self, contents: ContentsType) -> GenerateContentResponse:
        r"""Runs inference of Gemini model.
        This method can handle multimodal input

        Args:
            contents: Message list or Message with the chat history
            in Gemini API format.
            example: contents = [{'role':'user', 'parts': ['hello']}]


        Returns:
            response(GenerateContentResponse)

        If it is not in streaming mode,
        you can directly output the response.text.

        If it is in streaming mode,
        you can iterate over the response chunks as they become available.
        """
        response = self._client.generate_content(
            contents=self.to_gemini_req(contents),
            **self.model_config_dict,
        )
        response.resolve()
        return self.to_openai_response(response)

    def check_model_config(self):
        r"""Check whether the model configuration contains any
        unexpected arguments to Gemini API.

        Raises:
            ValueError: If the model configuration dictionary contains any
                unexpected arguments to OpenAI API.
        """
        if self.model_config_dict is not None:
            for param in self.model_config_dict:
                if param not in Gemini_API_PARAMS:
                    raise ValueError(
                        f"Unexpected argument `{param}` is "
                        "input into Gemini model backend."
                    )

    @property
    def stream(self) -> bool:
        r"""Returns whether the model is in stream mode,
            which sends partial results each time.
        Returns:
            bool: Whether the model is in stream mode.
        """
        return self.model_config_dict.get('stream', False)

    def to_gemini_req(self, req):
        converted_messages = []
        for message in req:
            role = message.get('role')
            if role == 'assistant':
                role = 'model'
            else:
                role = 'user'
            if 'content' in message:
                converted_message = {
                    "role": role,
                    "parts": message.get("content"),
                }
                converted_messages.append(converted_message)
            else:
                converted_messages.append(message)
        return converted_messages

    def to_openai_response(self, res: GenerateContentResponse):
        openai_res = ChatCompletion(
            id=f"chatcmpl-{uuid.uuid4().hex!s}",
            object="chat.completion",
            created=int(time.time()),
            model="gemini",
            choices=[],
        )
        for i, candidate in enumerate(res.candidates):
            content = ""
            if candidate.content and len(candidate.content.parts) > 0:
                content = candidate.content.parts[0].text
            choice = Choice(
                index=i,
                message=ChatCompletionMessage(
                    role="assistant", content=content
                ),
                finish_reason='stop',
            )
        openai_res.choices.append(choice)
        return openai_res