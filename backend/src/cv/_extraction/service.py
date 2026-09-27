import json
import logging
import re
from datetime import datetime
from typing import assert_never
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel

from src.cv._extraction.prompts import CVExtractionPrompt
from src.cv._extraction.views import ApproximateDate as SourceApproximateDate
from src.cv._extraction.views import CVExtractedData, ExtractionValidationError
from src.cv.views.cv_data import ApproximateDate as TargetApproximateDate
from src.cv.views.cv_data import CVData
from src.llm.service import LLMService
from src.llm.views.prompt.file import FilePrompt
from src.utils.classes import singleton

logger = logging.getLogger(__name__)


@singleton
class CVExtractionService:
    def __init__(self):
        self.llm_service = LLMService()

    async def _extract_cv_content_only(self, document: FilePrompt, user_id: str, max_retries: int = 3) -> CVExtractedData:
        prompt = CVExtractionPrompt(document)

        # Initial extraction
        response = await self.llm_service.call_with_structured_output(
            model="gpt-5.6-luna",
            prompt=prompt,
            reasoning_effort="low",
            metadata={
                "prompt": "cv_extraction_v2",
                "user_id": user_id,
            },
        )

        # Validation and retry loop
        for retry_attempt in range(max_retries):
            all_errors = self._validate_cv_extraction_run(response.data)

            if not all_errors:
                # Return when no errors are found
                return response.data

            if retry_attempt == max_retries - 1:
                # Do not persist an extraction that still violates the CV data constraints.
                logger.error(
                    f"CV extraction still contains errors after {max_retries} attempts. Errors: {all_errors[:5]}"  # Log first 5 errors
                )
                raise HTTPException(status_code=502, detail="CV extraction returned invalid data. Please try again.")

            # Build error message in JSONL format for the model
            error_lines = [json.dumps(error) for error in all_errors]
            error_message = "Your previous extraction contained errors. Please fix:\n" + "\n".join(error_lines)

            # Retry with specific error feedback
            response = await self.llm_service.follow_up_with_structured_output(
                model="gpt-5.6-luna",
                message=error_message,
                output_schema=CVExtractedData,
                previous_response=response,
                reasoning_effort="low",
                metadata={
                    "prompt": "cv_extraction_v2_retry",
                    "user_id": user_id,
                    "retry_attempt": str(retry_attempt + 1),
                },
            )

        return response.data

    async def extract_cv_data(self, document: FilePrompt, user_id: str) -> CVData:
        result = await self._extract_cv_content_only(document, user_id=user_id)
        if not result.is_cv:
            raise HTTPException(status_code=422, detail="The document is not a CV.")
        return self._convert_structured_output_to_cv_data(result)

    # region: - Extraction validation (e.g. duplicate sections, control characters)

    def _validate_cv_extraction_run(self, data: CVExtractedData) -> list[ExtractionValidationError]:
        errors_control_chars = self._validate_for_control_characters(data)
        errors_duplicate_sections = self._validate_for_duplicate_sections(data)
        return errors_control_chars + errors_duplicate_sections

    def _validate_for_control_characters(self, data: BaseModel) -> list[ExtractionValidationError]:
        """
        Validates extracted CV data for control characters.

        Returns list of error messages in format:
        "Invalid characters at <json_path>: contains <char_repr>"
        """

        # Control characters pattern: all C0 controls except newline + C1 controls
        CONTROL_CHARS_PATTERN = re.compile(r"[\u0000-\u0009\u000B-\u001F\u007F-\u009F]")

        errors: list[ExtractionValidationError] = []

        def check_string(value: str, path: str):
            match = CONTROL_CHARS_PATTERN.search(value)
            if match:
                char = match.group()
                char_repr = f"\\u{ord(char):04x}"
                errors.append({"error": f"Invalid characters at {path}: contains {char_repr}"})

        def recurse(obj, path: str):
            if obj is None:
                return
            elif isinstance(obj, str):
                check_string(obj, path)
            elif isinstance(obj, BaseModel):
                # Iterate through model fields
                for field_name, field_value in obj:
                    if field_value is not None:
                        recurse(field_value, f"{path}.{field_name}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    recurse(item, f"{path}[{i}]")
            # For other types (int, bool, date, etc.) - skip

        recurse(data, "$")
        return errors

    def _validate_for_duplicate_sections(self, data: CVExtractedData) -> list[ExtractionValidationError]:
        """
        Validates that non-custom section types appear at most once.

        Returns list of error messages in format:
        "Section 'skills' appears 2 times (must appear exactly once)"
        """
        section_counts: dict[str, int] = {}

        for section in data.sections:
            # Get section kind (discriminator field)
            section_kind = section.kind

            # Custom sections are allowed to have duplicates
            if section_kind == "custom":
                continue

            section_counts[section_kind] = section_counts.get(section_kind, 0) + 1

        errors: list[ExtractionValidationError] = []
        for section_kind, count in section_counts.items():
            if count > 1:
                errors.append(
                    {
                        "error": f"Section '{section_kind}' appears {count} times (must appear exactly once)",
                        "resolution_hint": f"Merge all '{section_kind}' sections into a single section containing all items from both sections without duplicates.",  # noqa: E501
                    }
                )

        return errors

    # endregion

    # region: - Conversion

    def _convert_structured_output_to_cv_data(self, structured_output: CVExtractedData) -> CVData:
        def map_approximate_date(input_date: SourceApproximateDate | None) -> TargetApproximateDate | None:
            if input_date is None:
                return None
            return TargetApproximateDate(month=input_date.month, year=input_date.year)

        def map_employment_item(item: CVExtractedData.EmploymentHistorySection.Item) -> CVData.EmploymentHistorySection.Item:
            return CVData.EmploymentHistorySection.Item(
                id=uuid4(),
                start_date=map_approximate_date(item.start_date),
                end_date=map_approximate_date(item.end_date),
                job_title=item.job_title,
                employer=item.employer,
                city=item.city,
                description=item.description,
            )

        def map_education_item(item: CVExtractedData.EducationSection.Item) -> CVData.EducationSection.Item:
            return CVData.EducationSection.Item(
                id=uuid4(),
                start_date=map_approximate_date(item.start_date),
                end_date=map_approximate_date(item.end_date),
                school_name=item.school_name,
                degree=item.degree,
                city=item.city,
                description=item.description,
            )

        def map_award_item(item: CVExtractedData.AwardsSection.Item) -> CVData.AwardsSection.Item:
            return CVData.AwardsSection.Item(
                id=uuid4(),
                name=item.name,
                city=item.city,
                start_date=map_approximate_date(item.start_date),
                end_date=map_approximate_date(item.end_date),
                description=item.description,
            )

        def map_extra_curricular_item(
            item: CVExtractedData.ExtraCurricularActivitiesSection.Item,
        ) -> CVData.ExtraCurricularActivitiesSection.Item:
            return CVData.ExtraCurricularActivitiesSection.Item(
                id=uuid4(),
                function_title=item.function_title,
                employer=item.employer,
                start_date=map_approximate_date(item.start_date),
                end_date=map_approximate_date(item.end_date),
                city=item.city,
                description=item.description,
            )

        def map_course_item(item: CVExtractedData.CoursesSection.Item) -> CVData.CoursesSection.Item:
            return CVData.CoursesSection.Item(
                id=uuid4(),
                course=item.course,
                institution=item.institution,
                start_date=map_approximate_date(item.start_date),
                end_date=map_approximate_date(item.end_date),
            )

        def map_custom_section(section: CVExtractedData.CustomSection) -> CVData.CustomSection:
            if isinstance(section.content, str):
                content: str | list[CVData.CustomSection.ContentItem] = section.content
            else:
                content = [
                    CVData.CustomSection.ContentItem(
                        id=uuid4(),
                        title=c.title,
                        start_date=map_approximate_date(c.start_date),
                        end_date=map_approximate_date(c.end_date),
                        city=c.city,
                        description=c.description,
                    )
                    for c in section.content
                ]
            return CVData.CustomSection(id=uuid4(), title=section.title, content=content)

        source_pd = structured_output.personal_details
        target_pd = CVData.PersonalDetails(
            first_name=source_pd.first_name,
            last_name=source_pd.last_name,
            professional_title=source_pd.professional_title,
            email=source_pd.email,
            phone=source_pd.phone,
            street_address=source_pd.street_address,
            city=source_pd.city,
            state=source_pd.state,
            postal_code=source_pd.postal_code,
            country=source_pd.country,
            date_of_birth=source_pd.date_of_birth.date if source_pd.date_of_birth else None,
            place_of_birth=source_pd.place_of_birth,
            nationality=source_pd.nationality,
            marital_status=None,
            driving_license=source_pd.driving_license,
            personal_website=source_pd.personal_website,
        )

        professional_summary = (
            CVData.ProfessionalSummary(summary=structured_output.professional_summary.summary)
            if structured_output.professional_summary
            else None
        )

        # Generate a default CV name using person's name and current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        default_cv_name = f"{source_pd.first_name} {source_pd.last_name} - CV {current_date}"

        cv_data = CVData(
            id=uuid4(),
            cv_name=default_cv_name,
            cv_language=structured_output.language or "en",
            target_country_code=None,
            style=CVData.Style(template_id="classic", accent_color=None),
            personal_details=target_pd,
            professional_summary=professional_summary,
            sections=[],
            footer_sections=CVData.FooterSections(
                privacy_clause=None,
                signature=None,  # currently not supported in extraction
            ),
        )

        # Iterate over sections in the order they were extracted (preserving original CV order)
        for section in structured_output.sections:
            if isinstance(section, CVExtractedData.SocialLinksSection):
                if section.social_links:
                    cv_data.sections.append(
                        CVData.SocialLinkSection(
                            id=uuid4(),
                            social_links=[
                                CVData.SocialLinkSection.Item(id=uuid4(), label=link.label, url=link.url)
                                for link in section.social_links
                                if link.url
                            ],
                        )
                    )

            elif isinstance(section, CVExtractedData.EmploymentHistorySection):
                if section.employment:
                    cv_data.sections.append(
                        CVData.EmploymentHistorySection(id=uuid4(), employment=[map_employment_item(item) for item in section.employment])
                    )

            elif isinstance(section, CVExtractedData.EducationSection):
                if section.education:
                    cv_data.sections.append(
                        CVData.EducationSection(id=uuid4(), education=[map_education_item(item) for item in section.education])
                    )

            elif isinstance(section, CVExtractedData.SkillsSection):
                if section.groups:
                    cv_data.sections.append(
                        CVData.SkillsSection(
                            id=uuid4(),
                            groups=[
                                CVData.SkillsSection.SkillGroup(
                                    name=g.name,
                                    skills=[
                                        CVData.SkillsSection.SkillGroup.Item(id=uuid4(), skill_name=s.skill_name, level=s.level)
                                        for s in g.skills
                                    ],
                                )
                                for g in section.groups
                            ],
                        )
                    )

            elif isinstance(section, CVExtractedData.LanguagesSection):
                if section.languages:
                    cv_data.sections.append(
                        CVData.LanguagesSection(
                            id=uuid4(),
                            languages=[
                                CVData.LanguagesSection.Item(id=uuid4(), language=lang.language, level=lang.level)
                                for lang in section.languages
                            ],
                        )
                    )

            elif isinstance(section, CVExtractedData.AwardsSection):
                if section.awards:
                    cv_data.sections.append(CVData.AwardsSection(id=uuid4(), awards=[map_award_item(item) for item in section.awards]))

            elif isinstance(section, CVExtractedData.ExtraCurricularActivitiesSection):
                if section.extra_curricular_activities:
                    cv_data.sections.append(
                        CVData.ExtraCurricularActivitiesSection(
                            id=uuid4(),
                            extra_curricular_activities=[map_extra_curricular_item(item) for item in section.extra_curricular_activities],
                        )
                    )

            elif isinstance(section, CVExtractedData.CoursesSection):
                if section.courses:
                    cv_data.sections.append(CVData.CoursesSection(id=uuid4(), courses=[map_course_item(item) for item in section.courses]))

            elif isinstance(section, CVExtractedData.HobbiesSection):
                hobbies = [h for h in section.hobbies if h is not None]
                if hobbies:
                    hobby_items = [CVData.HobbiesSection.Item(id=uuid4(), hobby=h) for h in hobbies]
                    cv_data.sections.append(CVData.HobbiesSection(id=uuid4(), hobbies=hobby_items))

            elif isinstance(section, CVExtractedData.ReferencesSection):
                if section.references:
                    cv_data.sections.append(
                        CVData.ReferencesSection(
                            id=uuid4(),
                            references=[
                                CVData.ReferencesSection.Item(
                                    id=uuid4(),
                                    referent_full_name=r.referent_full_name,
                                    company_name=r.company_name,
                                    phone=r.phone,
                                    email=r.email,
                                )
                                for r in section.references
                            ],
                        )
                    )

            elif isinstance(section, CVExtractedData.PrivacyClauseSection):
                cv_data.footer_sections.privacy_clause = CVData.FooterSections.PrivacyClause()

            elif isinstance(section, CVExtractedData.CustomSection):
                cv_data.sections.append(map_custom_section(section))

            else:
                assert_never(section)

        return cv_data

    # endregion
