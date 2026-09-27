from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, UploadFile

from src.auth.service import AuthenticationService
from src.auth.views import AuthenticatedUser
from src.cv.service import CVService
from src.cv.views.cv_data import CVData
from src.cv.views.request import CreateEmptyCVRequest, CVUpdateRequest, UpdateCVTargetCountryRequest
from src.cv.views.response import CVListItemResponse, CVTargetCountryResponse, FullCVContent
from src.utils.utils import SafeDepends

router = APIRouter(prefix="/cv", tags=["cv"])
cv_service = CVService()


@router.get("/")
async def list_cvs(user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)) -> list[CVListItemResponse]:
    return await cv_service.list_cvs(user.uid)


@router.post("/create-empty", status_code=201)
async def create_empty_cv(
    request: CreateEmptyCVRequest, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)
) -> FullCVContent:
    return await cv_service.create_empty_cv(user.uid, request.language)


@router.post("/create-from-upload", status_code=201)
async def create_cv_from_upload(
    file: UploadFile, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)
) -> FullCVContent:
    """Upload a PDF (maximum 10MB), extract its content with OpenAI, and save the CV."""
    return await cv_service.create_cv_from_upload(file, user.uid)


@router.post("/import", status_code=201)
async def import_cv(request: CVData, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)) -> FullCVContent:
    """Import structured CV data. Every import receives fresh CV, section, and item IDs."""
    return await cv_service.import_cv(request, user.uid)


@router.get("/{cv_id}")
async def get_cv(cv_id: UUID, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)) -> FullCVContent:
    result = await cv_service.get_cv_by_id(cv_id, user.uid)
    if result is None:
        raise HTTPException(status_code=404, detail="CV not found or access denied")
    return result


@router.put("/{cv_id}")
async def update_cv(
    cv_id: UUID, request: CVUpdateRequest, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)
) -> FullCVContent:
    if cv_id != request.id:
        raise HTTPException(status_code=400, detail="CV ID mismatch")
    result = await cv_service.update_cv(cv_id, request, user.uid)
    if result is None:
        raise HTTPException(status_code=404, detail="CV not found or access denied")
    return result


@router.post("/{cv_id}/duplicate", status_code=201)
async def duplicate_cv(cv_id: UUID, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)) -> FullCVContent:
    result = await cv_service.duplicate_cv(cv_id, user.uid)
    if result is None:
        raise HTTPException(status_code=404, detail="CV not found or access denied")
    return result


@router.get("/{cv_id}/target-country")
async def get_cv_target_country(
    cv_id: UUID, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)
) -> CVTargetCountryResponse:
    result = await cv_service.get_cv_target_country(cv_id, user.uid)
    if result is None:
        raise HTTPException(status_code=404, detail="CV not found or access denied")
    return result


@router.patch("/{cv_id}/target-country")
async def update_cv_target_country(
    cv_id: UUID, request: UpdateCVTargetCountryRequest, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)
) -> FullCVContent:
    result = await cv_service.update_cv_target_country(cv_id, request.target_country_code, user.uid)
    if result is None:
        raise HTTPException(status_code=404, detail="CV not found or access denied")
    return result


@router.delete("/{cv_id}", status_code=204)
async def delete_cv(cv_id: UUID, user: AuthenticatedUser = SafeDepends(AuthenticationService.is_authenticated)):
    if not await cv_service.delete_cv(cv_id, user.uid):
        raise HTTPException(status_code=404, detail="CV not found or access denied")
    return Response(status_code=204)
