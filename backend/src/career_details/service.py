from uuid import UUID

from fastapi import HTTPException
from sqlmodel import col, select

from src.career_details._matching.service import WorkExperienceMatchingService
from src.career_details.models import CareerDetailsModel
from src.career_details.views import CareerDetails
from src.cv.models.cv import CVModel
from src.cv.models.cv_item import CVItemModel
from src.cv.models.cv_section import CVSectionModel, CVSectionType
from src.db import with_database_session
from src.db.service import AsyncSession, DatabaseService
from src.utils.classes import singleton


@singleton
class CareerDetailsService:
    def __init__(self):
        self.db_service = DatabaseService()
        self.matching_service = WorkExperienceMatchingService()

    @with_database_session
    async def get_details(self, session: AsyncSession, cv_item_id: UUID, user_id: str) -> CareerDetails | None:
        item = await self._require_employment_item(session, cv_item_id, user_id)
        await self.matching_service.rematch_user_employments(session, user_id)
        await session.refresh(item)
        if item.work_experience_id is None:
            return None
        details = await self.db_service.get_first_in(
            select(CareerDetailsModel).where(CareerDetailsModel.work_experience_id == item.work_experience_id),
            session,
        )
        return self._map_details(details) if details else None

    @with_database_session
    async def update_details(self, session: AsyncSession, cv_item_id: UUID, request: CareerDetails, user_id: str) -> CareerDetails:
        item = await self._require_employment_item(session, cv_item_id, user_id, lock=True)
        await self.matching_service.rematch_user_employments(session, user_id)
        await session.refresh(item)
        if item.work_experience_id is None:
            raise HTTPException(status_code=500, detail="Failed to link employment item to a work experience")

        details = await self.db_service.get_first_in(
            select(CareerDetailsModel).where(CareerDetailsModel.work_experience_id == item.work_experience_id),
            session,
        )
        if details is None:
            details = CareerDetailsModel(
                work_experience_id=item.work_experience_id,
                annual_salary=request.annual_salary,
                salary_currency=request.salary_currency,
                weekly_hours=request.weekly_hours,
                direct_reports=request.direct_reports,
            )
        else:
            details.annual_salary = request.annual_salary
            details.salary_currency = request.salary_currency
            details.weekly_hours = request.weekly_hours
            details.direct_reports = request.direct_reports

        await self.db_service.add(details, session)
        return self._map_details(details)

    @with_database_session
    async def delete_details(self, session: AsyncSession, cv_item_id: UUID, user_id: str):
        item = await self._require_employment_item(session, cv_item_id, user_id, lock=True)
        await self.matching_service.rematch_user_employments(session, user_id)
        await session.refresh(item)
        if item.work_experience_id is None:
            return
        details = await self.db_service.get_first_in(
            select(CareerDetailsModel).where(CareerDetailsModel.work_experience_id == item.work_experience_id),
            session,
        )
        if details is None:
            return
        await session.delete(details)
        await session.commit()

    async def rematch_for_user(self, user_id: str):
        async with await self.db_service.get_session() as session:
            await self.matching_service.rematch_user_employments(session, user_id)

    # -

    async def _require_employment_item(
        self, session: AsyncSession, cv_item_id: UUID, user_id: str, lock: bool = False
    ) -> CVItemModel:
        query = (
            select(CVItemModel)
            .join(CVSectionModel, col(CVItemModel.section_id) == CVSectionModel.id)
            .join(CVModel, col(CVSectionModel.cv_id) == CVModel.id)
            .where(CVItemModel.id == cv_item_id, CVSectionModel.type == CVSectionType.employment, CVModel.user_id == user_id)
        )
        if lock:
            # Keep the employment item from being deleted while its details are saved.
            query = query.with_for_update(of=CVItemModel)
        item = await self.db_service.get_first_in(query, session)
        if item is None:
            raise HTTPException(status_code=404, detail="Employment item not found or access denied")
        return item

    def _map_details(self, details: CareerDetailsModel) -> CareerDetails:
        return CareerDetails(
            annual_salary=details.annual_salary,
            salary_currency=details.salary_currency,
            weekly_hours=details.weekly_hours,
            direct_reports=details.direct_reports,
        )
