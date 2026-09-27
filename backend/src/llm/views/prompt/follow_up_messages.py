from pydantic import BaseModel

from src.llm.views.prompt.encodable import EncodablePromptItem


class AssistantFollowUpMessage(BaseModel):
    message: str | BaseModel


class UserFollowUpMessage(BaseModel):
    message: str | EncodablePromptItem | list[str | EncodablePromptItem]

    class Config:
        arbitrary_types_allowed = True
