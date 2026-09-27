from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.views import AuthenticatedUser

# Public development credentials for the local exercise, not production authentication.
LOCAL_USERS = {"alice-token": "alice", "bob-token": "bob"}


class AuthenticationService:
    @staticmethod
    async def is_authenticated(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))],
    ) -> AuthenticatedUser:
        user_id = LOCAL_USERS.get(credentials.credentials) if credentials else None
        if user_id is None:
            raise HTTPException(status_code=401, detail="Use alice-token or bob-token", headers={"WWW-Authenticate": "Bearer"})
        return AuthenticatedUser(uid=user_id)
