import click

from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.models.config import ProviderConfig


def get_llm_provider(provider_name: str, provider: ProviderConfig) -> LLMProvider:
    """Get LLM Provider"""
    from prich.llm_providers.openai_provider import OpenAIProvider
    from prich.llm_providers.mlx_local_provider import MLXLocalProvider
    from prich.llm_providers.stdin_consumer_provider import STDINConsumerProvider
    from prich.llm_providers.echo_provider import EchoProvider
    from prich.llm_providers.ollama_provider import OllamaProvider

    if provider.provider_type == "openai":
        return OpenAIProvider(provider_name, provider)
    elif provider.provider_type == "stdin_consumer":
        return STDINConsumerProvider(provider_name, provider)
    elif provider.provider_type == "mlx_local":
        return MLXLocalProvider(provider_name, provider)
    elif provider.provider_type == "ollama":
        return OllamaProvider(provider_name, provider)
    elif provider.provider_type == "echo":
        return EchoProvider(provider_name, provider)
    else:
        raise click.ClickException(f"Unsupported LLM provider: {provider.provider_type} - {provider_name}")
