from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """LLM Provider Interface"""
    name: str
    mode: str
    show_response: bool

    @abstractmethod
    def send_prompt(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the response."""
        pass
