from typing import Protocol, TypeVar, assert_never

from openai.types.responses import ResponseInputContentParam, ResponseInputParam
from openai.types.responses.response_input_param import Message as OpenAIMessage
from pydantic import BaseModel

from src.llm.views.prompt.encodable import EncodablePromptItem
from src.llm.views.prompt.follow_up_messages import AssistantFollowUpMessage, UserFollowUpMessage

UserPrompt = str | EncodablePromptItem | list[str | EncodablePromptItem]
FollowUpPrompt = AssistantFollowUpMessage | UserFollowUpMessage
Output_T = TypeVar("Output_T", bound=str | BaseModel, covariant=True)


class PromptTemplate(Protocol):
    """Declare Output as a nested model, a model alias, str, or a property returning a model type."""

    Output: type[str | BaseModel]

    def system_prompt(self) -> str: ...

    def user_prompt(self) -> UserPrompt: ...

    def follow_up_prompt(self) -> list[FollowUpPrompt]:
        return []

    # - Internal implementation

    def _encode_user_prompt(self, user_prompt: UserPrompt) -> OpenAIMessage:
        # Convert user_prompt to a list if it's not already
        if not isinstance(user_prompt, list):
            user_prompt = [user_prompt]

        # Build content list for the message
        content: list[ResponseInputContentParam] = []
        for item in user_prompt:
            if isinstance(item, str):
                content.append({"type": "input_text", "text": item})
            elif isinstance(item, EncodablePromptItem):
                content.append(item._encoded())
            else:
                assert_never(item)

        # Return as a list containing one user message
        message: OpenAIMessage = {"role": "user", "content": content}
        return message

    def _encoded_follow_up_prompt(self) -> ResponseInputParam:
        messages: ResponseInputParam = []

        for follow_up in self.follow_up_prompt():
            if isinstance(follow_up, UserFollowUpMessage):
                messages.append(self._encode_user_prompt(follow_up.message))
            elif isinstance(follow_up, AssistantFollowUpMessage):
                if isinstance(follow_up.message, str):
                    messages.append({"role": "assistant", "content": follow_up.message})
                elif isinstance(follow_up.message, BaseModel):
                    messages.append({"role": "assistant", "content": follow_up.message.model_dump_json()})
                else:
                    assert_never(follow_up.message)
            else:
                assert_never(follow_up)

        return messages

    def _encoded_input_messages(self) -> ResponseInputParam:
        return [self._encode_user_prompt(self.user_prompt())] + self._encoded_follow_up_prompt()


# region: - Service typing


class _TypedPrompt(PromptTemplate, Protocol[Output_T]):
    """Infer the result from Output at the service call, including nested models."""

    @property
    def Output(self) -> type[Output_T]: ...


# endregion
