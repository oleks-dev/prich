from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional, List, Tuple


class BaseProviderModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str | None = Field(default=None, exclude=True)  # will be injected
    mode: Optional[str] = None

    def model_post_init(self, __context):
        if self.name is None and __context and "__name" in __context:
            self.name = __context["__name"]


class EchoProviderModel(BaseProviderModel):
    provider_type: Literal["echo"]


class OpenAIProviderModel(BaseProviderModel):
    provider_type: Literal["openai"]
    configuration: dict
    options: dict


class MLXLocalProviderModel(BaseProviderModel):
    provider_type: Literal["mlx_local"]
    model_path: str

    # generate
    #
    # The maximum number of tokens. Use``-1`` for an infinite
    #      generator. Default: ``256``.
    max_tokens: Optional[int] = None

    # sampler
    #
    # The temperature for sampling, if 0 the argmax is used.
    #           Default: ``0``.
    temp: Optional[float] = None
    # Nulceus sampling, higher means model considers
    #           more less likely words.
    top_p: Optional[float] = None
    # The minimum value (scaled by the top token's
    #           probability) that a token probability must have to be considered.
    min_p: Optional[float] = None
    # Minimum number of tokens that cannot
    #           be filtered by min_p sampling.
    min_tokens_to_keep: Optional[int] = None
    # The top k tokens ranked by probability to constrain
    #           the sampling to.
    top_k: Optional[int] = None

class STDINConsumerProviderModel(BaseProviderModel):
    provider_type: Literal["stdin_consumer"]
    call: str = None
    args: Optional[List[str]] = None

class OllamaProviderModel(BaseProviderModel):
    provider_type: Literal["ollama"]
    model: str
    base_url: Optional[str] = None
    options: Optional[dict] = None
    stream: Optional[bool] = None
    suffix: Optional[str] = None
    template: Optional[str] = None
    raw: Optional[bool] = None
    format: Optional[dict | str] = None
    think: Optional[bool] = None
