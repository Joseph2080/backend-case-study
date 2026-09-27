from typing import Literal, get_args

from typing_extensions import TypeIs

LanguageModelAlias = Literal[
    "default_writing",
    "default_extraction",
    "default_chat",
    "default_writing_small",
    "default_extraction_fast",
    "default_best",
]

OpenAIModel = Literal[
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-5.1",
    "gpt-5.1-chat-latest",
    "gpt-5.2",
    "gpt-5.4-mini",
    "gpt-5.5",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
]

LanguageModel = LanguageModelAlias | OpenAIModel


# -


def is_openai_model(model: LanguageModel) -> TypeIs[OpenAIModel]:
    """Narrow a language model to a concrete OpenAI model ID."""
    return model in get_args(OpenAIModel)
