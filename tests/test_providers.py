import json
import click
import pytest
from dataclasses import dataclass
from contextlib import contextmanager

from prich.llm_providers.ollama_provider import OllamaProvider

from prich.models.config_providers import OpenAIProviderModel, OllamaProviderModel
from prich.models.config import STDINConsumerProviderModel
from prich.llm_providers.openai_provider import OpenAIProvider
from prich.llm_providers.stdin_consumer_provider import STDINConsumerProvider
from tests.utils.utils import capture_stdout

@dataclass
class Delta:
    content: str

@dataclass
class Choice:
    delta: Delta | None

@dataclass
class OpenAIStream:
    choices: list[Choice] | None


get_provider_CASES = [
    {"id": "stdin_consumer",
     "name": "echo",
     "prompt": {
         "prompt": "test",
     },
     "provider": STDINConsumerProviderModel(
         provider_type="stdin_consumer", name="echo", call="cat", args=[], mode="flat"
     ),
     "expected_output": "",
     "expected_result": "test"
     },

    {"id": "stdin_consumer_wrong_prompt_1",
     "name": "echo",
     "prompt": {
         "instructions": "system",
         "input": "user",
     },
     "provider": STDINConsumerProviderModel(
         provider_type="stdin_consumer", name="echo", call="cat", args=[], mode="flat"
     ),
     "expected_exception": click.ClickException,
     "expected_exception_messages": ["stdin consumer provider requires provider mode"],
     },

    {"id": "stdin_consumer_wrong_prompt_2",
     "name": "echo",
     "prompt": {
         "prompt": "test",
     },
     "provider": STDINConsumerProviderModel(
         provider_type="stdin_consumer", name="echo", call="catt", args=[], mode="flat"
     ),
     "expected_exception": click.ClickException,
     "expected_exception_messages": ["STDIN consumer provider error: [Errno 2] No such file or director"],
     },

    # OpenAI

    {"id": "openai_wrong_prompt_1",
     "name": "openai",
     "prompt": {
         "prompt": "test",
     },
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={}
     ),
     "expected_exception": click.ClickException,
     "expected_exception_messages": ["Failed to decode prompt JSON"],
     },
    {"id": "openai_wrong_prompt_2",
     "name": "openai",
     "prompt": {
         "prompt": "{\"test\":\"test\"}",
     },
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={}
     ),
     "expected_exception": click.ClickException,
     "expected_exception_messages": ["OpenAI error: Missing required arguments; Expected either ('messages' and 'model') or ('messages', 'model' and 'stream') arguments to be given"],
     },
    {"id": "openai_prompt_1",
     "name": "openai",
     "prompt": {
         "prompt": json.dumps({
             "messages": [
                 {"role": "user", "content": "hello"}
             ],
             "model": "gpt3"
         }),
     },
     "fake_provider_response": "test llm response",
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "openai_prompt_instructions_and_input",
     "name": "openai",
     "prompt": {
         "instructions": "hello",
         "input": "hello",
     },
     "fake_provider_response": "test llm response",
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "openai_prompt_only_input_field",
     "name": "openai",
     "prompt": {
         "input": "hello",
     },
     "fake_provider_response": "test llm response",
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "openai_stream_prompt",
     "name": "openai",
     "prompt": {
         "prompt": json.dumps({
             "messages": [
                 {"role": "user", "content": "hello"}
             ],
             "model": "gpt3"
         }),
     },
     "fake_provider_stream_response": [
            None,
            OpenAIStream(None),
            OpenAIStream(choices=[Choice(delta=Delta(""))]),
            OpenAIStream(choices=[Choice(delta=Delta("test"))]),
            OpenAIStream(choices=[Choice(delta=Delta(" llm"))]),
            OpenAIStream(choices=[Choice(delta=Delta(" response"))]),
     ],
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={"stream": True}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "openai_stream_prompt_show_response_false",
     "name": "openai",
     "show_response": False,
     "prompt": {
         "prompt": json.dumps({
             "messages": [
                 {"role": "user", "content": "hello"}
             ],
             "model": "gpt3"
         }),
     },
     "fake_provider_stream_response": [
            None,
            OpenAIStream(None),
            OpenAIStream(choices=[Choice(delta=Delta(""))]),
            OpenAIStream(choices=[Choice(delta=Delta("test"))]),
            OpenAIStream(choices=[Choice(delta=Delta(" llm"))]),
            OpenAIStream(choices=[Choice(delta=Delta(" response"))]),
     ],
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={"stream": True}
     ),
     "expected_return": "test llm response",
     "expected_output": "",
     },
    {"id": "openai_stream_prompt_show_response_false_quiet",
     "name": "openai",
     "show_response": False,
     "is_quiet": True,
     "prompt": {
         "prompt": json.dumps({
             "messages": [
                 {"role": "user", "content": "hello"}
             ],
             "model": "gpt3"
         }),
     },
     "fake_provider_stream_response": [
            None,
            OpenAIStream(None),
            OpenAIStream(choices=[Choice(delta=Delta(""))]),
            OpenAIStream(choices=[Choice(delta=Delta("test"))]),
            OpenAIStream(choices=[Choice(delta=Delta(" llm"))]),
            OpenAIStream(choices=[Choice(delta=Delta(" response"))]),
     ],
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={"stream": True}
     ),
     "expected_return": "test llm response",
     "expected_output": "",
     },
    {"id": "openai_stream_prompt_show_response_true_quiet",
     "name": "openai",
     "show_response": True,
     "is_quiet": True,
     "prompt": {
         "prompt": json.dumps({
             "messages": [
                 {"role": "user", "content": "hello"}
             ],
             "model": "gpt3"
         }),
     },
     "fake_provider_stream_response": [
            None,
            OpenAIStream(None),
            OpenAIStream(choices=[Choice(delta=Delta(""))]),
            OpenAIStream(choices=[Choice(delta=Delta("test"))]),
            OpenAIStream(choices=[Choice(delta=Delta(" llm"))]),
            OpenAIStream(choices=[Choice(delta=Delta(" response"))]),
     ],
     "provider": OpenAIProviderModel(
         provider_type="openai", name="openai", configuration={"api_key": "test"}, options={"stream": True}
     ),
     "expected_return": "test llm response",
     "expected_output": "",
     },

    # Ollama

    {"id": "ollama_wrong_model",
     "name": "ollama",
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_response": "hello",
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="test", options={"stream": True}
     ),
     "expected_exception": click.ClickException,
     "expected_exception_messages": ["Model 'test' is not installed on Ollama. Install it with: 'ollama pull test'"],
     },
    {"id": "ollama_prompt",
     "name": "ollama",
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_response": "test llm response",
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "ollama_instructions_and_input",
     "name": "ollama",
     "prompt": {
         "instructions": "hello",
         "input": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_response": "test llm response",
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "ollama_only_input",
     "name": "ollama",
     "prompt": {
         "input": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_response": "test llm response",
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "ollama_prompt_quiet",
     "name": "ollama",
     "prompt": {
         "prompt": "hello",
     },
     "is_quiet": True,
     "ollama_models": [{"name": "model1"}],
     "fake_provider_response": "test llm response",
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "",
     },
    {"id": "ollama_prompt_show_response_false",
     "name": "ollama",
     "show_response": False,
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_response": "test llm response",
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "",
     },
    {"id": "ollama_prompt_stream",
     "name": "ollama",
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_stream_response": [json.dumps({"response": "test"}), json.dumps({"response": " llm"}), json.dumps({"response": " response"}), json.dumps({"done": True})],
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", stream=True, options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "ollama_prompt_stream_response_json_error",
     "name": "ollama",
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_stream_response": ["{\"response\": \'test\'\}"],
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", stream=True, options={}
     ),
     "expected_exception": click.ClickException,
     "expected_exception_messages": ["Ollama provider JSON parsing error"],
     },
    {"id": "ollama_prompt_stream_quiet",
     "name": "ollama",
     "is_quiet": True,
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_stream_response": [json.dumps({"response": "test"}), json.dumps({"response": " llm"}), json.dumps({"response": " response"})],
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", stream=True, options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "",
     },
    {"id": "ollama_prompt_stream_thinking",
     "name": "ollama",
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_stream_response": [json.dumps({"response": "test"}), json.dumps({"response": " llm"}), json.dumps({"response": " response"})],
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", stream=True, think=True, options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "test llm response\n",
     },
    {"id": "ollama_prompt_stream_show_response_false",
     "name": "ollama",
     "show_response": False,
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_stream_response": [json.dumps({"response": "test"}), json.dumps({"response": " llm"}), json.dumps({"response": " response"})],
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", stream=True, options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "",
     },
    {"id": "ollama_prompt_stream_thinking_show_response_false",
     "name": "ollama",
     "show_response": False,
     "prompt": {
         "prompt": "hello",
     },
     "ollama_models": [{"name": "model1"}],
     "fake_provider_stream_response": [json.dumps({"response": "test"}), json.dumps({"response": " llm"}), json.dumps({"response": " response"})],
     "provider": OllamaProviderModel(
         provider_type="ollama", name="test", model="model1", think=True, stream=True, options={}
     ),
     "expected_return": "test llm response",
     "expected_output": "",
     },

]
@pytest.mark.parametrize("case", get_provider_CASES, ids=[c["id"] for c in get_provider_CASES])
def test_providers(case, monkeypatch):
    def fake_response_function(self, **kwargs):
        return case.get("fake_provider_response")

    @contextmanager
    def fake_response_stream(self, **kwargs):
        yield case.get("fake_provider_stream_response")

    provider_data = case.get("provider")
    if type(provider_data) is STDINConsumerProviderModel:
        provider = STDINConsumerProvider(name=case.get("name"), provider=provider_data)

    elif type(provider_data) is OpenAIProviderModel:
        # from openai import OpenAI
        provider = OpenAIProvider(name=case.get("name"), provider=provider_data)
        if case.get("fake_provider_response") is not None:
            monkeypatch.setattr(OpenAIProvider, "_get_completion", fake_response_function)
        elif case.get("fake_provider_stream_response") is not None:
            monkeypatch.setattr(OpenAIProvider, "_get_stream_completion_chunks", fake_response_stream)

    elif type(provider_data) is OllamaProviderModel:
        provider = OllamaProvider(name=case.get("name"), provider=provider_data)
        if case.get("ollama_models") is not None:
            monkeypatch.setattr(OllamaProvider, "_get_models", lambda x: case.get("ollama_models"))
        if case.get("fake_provider_response") is not None:
            monkeypatch.setattr(OllamaProvider, "_get_generate", fake_response_function)
        if case.get("fake_provider_stream_response") is not None:
            monkeypatch.setattr(OllamaProvider, "_get_stream_generate", fake_response_stream)

    else:
        raise RuntimeError("Not supported provider")

    if case.get("is_quiet") is not None:
        monkeypatch.setattr("prich.llm_providers.openai_provider.is_print_enabled", lambda: not case.get("is_quiet"))
        monkeypatch.setattr("prich.core.utils.is_print_enabled", lambda: not case.get("is_quiet"))

    if case.get("show_response") is not None:
        provider.show_response = case.get("show_response")

    prompt = None
    instructions = None
    input_ = None
    if case.get("prompt") is not None:
        prompt = case["prompt"].get("prompt")
        instructions = case["prompt"].get("instructions")
        input_ = case["prompt"].get("input")
    if case.get("expected_exception") is not None:
        with pytest.raises(case.get("expected_exception")) as e:
            provider.send_prompt(prompt=prompt, instructions=instructions, input_=input_)
        if case.get("expected_exception_messages") is not None:
            for message in case.get("expected_exception_messages"):
                assert message in str(e.value)
    else:
        result, output = capture_stdout(provider.send_prompt, prompt=prompt, instructions=instructions, input_=input_)
        result_repeat, output_repeat = capture_stdout(provider.send_prompt, prompt=prompt, instructions=instructions, input_=input_)
        if case.get("expected_output") is not None:
            assert case.get("expected_output") == output
            assert case.get("expected_output") == output_repeat
        if case.get("expected_result") is not None:
            assert case.get("expected_result") == result
            assert case.get("expected_result") == result_repeat

