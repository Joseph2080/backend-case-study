from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    uid: str
