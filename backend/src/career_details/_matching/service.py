from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlmodel import col, select

from src.career_details._matching.utils import EmploymentFingerprint, PersonIdentity, employments_match
from src.career_details.models import CareerDetailsModel, WorkExperienceModel
from src.cv.models.cv import CVModel
from src.cv.models.cv_item import CVItemModel
from src.cv.models.cv_section import CVSectionModel, CVSectionType
from src.db.service import AsyncSession, DatabaseService
from src.utils.classes import singleton


@dataclass
class _EmploymentCandidate:
    item: CVItemModel
    person: PersonIdentity
    fingerprint: EmploymentFingerprint


@singleton
class WorkExperienceMatchingService:
    def __init__(self):
        self.db_service = DatabaseService()

    async def rematch_user_employments(self, session: AsyncSession, user_id: str):
        """Cluster employment entries per person and assign shared work_experience ids."""
        candidates = await self._load_candidates(session, user_id)
        if not candidates:
            return

        by_person: dict[str, list[_EmploymentCandidate]] = {}
        for candidate in candidates:
            by_person.setdefault(candidate.person.key(), []).append(candidate)

        for person_candidates in by_person.values():
            await self._assign_clusters(session, user_id, person_candidates)

        await session.commit()

    async def _load_candidates(self, session: AsyncSession, user_id: str) -> list[_EmploymentCandidate]:
        result = await session.execute(
            select(CVItemModel, CVModel)
            .join(CVSectionModel, col(CVItemModel.section_id) == CVSectionModel.id)
            .join(CVModel, col(CVSectionModel.cv_id) == CVModel.id)
            .where(CVModel.user_id == user_id, CVSectionModel.type == CVSectionType.employment)
        )
        rows = result.all()

        candidates: list[_EmploymentCandidate] = []
        for item, cv in rows:
            person = PersonIdentity(
                email=cv.email,
                first_name=cv.first_name,
                last_name=cv.last_name,
                date_of_birth=cv.date_of_birth,
            )
            fingerprint = EmploymentFingerprint(
                title=item.title,
                organization=item.organization,
                city=item.city,
                start_year=item.start_year,
                start_month=item.start_month,
                end_year=item.end_year,
                end_month=item.end_month,
            )
            candidates.append(_EmploymentCandidate(item=item, person=person, fingerprint=fingerprint))
        return candidates

    async def _assign_clusters(self, session: AsyncSession, user_id: str, candidates: list[_EmploymentCandidate]):
        parent = list(range(len(candidates)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i: int, j: int):
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[rj] = ri

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                if employments_match(candidates[i].fingerprint, candidates[j].fingerprint):
                    union(i, j)

        clusters: dict[int, list[_EmploymentCandidate]] = {}
        for index, candidate in enumerate(candidates):
            clusters.setdefault(find(index), []).append(candidate)

        for cluster in clusters.values():
            work_experience_id = await self._resolve_work_experience_id(session, user_id, cluster)
            for candidate in cluster:
                if candidate.item.work_experience_id != work_experience_id:
                    candidate.item.work_experience_id = work_experience_id
                    session.add(candidate.item)

    async def _resolve_work_experience_id(
        self, session: AsyncSession, user_id: str, cluster: list[_EmploymentCandidate]
    ) -> UUID:
        existing_ids = [c.item.work_experience_id for c in cluster if c.item.work_experience_id is not None]
        unique_ids = list(dict.fromkeys(existing_ids))

        if len(unique_ids) == 1:
            return unique_ids[0]

        if len(unique_ids) > 1:
            chosen = await self._pick_work_experience_with_details(session, unique_ids)
            await self._merge_career_details(session, chosen, unique_ids)
            return chosen

        work_experience = WorkExperienceModel(id=uuid4(), user_id=user_id)
        session.add(work_experience)
        await session.flush()
        return work_experience.id

    async def _pick_work_experience_with_details(self, session: AsyncSession, work_experience_ids: list[UUID]) -> UUID:
        details = await self.db_service.get_all_in(
            select(CareerDetailsModel).where(col(CareerDetailsModel.work_experience_id).in_(work_experience_ids)),
            session,
        )
        if details:
            newest = max(details, key=lambda row: row.updated_at)
            return newest.work_experience_id
        return work_experience_ids[0]

    async def _merge_career_details(self, session: AsyncSession, keep_id: UUID, work_experience_ids: list[UUID]):
        for work_experience_id in work_experience_ids:
            if work_experience_id == keep_id:
                continue
            details = await self.db_service.get_first_in(
                select(CareerDetailsModel).where(CareerDetailsModel.work_experience_id == work_experience_id),
                session,
            )
            if details is None:
                continue
            kept = await self.db_service.get_first_in(
                select(CareerDetailsModel).where(CareerDetailsModel.work_experience_id == keep_id),
                session,
            )
            if kept is None:
                details.work_experience_id = keep_id
                session.add(details)
            else:
                await session.delete(details)
