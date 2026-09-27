from typing import Generic, TypeVar

from pydantic import BaseModel

from src.llm.views.cache import CachePolicy

Parsed_T = TypeVar("Parsed_T", bound=BaseModel)


class StructuredOutputResponse(BaseModel, Generic[Parsed_T]):
    id: str
    data: Parsed_T
    prompt_cache_key: str | None = None
    cache_policy: CachePolicy
