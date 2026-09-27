import hashlib
import json
import logging
from typing import Literal, TypeVar, assert_never

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, InternalServerError, RateLimitError
from openai.types.responses import ResponseInputParam, ResponseInputTextParam
from openai.types.responses.response_input_param import Message as OpenAIMessage
from openai.types.shared.reasoning_effort import ReasoningEffort
from pydantic import BaseModel

from src.llm.views.cache import CachePolicy, PromptCacheArgs
from src.llm.views.llm_models import LanguageModel, OpenAIModel, is_openai_model
from src.llm.views.prompt.template import PromptTemplate, UserPrompt, _TypedPrompt
from src.llm.views.results import StructuredOutputResponse
from src.utils.classes import singleton
from src.utils.env import env
from src.utils.wrappers import retry_with_exponential_backoff_async

OutputSchema = TypeVar("OutputSchema", bound=BaseModel)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@singleton
class LLMService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=env.OPENAI_API_KEY.get_secret_value())

    @retry_with_exponential_backoff_async(
        errors=(RateLimitError, APITimeoutError, APIConnectionError, InternalServerError),  # , BadRequestError),
        log_on_retry=logger,
    )
    async def call_with_structured_output(
        self,
        model: LanguageModel,
        prompt: _TypedPrompt[OutputSchema],
        temperature: float = 1.0,
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        allow_web_search_tool: bool = False,
        # verbosity: Literal["low", "medium", "high"] = "medium",
        metadata: dict[str, str] | None = None,
        use_priority_tier: bool = False,  # more expensive but faster (if true)
        max_output_tokens: int = 32_000,
        cache_policy: CachePolicy = "system",
    ) -> StructuredOutputResponse[OutputSchema]:
        openai_model = self._to_openai_model(model)
        metadata = {**(metadata or {}), "env": env.ENVIRONMENT}
        input_messages, cache_args = self._prepare_prompt(openai_model, prompt, cache_policy)
        res = await self.openai_client.responses.parse(
            model=openai_model,
            input=input_messages,
            temperature=temperature,
            text_format=prompt.Output,
            reasoning={
                "effort": self._to_openai_reasoning_effort(reasoning_effort, openai_model),
                "summary": "auto",
            },
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": "medium",
                }
            ]
            if allow_web_search_tool
            else [],
            max_output_tokens=max_output_tokens,
            # verbosity=verbosity,
            metadata=metadata,
            service_tier="priority" if use_priority_tier else "default",
            **cache_args,
        )

        if not res.output_parsed:
            logger.error(f"No output parsed: {res.error}")
            raise Exception(f"No output parsed: {res.error}")

        return StructuredOutputResponse(
            id=res.id,
            data=res.output_parsed,
            prompt_cache_key=cache_args.get("prompt_cache_key"),
            cache_policy=cache_policy,
        )

    @retry_with_exponential_backoff_async(
        errors=(RateLimitError, APITimeoutError, APIConnectionError, InternalServerError),  # , BadRequestError),
        log_on_retry=logger,
    )
    async def follow_up_with_structured_output(
        self,
        model: LanguageModel,
        message: str,  # follow-up message
        output_schema: type[OutputSchema],
        previous_response: StructuredOutputResponse[OutputSchema],
        reasoning_effort: Literal["low", "medium", "high"] | None = None,
        allow_web_search_tool: bool = False,
        metadata: dict[str, str] | None = None,
        use_priority_tier: bool = False,  # more expensive but faster (if true)
    ) -> StructuredOutputResponse[OutputSchema]:
        """Only works after a previous response from `call_with_structured_output`."""
        openai_model = self._to_openai_model(model)
        metadata = {**(metadata or {}), "env": env.ENVIRONMENT}
        cache_policy = previous_response.cache_policy
        cache_args: PromptCacheArgs = {}
        if self._supports_explicit_prompt_caching(openai_model):
            cache_args["prompt_cache_options"] = {"mode": "implicit" if cache_policy == "conversation" else "explicit"}
            if cache_policy != "none" and previous_response.prompt_cache_key:
                cache_args["prompt_cache_key"] = previous_response.prompt_cache_key
        res = await self.openai_client.responses.parse(
            model=openai_model,
            previous_response_id=previous_response.id,
            input=message,
            text_format=output_schema,
            reasoning={
                "effort": self._to_openai_reasoning_effort(reasoning_effort, openai_model),
                "summary": "auto",
            },
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": "medium",
                }
            ]
            if allow_web_search_tool
            else [],
            max_output_tokens=32_000,
            metadata=metadata,
            service_tier="priority" if use_priority_tier else "default",
            **cache_args,
        )

        if not res.output_parsed:
            logger.error(f"No output parsed: {res.error}")
            raise Exception(f"No output parsed: {res.error}")

        return StructuredOutputResponse(
            id=res.id,
            data=res.output_parsed,
            prompt_cache_key=previous_response.prompt_cache_key,
            cache_policy=cache_policy,
        )

    def _prepare_prompt(
        self, model: OpenAIModel, prompt: PromptTemplate, cache_policy: CachePolicy
    ) -> tuple[ResponseInputParam, PromptCacheArgs]:
        """Encode the system prompt as persistent conversation state and configure GPT-5.6+ caching."""
        system_prompt = prompt.system_prompt()
        supports_explicit_caching = self._supports_explicit_prompt_caching(model)

        developer_content: ResponseInputTextParam = {"type": "input_text", "text": system_prompt}
        if supports_explicit_caching and cache_policy == "system":
            developer_content["prompt_cache_breakpoint"] = {"mode": "explicit"}
        developer_message: OpenAIMessage = {"role": "developer", "content": [developer_content]}

        input_messages = [developer_message, *prompt._encoded_input_messages()]

        if not supports_explicit_caching:
            return input_messages, {}

        match cache_policy:
            case "none":
                return input_messages, {"prompt_cache_options": {"mode": "explicit"}}
            case "system":
                return input_messages, {
                    "prompt_cache_key": self._prompt_cache_key(system_prompt),
                    "prompt_cache_options": {"mode": "explicit"},
                }
            case "conversation":
                return input_messages, {
                    "prompt_cache_key": self._prompt_cache_key(system_prompt, prompt.user_prompt()),
                    "prompt_cache_options": {"mode": "implicit"},
                }

    def _supports_explicit_prompt_caching(self, model: OpenAIModel) -> bool:
        """Return whether the model accepts GPT-5.6+ explicit prompt-cache controls."""
        match model:
            case "gpt-5.6-sol" | "gpt-5.6-terra" | "gpt-5.6-luna":
                return True
            case (
                "gpt-4.1"
                | "gpt-4.1-mini"
                | "gpt-5"
                | "gpt-5-mini"
                | "gpt-5-nano"
                | "gpt-5.1"
                | "gpt-5.1-chat-latest"
                | "gpt-5.2"
                | "gpt-5.4-mini"
                | "gpt-5.5"
            ):
                return False
            case _:
                assert_never(model)

    def _prompt_cache_key(self, system_prompt: str, first_user_prompt: UserPrompt | None = None) -> str:
        """Hash the system prompt and first-user text while intentionally excluding file and image content."""
        key_parts = [system_prompt]
        if isinstance(first_user_prompt, str):
            key_parts.append(first_user_prompt)
        elif isinstance(first_user_prompt, list):
            key_parts.extend(item for item in first_user_prompt if isinstance(item, str))
        return hashlib.sha256(json.dumps(key_parts, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()).hexdigest()

    def _to_openai_model(self, model: LanguageModel) -> OpenAIModel:
        if is_openai_model(model):
            return model

        match model:
            case "default_writing":
                return "gpt-5.6-terra"
            case "default_extraction":
                return "gpt-5.1"
            case "default_chat":
                return "gpt-5.1"
            case "default_writing_small":
                return "gpt-5-mini"
            case "default_extraction_fast":
                return "gpt-5.4-mini"
            case "default_best":
                return "gpt-5.5"
            case _:
                assert_never(model)

    def _to_openai_reasoning_effort(
        self, reasoning_effort: Literal["low", "medium", "high"] | None, model: OpenAIModel
    ) -> ReasoningEffort | None:
        """None input selects model-specific default (none/minimal/omit), None output means omit the parameter entirely."""
        match reasoning_effort:
            case "low":
                return "low"
            case "medium":
                return "medium"
            case "high":
                return "high"
            case None:
                if model.endswith("chat-latest"):
                    return None  # chat models use automatic reasoning
                elif model == "gpt-5" or model.startswith("gpt-5-"):
                    return "minimal"
                else:
                    return "none"
