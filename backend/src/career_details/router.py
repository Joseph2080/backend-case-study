from uuid import UUID

from fastapi import APIRouter, Response

from src.auth.service import AuthenticationService
from src.auth.views import AuthenticatedUser
from src.career_details.service import CareerDetailsService
from src.career_details.views import CareerDetails
from src.utils.utils import SafeDepends

router = APIRouter(prefix="/career-details", tags=["career-details"])
career_details_service = CareerDetailsService()


@router.get("/{cv_item_id}")
async def get_career_details(
    cv_item_id: UUID, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)
) -> CareerDetails | None:
    return await career_details_service.get_details(cv_item_id, user.uid)


@router.put("/{cv_item_id}")
async def update_career_details(
    cv_item_id: UUID, request: CareerDetails, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)
) -> CareerDetails:
    """Create or replace the complete set of private career details."""
    return await career_details_service.update_details(cv_item_id, request, user.uid)


@router.delete("/{cv_item_id}", status_code=204)
async def delete_career_details(cv_item_id: UUID, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)):
    await career_details_service.delete_details(cv_item_id, user.uid)
    return Response(status_code=204)
