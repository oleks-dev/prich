import click
import pytest

from prich.models.config import STDINConsumerProviderModel

from prich.llm_providers.stdin_consumer_provider import STDINConsumerProvider

get_stdin_consumer_CASES = [
    {"id": "stdin_consumer",
     "name": "echo",
     "prompt": {
         "prompt": "test",
     },
     "provider": STDINConsumerProviderModel(
         provider_type="stdin_consumer", name="echo", call="cat", args=[], mode="flat"
     ),
     "expected_output": "test",
     },

    {"id": "stdin_consumer_wrong_prompts",
     "name": "echo",
     "prompt": {
         "system": "system",
         "user": "user",
     },
     "provider": STDINConsumerProviderModel(
         provider_type="stdin_consumer", name="echo", call="cat", args=[], mode="flat"
     ),
     "expected_exception": click.ClickException,
     "expected_exception_messages": ["stdin consumer provider requires provider mode"],
     },

    {"id": "stdin_consumer_wrong_prompts",
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

]
@pytest.mark.parametrize("case", get_stdin_consumer_CASES, ids=[c["id"] for c in get_stdin_consumer_CASES])
def test_stdin_consumer(case):
    provider = case.get("provider")
    stdin_consumer = STDINConsumerProvider(name=case.get("name"), provider=provider)

    prompt = None
    system = None
    user = None
    if case.get("prompt") is not None:
        prompt = case["prompt"].get("prompt")
        system = case["prompt"].get("system")
        user = case["prompt"].get("user")
    if case.get("expected_exception"):
        with pytest.raises(case.get("expected_exception")) as e:
            stdin_consumer.send_prompt(prompt=prompt, system=system, user=user)
        if case.get("expected_exception_messages"):
            for message in case.get("expected_exception_messages"):
                assert message in str(e)
    else:
        result = stdin_consumer.send_prompt(prompt=prompt, system=system, user=user)
        if case.get("expected_output"):
            assert case.get("expected_output") == result
