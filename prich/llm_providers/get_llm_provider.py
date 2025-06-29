import click
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.models.config import ProviderConfig


def get_llm_provider(provider_name: str, provider: ProviderConfig) -> LLMProvider:
    """Get LLM Provider"""
    from prich.llm_providers.openai_provider import OpenAIProvider
    from prich.llm_providers.mlx_local_provider import MLXLocalProvider
    from prich.llm_providers.q_chat_cli_provider import QChatCLIProvider
    from prich.llm_providers.echo_provider import EchoProvider

    if provider.provider_type == "openai":
        return OpenAIProvider(provider_name, provider)
    elif provider.provider_type == "qchatcli":
        return QChatCLIProvider(provider_name, provider)
    elif provider.provider_type == "MLXLocal":
        return MLXLocalProvider(provider_name, provider)
    elif provider.provider_type == "echo":
        return EchoProvider(provider_name, provider)
    else:
        raise click.ClickException(f"Unsupported LLM provider: {provider.provider_type} - {provider_name}")
