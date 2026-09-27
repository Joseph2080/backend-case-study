from typing import Literal

from openai.types.responses.response_create_params import PromptCacheOptions
from typing_extensions import TypedDict

CachePolicy = Literal["none", "system", "conversation"]
"""Prompt caching behavior for GPT-5.6+.

``none`` disables caching, ``system`` explicitly caches only the system prompt,
and ``conversation`` implicitly caches the whole conversation at its latest message.
Older models ignore this policy and retain their automatic caching behavior.
"""


class PromptCacheArgs(TypedDict, total=False):
    prompt_cache_key: str
    prompt_cache_options: PromptCacheOptions
