from typing import Protocol, runtime_checkable

from openai.types.responses import ResponseInputContentParam


@runtime_checkable
class EncodablePromptItem(Protocol):
    """Runtime-checkable protocol for prompts that can encode themselves for OpenAI responses."""

    def _encoded(self) -> ResponseInputContentParam: ...
