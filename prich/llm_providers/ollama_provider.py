import json
import click
from requests import JSONDecodeError
from rich.console import Console
from contextlib import nullcontext

from prich.core.utils import console_print, is_print_enabled
from prich.models.config_providers import OllamaProviderModel
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.llm_providers.base_optional_provider import LazyOptionalProvider

console = Console()


class OllamaProvider(LLMProvider, LazyOptionalProvider):
    def __init__(self, name: str, provider: OllamaProviderModel):
        super().__init__()
        self.name = name
        self.provider = provider
        self.base_url = provider.base_url or "http://localhost:11434"
        if self.base_url[-1] == "/":
            self.base_url = self.base_url[:-1]
        self.client_url = f"{self.base_url}/api/generate"
        self.show_response = True
        self.health_url = f"{self.base_url}/api/tags"
        self.requests = None

    def get_models(self):
        resp = self.requests.get(self.health_url, timeout=2)
        resp.raise_for_status()
        return resp.json().get("models", [])

    def get_stream_generate(self, payload):
        resp = self.requests.post(self.client_url, json=payload, stream=True)
        resp.raise_for_status()
        yield resp.iter_lines(decode_unicode=True)

    def get_generate(self, payload):
        resp = self.requests.post(self.client_url, json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "")

    def _ensure_client(self):
        # Ensure 'requests' library is available
        self.requests = self._lazy_import("requests", pip_name="requests")
        # Check Ollama server
        try:
            models = self.get_models()
        except self.requests.RequestException:
            raise click.ClickException(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Is Ollama running? Start it with: `ollama serve`"
            )

        # Check if model is installed
        models = [m.get("name") for m in models]
        if self.provider.model not in models:
            raise click.ClickException(
                f"Model '{self.provider.model}' is not installed on Ollama. "
                f"Install it with: 'ollama pull {self.provider.model}'"
            )

    def send_prompt(self, prompt: str = None, instructions: str = None, input_: str = None) -> str:
        self._ensure_client()
        text = []
        try:
            if prompt:
                if not isinstance(prompt, str):
                    prompt = json.dumps(prompt)
            else:
                prompt = input_
            payload = {
                "model": self.provider.model,
                "prompt": prompt,
                "options": self.provider.options or {}
            }
            if instructions:
                payload['system'] = instructions
            if is_print_enabled() and self.provider.stream is not None:
                payload["stream"] = self.provider.stream
            else:
                payload["stream"] = False
            if self.provider.think is not None:
                payload["think"] = self.provider.think

            status = console.status("Thinking...") if is_print_enabled() else nullcontext()

            with status:
                if payload.get("stream"):
                    # Streaming mode
                    with self.get_stream_generate(payload=payload) as response_lines:
                        for line in response_lines:
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    chunk = data["response"]
                                    text.append(chunk)
                                    if self.show_response and is_print_enabled():
                                        if self.provider.think and status._live.is_started and not chunk:
                                            if status.status != f"{self.provider.model} Thinking...":
                                                status.update(status=f"{self.provider.model} Thinking...")
                                        if not isinstance(status, nullcontext) and status._live.is_started and chunk:
                                            status.stop()
                                        console_print(chunk, end='')
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue

                        if self.show_response and is_print_enabled():
                            console_print()
                else:
                    output = self.get_generate(payload=payload)
                    text.append(output)
                    if self.show_response and is_print_enabled():
                        if not isinstance(status, nullcontext):
                            status.stop()
                        console_print(output)

            return ''.join(text)
        except JSONDecodeError as e:
            raise click.ClickException(f"Ollama provider JSON parsing error: {str(e)}")
        except self.requests.RequestException as e:
            raise click.ClickException(f"Ollama provider request error: {str(e)}")
        except Exception as e:
            raise click.ClickException(f"Ollama provider error: {str(e)}")
