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
import re

import pytest

from camel.configs import GeminiConfig
from camel.models import GeminiModel
from camel.types import ModelType
from camel.utils import GeminiTokenCounter


@pytest.mark.model_backend
@pytest.mark.parametrize(
    "model_type",
    [
        ModelType.GEMINI_1_5_FLASH,
        ModelType.GEMINI_1_5_PRO,
    ],
)
def test_anthropic_model(model_type):
    model_config_dict = GeminiConfig().__dict__
    model = GeminiModel(model_type, model_config_dict)
    assert model.model_type == model_type
    assert model.model_config_dict == model_config_dict
    assert isinstance(model.token_counter, GeminiTokenCounter)
    assert isinstance(model.model_type.value_for_tiktoken, str)
    assert isinstance(model.model_type.token_limit, int)


@pytest.mark.model_backend
def test_anthropic_model_unexpected_argument():
    model_type = ModelType.GEMINI_1_5_FLASH
    model_config = GeminiConfig(
        model_path="vicuna-7b-v1.5",
        server_url="http://localhost:8000/v1",
    )
    model_config_dict = model_config.__dict__

    with pytest.raises(
        ValueError,
        match=re.escape(
            (
                "Unexpected argument `model_path` is "
                "input into Anthropic model backend."
            )
        ),
    ):
        _ = GeminiModel(model_type, model_config_dict)