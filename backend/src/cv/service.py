import copy
import logging
from typing import Generator, Protocol, TypeVar, assert_never, runtime_checkable
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import col, select

from src.career_details.service import CareerDetailsService
from src.cv._conversion.service import CVDatabaseConversionService
from src.cv._extraction.service import CVExtractionService
from src.cv._sync.service import CVDatabaseSyncService
from src.cv.models.cv import CVModel
from src.cv.models.cv_section import CVSectionModel
from src.cv.views.cv_data import CVData
from src.cv.views.request import CVUpdateRequest
from src.cv.views.response import CVListItemResponse, CVTargetCountryResponse, FullCVContent
from src.db import selectinload, with_database_session
from src.db.service import AsyncSession, DatabaseService
from src.llm.views.prompt.file import FilePrompt
from src.utils.classes import singleton
from src.utils.country_code import CountryCode
from src.utils.supported_language import SupportedLanguage

logger = logging.getLogger(__name__)


@singleton
class CVService:
    def __init__(self):
        self.db_service = DatabaseService()
        self.extraction_service = CVExtractionService()
        self.conversion_service = CVDatabaseConversionService()
        self.sync_service = CVDatabaseSyncService()
        self.career_details_service = CareerDetailsService()

    async def create_cv_from_upload(self, file: UploadFile, user_id: str) -> FullCVContent:
        """Extract a PDF and persist the CV only after successful validation."""
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Invalid file type. Upload a PDF.")
        max_file_size = 10 * 1024 * 1024
        content = await file.read(max_file_size + 1)
        if len(content) > max_file_size:
            raise HTTPException(status_code=413, detail="File too large. Maximum size: 10MB")
        if not content.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="The upload is not a PDF.")

        document = FilePrompt(filename="cv.pdf", content_type="application/pdf", file_data=content)
        try:
            cv_data = await self.extraction_service.extract_cv_data(document, user_id=user_id)
        except HTTPException:
            raise
        except Exception as error:
            logger.warning(f"CV extraction failed: {type(error).__name__}")
            raise HTTPException(status_code=502, detail="CV extraction failed. Please try again.") from error

        cv_model = self.conversion_service.convert_cv_data_to_model(cv_data, user_id=user_id)
        await self.db_service.add(cv_model)
        await self.career_details_service.rematch_for_user(user_id)
        return await self.conversion_service.convert_cv_data_for_api(cv_data)

    async def create_empty_cv(self, user_id: str, language: SupportedLanguage) -> FullCVContent:
        """Create a new empty CV with default sections but no content."""
        cv_data = CVData(
            id=uuid4(),
            cv_name="CV",
            cv_language=language,
            target_country_code=None,
            style=CVData.Style(template_id="classic", accent_color=None),
            personal_details=CVData.PersonalDetails(
                first_name="",
                last_name="",
                professional_title=None,
                email=None,
                phone=None,
                street_address=None,
                city=None,
                state=None,
                postal_code=None,
                country=None,
                date_of_birth=None,
                place_of_birth=None,
                nationality=None,
                marital_status=None,
                driving_license=None,
                personal_website=None,
            ),
            professional_summary=None,
            sections=[
                CVData.SocialLinkSection(id=uuid4(), social_links=[]),
                CVData.EmploymentHistorySection(id=uuid4(), employment=[]),
                CVData.EducationSection(id=uuid4(), education=[]),
                CVData.SkillsSection(id=uuid4(), groups=[]),
                CVData.LanguagesSection(id=uuid4(), languages=[]),
            ],
            footer_sections=CVData.FooterSections(privacy_clause=None, signature=None),
        )

        cv_model = self.conversion_service.convert_cv_data_to_model(cv_data, user_id=user_id)
        await self.db_service.add(cv_model)

        return await self.conversion_service.convert_cv_data_for_api(cv_data)

    async def list_cvs(self, user_id: str) -> list[CVListItemResponse]:
        """List the user's CVs, including independent copies."""
        cv_models = await self.db_service.get_all_in(
            select(CVModel).where(CVModel.user_id == user_id).order_by(col(CVModel.updated_at).desc())
        )

        return [
            CVListItemResponse(
                id=cv.id,
                cv_name=cv.cv_name,
                first_name=cv.first_name,
                last_name=cv.last_name,
                email=cv.email,
                created_at=cv.created_at,
                updated_at=cv.updated_at,
            )
            for cv in cv_models
        ]

    async def _get_full_cv_model(self, cv_id: UUID, user_id: str, session: AsyncSession | None = None) -> CVModel | None:
        return await self.db_service.get_first_in(
            select(CVModel)
            .where(CVModel.id == cv_id, CVModel.user_id == user_id)
            .options(
                selectinload(CVModel.sections).selectinload(CVSectionModel.items),
                selectinload(CVModel.sections).selectinload(CVSectionModel.attributes),
            ),
            session,
        )

    async def get_cv_by_id(self, cv_id: UUID, user_id: str) -> FullCVContent | None:
        """Get CV by ID with user authorization check."""
        cv_model = await self._get_full_cv_model(cv_id, user_id)
        if not cv_model:
            return None

        cv_data = self.conversion_service.convert_model_to_cv_data(cv_model)
        return await self.conversion_service.convert_cv_data_for_api(cv_data)

    async def get_cv_data_by_id(self, cv_id: UUID, user_id: str) -> CVData | None:
        cv_model = await self._get_full_cv_model(cv_id, user_id)
        if not cv_model:
            return None
        return self.conversion_service.convert_model_to_cv_data(cv_model)

    async def get_cv_target_country(self, cv_id: UUID, user_id: str) -> CVTargetCountryResponse | None:
        cv_model = await self.db_service.get_first_in(select(CVModel).where(CVModel.id == cv_id, CVModel.user_id == user_id))
        if not cv_model:
            return None
        return CVTargetCountryResponse(target_country_code=cv_model.target_country_code)

    async def update_cv(self, cv_id: UUID, request: CVUpdateRequest, user_id: str) -> FullCVContent | None:
        """Update an existing CV with authorization check."""
        # Fetch the existing CV and verify ownership
        existing_cv_model = await self._get_full_cv_model(cv_id, user_id)
        if not existing_cv_model:
            return None

        # Convert request to CVData
        cv_data = self._convert_update_request_to_cv_data(request, existing_cv_model)

        # Delegate the synchronization to the sync service
        updated_cv_model = await self.sync_service.sync_to_database(cv_data)
        await self.career_details_service.rematch_for_user(user_id)

        # Convert back for API response
        final_cv_data = self.conversion_service.convert_model_to_cv_data(updated_cv_model)
        return await self.conversion_service.convert_cv_data_for_api(final_cv_data)

    @with_database_session
    async def update_cv_target_country(
        self, session: AsyncSession, cv_id: UUID, country_code: CountryCode, user_id: str
    ) -> FullCVContent | None:
        cv_model = await self._get_full_cv_model(cv_id, user_id, session)
        if not cv_model:
            return None

        cv_model.target_country_code = country_code
        await session.commit()

        cv_data = self.conversion_service.convert_model_to_cv_data(cv_model)
        return await self.conversion_service.convert_cv_data_for_api(cv_data)

    def _convert_update_request_to_cv_data(self, request: CVUpdateRequest, existing_cv_model: CVModel) -> CVData:
        """Convert CVUpdateRequest to CVData, generating UUIDs for new entities."""

        existing_cv_data = self.conversion_service.convert_model_to_cv_data(existing_cv_model)

        allowed_section_ids = {section.id for section in existing_cv_model.sections}
        # Combine item and attribute IDs since some sections use attributes (skills, languages, etc.)
        allowed_entity_ids = {item.id for section in existing_cv_model.sections for item in section.items} | {
            attribute.id for section in existing_cv_model.sections for attribute in section.attributes
        }

        # Process sections, validating and generating UUIDs where needed
        processed_sections = []
        for section in request.sections:
            # Validate section ID
            if section.id is not None and section.id not in allowed_section_ids:
                logger.error(f"Disallowed section id: {section.id}. Section does not exist in current CV. Can't request with new ids.")
                raise HTTPException(status_code=400, detail=f"Disallowed section id: {section.id}")

            # Generate UUID for section if None
            section_id = section.id or uuid4()

            class ItemIdentifiable(Protocol):
                id: UUID | None

            def verified_item_id(item: ItemIdentifiable) -> UUID:
                if item.id is not None and item.id not in allowed_entity_ids:
                    logger.error(f"Disallowed entity id: {item.id}. Entity does not exist in current CV. Can't request with new ids.")
                    raise HTTPException(status_code=400, detail=f"Disallowed entity id: {item.id}")
                return item.id or uuid4()

            # Process based on section type with type-safe pattern matching
            if isinstance(section, CVUpdateRequest.SocialLinkSection):
                processed_sections.append(
                    CVData.SocialLinkSection(
                        id=section_id,
                        social_links=[
                            CVData.SocialLinkSection.Item(id=verified_item_id(item), label=item.label, url=item.url)
                            for item in section.social_links
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.EmploymentHistorySection):
                processed_sections.append(
                    CVData.EmploymentHistorySection(
                        id=section_id,
                        employment=[
                            CVData.EmploymentHistorySection.Item(
                                id=verified_item_id(item),
                                start_date=item.start_date,
                                end_date=item.end_date,
                                job_title=item.job_title,
                                employer=item.employer,
                                city=item.city,
                                description=item.description,
                            )
                            for item in section.employment
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.EducationSection):
                processed_sections.append(
                    CVData.EducationSection(
                        id=section_id,
                        education=[
                            CVData.EducationSection.Item(
                                id=verified_item_id(item),
                                start_date=item.start_date,
                                end_date=item.end_date,
                                school_name=item.school_name,
                                degree=item.degree,
                                city=item.city,
                                description=item.description,
                            )
                            for item in section.education
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.SkillsSection):
                processed_sections.append(
                    CVData.SkillsSection(
                        id=section_id,
                        groups=[
                            CVData.SkillsSection.SkillGroup(
                                name=group.name,
                                skills=[
                                    CVData.SkillsSection.SkillGroup.Item(
                                        id=verified_item_id(item), skill_name=item.skill_name, level=item.level
                                    )
                                    for item in group.skills
                                ],
                            )
                            for group in section.groups
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.LanguagesSection):
                processed_sections.append(
                    CVData.LanguagesSection(
                        id=section_id,
                        languages=[
                            CVData.LanguagesSection.Item(id=verified_item_id(item), language=item.language, level=item.level)
                            for item in section.languages
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.AwardsSection):
                processed_sections.append(
                    CVData.AwardsSection(
                        id=section_id,
                        awards=[
                            CVData.AwardsSection.Item(
                                id=verified_item_id(item),
                                name=item.name,
                                city=item.city,
                                start_date=item.start_date,
                                end_date=item.end_date,
                                description=item.description,
                            )
                            for item in section.awards
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.ExtraCurricularActivitiesSection):
                processed_sections.append(
                    CVData.ExtraCurricularActivitiesSection(
                        id=section_id,
                        extra_curricular_activities=[
                            CVData.ExtraCurricularActivitiesSection.Item(
                                id=verified_item_id(item),
                                function_title=item.function_title,
                                employer=item.employer,
                                start_date=item.start_date,
                                end_date=item.end_date,
                                city=item.city,
                                description=item.description,
                            )
                            for item in section.extra_curricular_activities
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.CoursesSection):
                processed_sections.append(
                    CVData.CoursesSection(
                        id=section_id,
                        courses=[
                            CVData.CoursesSection.Item(
                                id=verified_item_id(item),
                                course=item.course,
                                institution=item.institution,
                                start_date=item.start_date,
                                end_date=item.end_date,
                            )
                            for item in section.courses
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.HobbiesSection):
                processed_sections.append(
                    CVData.HobbiesSection(
                        id=section_id,
                        hobbies=[CVData.HobbiesSection.Item(id=verified_item_id(item), hobby=item.hobby) for item in section.hobbies],
                    )
                )

            elif isinstance(section, CVUpdateRequest.ReferencesSection):
                processed_sections.append(
                    CVData.ReferencesSection(
                        id=section_id,
                        references=[
                            CVData.ReferencesSection.Item(
                                id=verified_item_id(item),
                                referent_full_name=item.referent_full_name,
                                company_name=item.company_name,
                                phone=item.phone,
                                email=item.email,
                            )
                            for item in section.references
                        ],
                    )
                )

            elif isinstance(section, CVUpdateRequest.CustomSection):
                # Process custom section content - unwrap discriminated union
                if isinstance(section.content, CVUpdateRequest.CustomSection.TextContent):
                    processed_content = section.content.text
                elif isinstance(section.content, CVUpdateRequest.CustomSection.StructuredContent):
                    processed_content = [
                        CVData.CustomSection.ContentItem(
                            id=verified_item_id(item),
                            title=item.title,
                            start_date=item.start_date,
                            end_date=item.end_date,
                            city=item.city,
                            description=item.description,
                        )
                        for item in section.content.items
                    ]
                else:
                    assert_never(section.content)

                processed_sections.append(
                    CVData.CustomSection(
                        id=section_id,
                        title=section.title,
                        content=processed_content,
                    )
                )

            else:
                assert_never(section)

        return CVData(
            id=request.id,
            cv_name=request.cv_name,
            cv_language=request.cv_language,
            target_country_code=existing_cv_data.target_country_code,
            style=request.style,
            personal_details=request.personal_details,
            professional_summary=request.professional_summary,
            sections=processed_sections,
            footer_sections=request.footer_sections,
        )

    def _clone_cv_data_with_new_ids(self, cv_data: CVData, new_cv_name: str | None = None) -> CVData:
        """
        Return a deep-cloned `CVData` with fresh UUIDs for the CV, all sections, and all nested items/attributes.

        Behavior and invariants:
        - Only `id` fields are regenerated recursively. All other content is preserved 1:1.
        - The source `cv_data` is never mutated.
        - If `new_cv_name` is provided, the clone's `cv_name` is set to that value; otherwise the original name is retained.
        """

        @runtime_checkable
        class UUIDIdentifiable(Protocol):
            id: UUID

        Identifiable_T = TypeVar("Identifiable_T", bound=UUIDIdentifiable)

        def subitems_of(item: UUIDIdentifiable) -> Generator[UUIDIdentifiable, None, None]:
            if isinstance(item, BaseModel):
                for _, value in item:
                    if isinstance(value, list):
                        for value_item in value:
                            if isinstance(value_item, UUIDIdentifiable):
                                yield value_item
                            elif isinstance(value_item, CVData.SkillsSection.SkillGroup):
                                # special case: SkillGroup has no id but contains skills with ids
                                for skill in value_item.skills:
                                    yield skill
                    elif isinstance(value, UUIDIdentifiable):
                        yield value

        def randomize_all_ids(item: Identifiable_T) -> Identifiable_T:
            for subitem in subitems_of(item):
                randomize_all_ids(subitem)

            item.id = uuid4()
            return item

        # base clone
        new_cv_data = copy.deepcopy(cv_data)

        # update ids recursively
        randomize_all_ids(new_cv_data)

        if new_cv_name is not None:
            new_cv_data.cv_name = new_cv_name

        return new_cv_data

    async def import_cv(self, cv_data: CVData, user_id: str) -> FullCVContent:
        """Import structured CV data as an independent CV with fresh IDs."""
        imported = self._clone_cv_data_with_new_ids(cv_data)
        model = self.conversion_service.convert_cv_data_to_model(imported, user_id)
        await self.db_service.add(model)
        await self.career_details_service.rematch_for_user(user_id)
        return await self.conversion_service.convert_cv_data_for_api(imported)

    async def duplicate_cv(self, cv_id: UUID, user_id: str) -> FullCVContent | None:
        source = await self.get_cv_data_by_id(cv_id, user_id)
        if source is None:
            return None
        copied = self._clone_cv_data_with_new_ids(source)
        model = self.conversion_service.convert_cv_data_to_model(copied, user_id)
        model.parent_cv_id = source.id
        await self.db_service.add(model)
        await self.career_details_service.rematch_for_user(user_id)
        return await self.conversion_service.convert_cv_data_for_api(copied)

    @with_database_session
    async def delete_cv(self, session: AsyncSession, cv_id: UUID, user_id: str) -> bool:
        model = await self._get_full_cv_model(cv_id, user_id, session)
        if model is None:
            return False
        await session.delete(model)
        await session.commit()
        return True
