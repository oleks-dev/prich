from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Tuple


class BaseProviderModel(BaseModel):
    name: str | None = Field(default=None, exclude=True)  # will be injected
    mode: Optional[str] = None

    def model_post_init(self, __context):
        if self.name is None and __context and "__name" in __context:
            self.name = __context["__name"]


class EchoProviderModel(BaseProviderModel):
    provider_type: Literal["echo"]
    model: Literal[None] = None
    mode: Optional[str] = None


class OpenAIProviderModel(BaseProviderModel):
    provider_type: Literal["openai"]
    mode: Optional[str] = None
    api_endpoint: str
    api_key: str
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class MLXLocalProviderModel(BaseProviderModel):
    provider_type: Literal["mlx_local"]
    mode: Optional[str] = None
    model_path: str

    # generate
    #
    # The maximum number of tokens. Use``-1`` for an infinite
    #      generator. Default: ``256``.
    max_tokens: Optional[int] = None
    # Maximum size of the key-value cache. Old
    #           entries (except the first 4 tokens) will be overwritten.
    max_kv_size: Optional[int] = None
    # Step size for processing the prompt.
    #         kv_bits (int, optional): Number of bits to use for KV cache quantization.
    #           None implies no cache quantization. Default: ``None``.
    prefill_step_size: Optional[int] = None
    # Number of bits to use for KV cache quantization.
    #           None implies no cache quantization. Default: ``None``.
    kv_bits: Optional[int] = None
    # Group size for KV cache quantization. Default: ``64``.
    kv_group_size: Optional[int] = None
    # Step to begin using a quantized KV cache.
    #            when ``kv_bits`` is non-None. Default: ``0``.
    quantized_kv_start: Optional[int] = None

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
    # The probability of applying XTC
    #             sampling.
    xtc_probability: Optional[float] = None
    # The threshold the probs need to reach
    #             for being sampled.
    xtc_threshold: Optional[float] = None
    # List of special tokens IDs to
    #             be excluded from XTC sampling.
    xtc_special_tokens: Optional[list[float]] = None

class STDINConsumerProviderModel(BaseProviderModel):
    provider_type: Literal["stdin_consumer"]
    model: Literal[None] = None
    mode: Optional[str] = None
    cmd: Optional[str] = None
    args: Optional[List[str]] = None
    stdout_strip_prefix: Optional[str] = None
    stdout_slice: Optional[Tuple[Optional[int], Optional[int]]] = None
