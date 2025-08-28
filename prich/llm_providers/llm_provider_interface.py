from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """LLM Provider Interface"""
    name: str
    mode: str
    show_response: bool

    @abstractmethod
    def send_prompt(self, prompt: str = None, instructions: str = None, input_: str = None) -> str:
        """Send a prompt to the LLM and return the response. Use prompt with full model prompt template and system/user when model supports field templates."""
        pass
