import html
from typing import OrderedDict, assert_never, overload
from uuid import UUID

from src.cv.models.cv import CVLanguage, CVModel, DatePosition, TextAlignment
from src.cv.models.cv_attribute import CVAttributeLanguageLevel, CVAttributeModel, CVAttributeSkillLevel
from src.cv.models.cv_item import CVItemModel
from src.cv.models.cv_section import CVSectionModel, CVSectionType
from src.cv.views.cv_data import ApproximateDate, CVData, LanguageLevel, SkillLevel
from src.cv.views.response import FullCVContent
from src.cv.views.style import ALL_CV_FONT_FAMILIES, CVFontFamily
from src.utils.classes import singleton


@singleton
class CVDatabaseConversionService:
    # region: - CVData <-> CVModel

    def convert_cv_data_to_model(self, cv_data: CVData, user_id: str) -> CVModel:
        pd = cv_data.personal_details

        professional_summary_text = cv_data.professional_summary.summary if cv_data.professional_summary else None

        cv_model = CVModel(
            id=cv_data.id,
            user_id=user_id,
            cv_name=cv_data.cv_name,
            cv_language=CVLanguage.from_language_code(cv_data.cv_language),
            target_country_code=cv_data.target_country_code,
            template_id=cv_data.style.template_id,
            accent_color=cv_data.style.accent_color,
            section_spacing=cv_data.style.section_spacing,
            line_spacing=cv_data.style.line_spacing,
            margin_spacing=cv_data.style.margin_spacing,
            date_position=DatePosition.from_string(cv_data.style.date_position) if cv_data.style.date_position else None,
            text_alignment=TextAlignment.from_string(cv_data.style.text_alignment) if cv_data.style.text_alignment else None,
            font_size=cv_data.style.font_size,
            font_family=cv_data.style.font_family,
            content_font_scale=cv_data.style.content_font_scale,
            heading_font_scale=cv_data.style.heading_font_scale,
            first_name=pd.first_name,
            last_name=pd.last_name,
            professional_title=pd.professional_title,
            email=pd.email,
            phone=pd.phone,
            street_address=pd.street_address,
            city=pd.city,
            state=pd.state,
            postal_code=pd.postal_code,
            country=pd.country,
            date_of_birth=pd.date_of_birth,
            place_of_birth=pd.place_of_birth,
            nationality=pd.nationality,
            marital_status=pd.marital_status,
            driving_license=pd.driving_license,
            personal_website=pd.personal_website,
            professional_summary=professional_summary_text,
            privacy_clause_enabled=cv_data.footer_sections.privacy_clause is not None,
        )

        # Persist signature settings
        if signature := cv_data.footer_sections.signature:
            cv_model.signature_enabled = True
            cv_model.signature_location = signature.location
            cv_model.signature_include_date = signature.include_date
            cv_model.signature_show_name = signature.show_name

        # Build DB sections from discriminated union
        for section in cv_data.sections:
            if isinstance(section, CVData.SocialLinkSection):
                cv_model.sections.append(self._convert_social_link_section_to_db(section, cv_model))
            elif isinstance(section, CVData.EmploymentHistorySection):
                cv_model.sections.append(self._convert_employment_history_section_to_db(section, cv_model))
            elif isinstance(section, CVData.EducationSection):
                cv_model.sections.append(self._convert_education_section_to_db(section, cv_model))
            elif isinstance(section, CVData.SkillsSection):
                cv_model.sections.append(self._convert_skill_section_to_db(section, cv_model))
            elif isinstance(section, CVData.LanguagesSection):
                cv_model.sections.append(self._convert_language_section_to_db(section, cv_model))
            elif isinstance(section, CVData.AwardsSection):
                cv_model.sections.append(self._convert_award_section_to_db(section, cv_model))
            elif isinstance(section, CVData.ExtraCurricularActivitiesSection):
                cv_model.sections.append(self._convert_extra_curricular_activity_section_to_db(section, cv_model))
            elif isinstance(section, CVData.CoursesSection):
                cv_model.sections.append(self._convert_course_section_to_db(section, cv_model))
            elif isinstance(section, CVData.HobbiesSection):
                cv_model.sections.append(self._convert_hobby_section_to_db(section, cv_model))
            elif isinstance(section, CVData.ReferencesSection):
                cv_model.sections.append(self._convert_reference_section_to_db(section, cv_model))
            elif isinstance(section, CVData.CustomSection):
                cv_model.sections.append(self._convert_custom_section_to_db(section, cv_model))
            else:
                assert_never(section)  # only for type checking

        # ensure unique and stable ordering across all sections
        for index, section in enumerate(cv_model.sections):
            section.position = index

        return cv_model

    def convert_model_to_cv_data(self, cv_model: CVModel) -> CVData:
        personal_details = CVData.PersonalDetails(
            first_name=cv_model.first_name,
            last_name=cv_model.last_name,
            professional_title=cv_model.professional_title,
            email=cv_model.email,
            phone=cv_model.phone,
            street_address=cv_model.street_address,
            city=cv_model.city,
            state=cv_model.state,
            postal_code=cv_model.postal_code,
            country=cv_model.country,
            date_of_birth=cv_model.date_of_birth,
            place_of_birth=cv_model.place_of_birth,
            nationality=cv_model.nationality,
            marital_status=cv_model.marital_status,
            driving_license=cv_model.driving_license,
            personal_website=cv_model.personal_website,
        )

        signature = (
            CVData.FooterSections.Signature(
                location=cv_model.signature_location,
                include_date=cv_model.signature_include_date,
                show_name=cv_model.signature_show_name,
            )
            if cv_model.signature_enabled
            else None
        )

        cv_data = CVData(
            id=cv_model.id,
            cv_name=cv_model.cv_name,
            cv_language=cv_model.cv_language.language_code,
            target_country_code=cv_model.target_country_code,
            style=CVData.Style(
                template_id=cv_model.template_id or "classic",
                accent_color=cv_model.accent_color,
                section_spacing=cv_model.section_spacing or 1.0,
                line_spacing=cv_model.line_spacing or 1.0,
                margin_spacing=cv_model.margin_spacing or 1.0,
                date_position=cv_model.date_position.value if cv_model.date_position else None,
                text_alignment=cv_model.text_alignment.value if cv_model.text_alignment else None,
                font_size=cv_model.font_size or 1.0,
                font_family=self._font_family_db_to_data(cv_model.font_family),
                content_font_scale=cv_model.content_font_scale or 1.0,
                heading_font_scale=cv_model.heading_font_scale or 1.0,
            ),
            personal_details=personal_details,
            professional_summary=(
                CVData.ProfessionalSummary(summary=cv_model.professional_summary) if cv_model.professional_summary else None
            ),
            sections=[],
            footer_sections=CVData.FooterSections(
                privacy_clause=CVData.FooterSections.PrivacyClause() if cv_model.privacy_clause_enabled else None,
                signature=signature,
            ),
        )

        # Map other sections by their position using match
        for section in sorted(cv_model.sections, key=lambda s: s.position):
            match section.type:
                case CVSectionType.social_links:
                    if new_section := self._convert_social_link_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.employment:
                    if new_section := self._convert_employment_history_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.education:
                    if new_section := self._convert_education_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.skills:
                    if new_section := self._convert_skill_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.languages:
                    if new_section := self._convert_language_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.awards:
                    if new_section := self._convert_award_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.extracurricular:
                    if new_section := self._convert_extra_curricular_activity_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.courses:
                    if new_section := self._convert_course_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.hobbies:
                    if new_section := self._convert_hobby_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.references:
                    if new_section := self._convert_reference_section_db_to_data(section):
                        cv_data.sections.append(new_section)
                case CVSectionType.custom:
                    if custom := self._convert_custom_section_db_to_data(section):
                        cv_data.sections.append(custom)
                case _:
                    assert_never(section.type)

        return cv_data

    def _font_family_db_to_data(self, font_family: str | None) -> CVFontFamily | None:
        if font_family is None:
            return None

        if font_family in ALL_CV_FONT_FAMILIES:
            return font_family

        raise ValueError(f"Unsupported CV font family stored in database: {font_family}")

    # endregion

    # region: - CVData <-> FullCVContent

    async def convert_cv_data_for_api(self, cv_data: CVData) -> FullCVContent:
        full_cv_content = FullCVContent(
            id=cv_data.id,
            cv_name=cv_data.cv_name,
            cv_language=cv_data.cv_language,
            style=cv_data.style,
            personal_details=cv_data.personal_details,
            professional_summary=cv_data.professional_summary,
            footer_sections=cv_data.footer_sections,
            sections=[],
        )

        # Convert sections, wrapping custom section content in discriminated union
        for section in cv_data.sections:
            if isinstance(section, CVData.CustomSection):
                # Convert custom section content to discriminated union
                if isinstance(section.content, str):
                    content = FullCVContent.CustomSection.TextContent(text=section.content)
                else:  # list[ContentItem]
                    content = FullCVContent.CustomSection.StructuredContent(items=section.content)

                full_cv_content.sections.append(FullCVContent.CustomSection(id=section.id, title=section.title, content=content))
            else:
                full_cv_content.sections.append(section)

        return full_cv_content

    # def convert_api_to_cv_data(self, full_cv_content: FullCVContent) -> CVData:
    #     raise NotImplementedError

    # endregion

    # region: - Social Links

    def _convert_social_link_to_db(self, item: CVData.SocialLinkSection.Item, section: CVSectionModel) -> CVAttributeModel:
        return CVAttributeModel(
            id=item.id,
            section_id=section.id,
            name=item.label,
            url=item.url,
        )

    def _convert_social_link_section_to_db(
        self, section: CVData.SocialLinkSection, cv: CVModel, section_id: UUID | None = None
    ) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.social_links,
            title=None,
            position=0,
        )
        db_section.attributes = [
            self._convert_social_link_to_db(item, db_section).with_position(pos) for pos, item in enumerate(section.social_links)
        ]
        return db_section

    def _convert_social_link_section_db_to_data(self, section: CVSectionModel | None) -> CVData.SocialLinkSection | None:
        if section is None:
            return None
        items = [
            CVData.SocialLinkSection.Item(id=attribute.id, label=attribute.name, url=attribute.url)
            for attribute in section.attributes
            if attribute.url
        ]
        return CVData.SocialLinkSection(
            id=section.id,
            social_links=items,
        )

    # endregion
    # region: - Employment History

    def _convert_employment_history_to_db(self, item: CVData.EmploymentHistorySection.Item, section: CVSectionModel) -> CVItemModel:
        sy, sm = self._year_month(item.start_date)
        ey, em = self._year_month(item.end_date)
        return CVItemModel(
            id=item.id,
            section_id=section.id,
            title=item.job_title,
            organization=item.employer,
            city=item.city,
            description=item.description,
            start_year=sy,
            start_month=sm,
            end_year=ey,
            end_month=em,
        )

    def _convert_employment_history_section_to_db(self, section: CVData.EmploymentHistorySection, cv: CVModel) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.employment,
            title=None,
            position=0,
        )
        db_section.items = [
            self._convert_employment_history_to_db(item, db_section).with_position(pos) for pos, item in enumerate(section.employment)
        ]
        return db_section

    def _convert_employment_history_section_db_to_data(self, section: CVSectionModel | None) -> CVData.EmploymentHistorySection | None:
        if section is None:
            return None
        items = [
            CVData.EmploymentHistorySection.Item(
                id=item.id,
                job_title=self._unescape(item.title),
                employer=self._unescape(item.organization),
                city=self._unescape(item.city),
                description=item.description,
                start_date=self._approximate_date(year=item.start_year, month=item.start_month),
                end_date=self._approximate_date(year=item.end_year, month=item.end_month),
            )
            for item in section.items
        ]
        return CVData.EmploymentHistorySection(id=section.id, employment=items)

    # endregion
    # region: - Education

    def _convert_education_to_db(self, item: CVData.EducationSection.Item, section: CVSectionModel) -> CVItemModel:
        sy, sm = self._year_month(item.start_date)
        ey, em = self._year_month(item.end_date)

        return CVItemModel(
            id=item.id,
            section_id=section.id,
            title=item.degree,
            organization=item.school_name,
            city=item.city,
            description=item.description,
            start_year=sy,
            start_month=sm,
            end_year=ey,
            end_month=em,
        )

    def _convert_education_section_to_db(self, section: CVData.EducationSection, cv: CVModel) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.education,
            title=None,
            position=0,
        )
        db_section.items = [
            self._convert_education_to_db(item, db_section).with_position(pos) for pos, item in enumerate(section.education)
        ]
        return db_section

    def _convert_education_section_db_to_data(self, section: CVSectionModel | None) -> CVData.EducationSection | None:
        if section is None:
            return None
        items = [
            CVData.EducationSection.Item(
                id=item.id,
                degree=self._unescape(item.title),
                school_name=self._unescape(item.organization),
                city=self._unescape(item.city),
                description=item.description,
                start_date=self._approximate_date(year=item.start_year, month=item.start_month),
                end_date=self._approximate_date(year=item.end_year, month=item.end_month),
            )
            for item in section.items
        ]
        return CVData.EducationSection(id=section.id, education=items)

    # endregion
    # region: - Skills

    def _convert_skill_level_literal_to_enum(self, level: SkillLevel) -> CVAttributeSkillLevel:
        """Explicitly convert skill level literal to enum (to catch type mismatches later)."""
        match level:
            case "novice":
                return CVAttributeSkillLevel.novice
            case "beginner":
                return CVAttributeSkillLevel.beginner
            case "skillful":
                return CVAttributeSkillLevel.skillful
            case "experienced":
                return CVAttributeSkillLevel.experienced
            case "expert":
                return CVAttributeSkillLevel.expert

    def _convert_skill_level_enum_to_literal(self, level: CVAttributeSkillLevel) -> SkillLevel:
        match level:
            case CVAttributeSkillLevel.novice:
                return "novice"
            case CVAttributeSkillLevel.beginner:
                return "beginner"
            case CVAttributeSkillLevel.skillful:
                return "skillful"
            case CVAttributeSkillLevel.experienced:
                return "experienced"
            case CVAttributeSkillLevel.expert:
                return "expert"

    def _convert_skill_to_db(
        self, item: CVData.SkillsSection.SkillGroup.Item, section: CVSectionModel, group_name: str | None
    ) -> CVAttributeModel:
        return CVAttributeModel(
            id=item.id,
            section_id=section.id,
            name=item.skill_name,
            skill_level=(self._convert_skill_level_literal_to_enum(item.level) if item.level else None),
            skill_group_name=group_name,
        )

    def _convert_skill_section_to_db(self, section: CVData.SkillsSection, cv: CVModel) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.skills,
            title=None,
            position=0,
        )
        # Flatten all skills from all groups, preserving position across groups
        attributes: list[CVAttributeModel] = []
        pos = 0
        for group in section.groups:
            for skill in group.skills:
                attributes.append(self._convert_skill_to_db(skill, db_section, group.name).with_position(pos))
                pos += 1
        db_section.attributes = attributes
        return db_section

    def _convert_skill_section_db_to_data(self, section: CVSectionModel | None) -> CVData.SkillsSection | None:
        if section is None:
            return None

        groups = OrderedDict[str | None, CVData.SkillsSection.SkillGroup]()

        for attribute in section.attributes:
            group_name = attribute.skill_group_name
            if group_name not in groups:
                groups[group_name] = CVData.SkillsSection.SkillGroup(name=group_name, skills=[])

            item = CVData.SkillsSection.SkillGroup.Item(
                id=attribute.id,
                skill_name=attribute.name,
                level=(self._convert_skill_level_enum_to_literal(attribute.skill_level) if attribute.skill_level else None),
            )
            groups[group_name].skills.append(item)

        return CVData.SkillsSection(id=section.id, groups=list(groups.values()))

    # endregion
    # region: - Languages

    def _convert_language_level_literal_to_enum(self, level: LanguageLevel) -> CVAttributeLanguageLevel:
        """Explicitly convert language level literal to enum (to catch type mismatches later)."""
        match level:
            case "A1":
                return CVAttributeLanguageLevel.A1
            case "A2":
                return CVAttributeLanguageLevel.A2
            case "B1":
                return CVAttributeLanguageLevel.B1
            case "B2":
                return CVAttributeLanguageLevel.B2
            case "C1":
                return CVAttributeLanguageLevel.C1
            case "C2":
                return CVAttributeLanguageLevel.C2
            case "basic":
                return CVAttributeLanguageLevel.basic
            case "elementary":
                return CVAttributeLanguageLevel.elementary
            case "intermediate":
                return CVAttributeLanguageLevel.intermediate
            case "advanced":
                return CVAttributeLanguageLevel.advanced
            case "fluent":
                return CVAttributeLanguageLevel.fluent
            case "native":
                return CVAttributeLanguageLevel.native
            case "conversational":
                return CVAttributeLanguageLevel.conversational
            case "professional":
                return CVAttributeLanguageLevel.professional

    def _convert_language_level_enum_to_literal(self, level: CVAttributeLanguageLevel) -> LanguageLevel:
        match level:
            case CVAttributeLanguageLevel.A1:
                return "A1"
            case CVAttributeLanguageLevel.A2:
                return "A2"
            case CVAttributeLanguageLevel.B1:
                return "B1"
            case CVAttributeLanguageLevel.B2:
                return "B2"
            case CVAttributeLanguageLevel.C1:
                return "C1"
            case CVAttributeLanguageLevel.C2:
                return "C2"
            case CVAttributeLanguageLevel.basic:
                return "basic"
            case CVAttributeLanguageLevel.elementary:
                return "elementary"
            case CVAttributeLanguageLevel.intermediate:
                return "intermediate"
            case CVAttributeLanguageLevel.advanced:
                return "advanced"
            case CVAttributeLanguageLevel.fluent:
                return "fluent"
            case CVAttributeLanguageLevel.native:
                return "native"
            case CVAttributeLanguageLevel.conversational:
                return "conversational"
            case CVAttributeLanguageLevel.professional:
                return "professional"

    def _convert_language_to_db(self, item: CVData.LanguagesSection.Item, section: CVSectionModel) -> CVAttributeModel:
        return CVAttributeModel(
            id=item.id,
            section_id=section.id,
            name=item.language,
            language_level=(self._convert_language_level_literal_to_enum(item.level) if item.level else None),
        )

    def _convert_language_section_to_db(self, section: CVData.LanguagesSection, cv: CVModel) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.languages,
            title=None,
            position=0,
        )
        db_section.attributes = [
            self._convert_language_to_db(item, db_section).with_position(pos) for pos, item in enumerate(section.languages)
        ]
        return db_section

    def _convert_language_section_db_to_data(self, section: CVSectionModel | None) -> CVData.LanguagesSection | None:
        if section is None:
            return None
        items = [
            CVData.LanguagesSection.Item(
                id=attribute.id,
                language=attribute.name,
                level=(self._convert_language_level_enum_to_literal(attribute.language_level) if attribute.language_level else None),
            )
            for attribute in section.attributes
        ]
        return CVData.LanguagesSection(id=section.id, languages=items)

    # endregion
    # region: - Awards

    def _convert_award_to_db(self, item: CVData.AwardsSection.Item, section: CVSectionModel) -> CVItemModel:
        sy, sm = self._year_month(item.start_date)
        ey, em = self._year_month(item.end_date)
        return CVItemModel(
            id=item.id,
            section_id=section.id,
            title=item.name,
            organization=None,
            city=item.city,
            description=item.description,
            start_year=sy,
            start_month=sm,
            end_year=ey,
            end_month=em,
        )

    def _convert_award_section_to_db(self, section: CVData.AwardsSection, cv: CVModel) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.awards,
            title=None,
            position=0,
        )
        db_section.items = [self._convert_award_to_db(item, db_section).with_position(pos) for pos, item in enumerate(section.awards)]
        return db_section

    def _convert_award_section_db_to_data(self, section: CVSectionModel | None) -> CVData.AwardsSection | None:
        if section is None:
            return None
        items = [
            CVData.AwardsSection.Item(
                id=item.id,
                name=self._unescape(item.title),
                city=self._unescape(item.city),
                description=item.description,
                start_date=self._approximate_date(year=item.start_year, month=item.start_month),
                end_date=self._approximate_date(year=item.end_year, month=item.end_month),
            )
            for item in section.items
            if item.title is not None
        ]
        return CVData.AwardsSection(id=section.id, awards=items)

    # endregion
    # region: - Extra Curricular Activities

    def _convert_extra_curricular_activity_to_db(
        self, item: CVData.ExtraCurricularActivitiesSection.Item, section: CVSectionModel
    ) -> CVItemModel:
        sy, sm = self._year_month(item.start_date)
        ey, em = self._year_month(item.end_date)
        return CVItemModel(
            id=item.id,
            section_id=section.id,
            title=item.function_title,
            organization=item.employer,
            city=item.city,
            description=item.description,
            start_year=sy,
            start_month=sm,
            end_year=ey,
            end_month=em,
        )

    def _convert_extra_curricular_activity_section_to_db(
        self, section: CVData.ExtraCurricularActivitiesSection, cv: CVModel
    ) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.extracurricular,
            title=None,
            position=0,
        )
        db_section.items = [
            self._convert_extra_curricular_activity_to_db(item, db_section).with_position(pos)
            for pos, item in enumerate(section.extra_curricular_activities)
        ]
        return db_section

    def _convert_extra_curricular_activity_section_db_to_data(
        self, section: CVSectionModel | None
    ) -> CVData.ExtraCurricularActivitiesSection | None:
        if section is None:
            return None
        items = [
            CVData.ExtraCurricularActivitiesSection.Item(
                id=item.id,
                function_title=self._unescape(item.title),
                employer=self._unescape(item.organization),
                city=self._unescape(item.city),
                description=item.description,
                start_date=self._approximate_date(year=item.start_year, month=item.start_month),
                end_date=self._approximate_date(year=item.end_year, month=item.end_month),
            )
            for item in section.items
            if item.title is not None
        ]
        return CVData.ExtraCurricularActivitiesSection(id=section.id, extra_curricular_activities=items)

    # endregion
    # region: - Courses

    def _convert_course_to_db(self, item: CVData.CoursesSection.Item, section: CVSectionModel) -> CVItemModel:
        sy, sm = self._year_month(item.start_date)
        ey, em = self._year_month(item.end_date)
        return CVItemModel(
            id=item.id,
            section_id=section.id,
            title=item.course,
            organization=item.institution,
            city=None,
            description=None,
            start_year=sy,
            start_month=sm,
            end_year=ey,
            end_month=em,
        )

    def _convert_course_section_to_db(self, section: CVData.CoursesSection, cv: CVModel) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.courses,
            title=None,
            position=0,
        )
        db_section.items = [self._convert_course_to_db(item, db_section).with_position(pos) for pos, item in enumerate(section.courses)]
        return db_section

    def _convert_course_section_db_to_data(self, section: CVSectionModel | None) -> CVData.CoursesSection | None:
        if section is None:
            return None
        items = [
            CVData.CoursesSection.Item(
                id=item.id,
                course=self._unescape(item.title),
                institution=self._unescape(item.organization),
                start_date=self._approximate_date(year=item.start_year, month=item.start_month),
                end_date=self._approximate_date(year=item.end_year, month=item.end_month),
            )
            for item in section.items
            if item.title is not None
        ]
        return CVData.CoursesSection(id=section.id, courses=items)

    # endregion
    # region: - Hobbies

    def _convert_hobby_to_db(self, item: CVData.HobbiesSection.Item, section: CVSectionModel) -> CVAttributeModel:
        return CVAttributeModel(
            id=item.id,
            section_id=section.id,
            name=item.hobby,
        )

    def _convert_hobby_section_to_db(self, section: CVData.HobbiesSection, cv: CVModel) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.hobbies,
            title=None,
            position=0,
        )
        db_section.attributes = [self._convert_hobby_to_db(item, db_section).with_position(pos) for pos, item in enumerate(section.hobbies)]
        return db_section

    def _convert_hobby_section_db_to_data(self, section: CVSectionModel | None) -> CVData.HobbiesSection | None:
        if section is None:
            return None
        items = [CVData.HobbiesSection.Item(id=attribute.id, hobby=attribute.name) for attribute in section.attributes]
        return CVData.HobbiesSection(id=section.id, hobbies=items)

    # endregion
    # region: - References

    def _convert_reference_to_db(self, item: CVData.ReferencesSection.Item, section: CVSectionModel) -> CVAttributeModel:
        return CVAttributeModel(
            id=item.id,
            section_id=section.id,
            name=item.referent_full_name,
            company_name=item.company_name,
            email=item.email,
            phone=item.phone,
        )

    def _convert_reference_section_to_db(self, section: CVData.ReferencesSection, cv: CVModel) -> CVSectionModel:
        db_section = CVSectionModel(
            id=section.id,
            cv_id=cv.id,
            type=CVSectionType.references,
            title=None,
            position=0,
        )
        db_section.attributes = [
            self._convert_reference_to_db(item, db_section).with_position(pos) for pos, item in enumerate(section.references)
        ]
        return db_section

    def _convert_reference_section_db_to_data(self, section: CVSectionModel | None) -> CVData.ReferencesSection | None:
        if section is None:
            return None
        items = [
            CVData.ReferencesSection.Item(
                id=attribute.id,
                referent_full_name=attribute.name,
                company_name=attribute.company_name,
                email=attribute.email,
                phone=attribute.phone,
            )
            for attribute in section.attributes
        ]
        return CVData.ReferencesSection(id=section.id, references=items)

    # endregion
    # region: - Custom Sections

    def _convert_custom_item_to_db(self, item: CVData.CustomSection.ContentItem, section: CVSectionModel) -> CVItemModel:
        sy, sm = self._year_month(item.start_date)
        ey, em = self._year_month(item.end_date)
        return CVItemModel(
            id=item.id,
            section_id=section.id,
            title=item.title,
            organization=None,
            city=item.city,
            description=item.description,
            start_year=sy,
            start_month=sm,
            end_year=ey,
            end_month=em,
        )

    def _convert_custom_section_to_db(self, custom_section: CVData.CustomSection, cv: CVModel) -> CVSectionModel:
        section = CVSectionModel(
            id=custom_section.id,
            cv_id=cv.id,
            type=CVSectionType.custom,
            title=custom_section.title,
            position=0,
        )
        if isinstance(custom_section.content, str):
            section.text_content = custom_section.content
        else:
            section.items = [
                self._convert_custom_item_to_db(item, section).with_position(pos) for pos, item in enumerate(custom_section.content)
            ]
        return section

    def _convert_custom_item_db_to_data(self, item: CVItemModel) -> CVData.CustomSection.ContentItem | None:
        if item.title is None:
            return None

        return CVData.CustomSection.ContentItem(
            id=item.id,
            title=self._unescape(item.title),
            start_date=self._approximate_date(year=item.start_year, month=item.start_month),
            end_date=self._approximate_date(year=item.end_year, month=item.end_month),
            city=self._unescape(item.city),
            description=item.description,
        )

    def _convert_custom_section_db_to_data(self, section: CVSectionModel | None) -> CVData.CustomSection | None:
        if section is None:
            return None
        if section.title is None:
            return None

        if section.text_content is not None:
            return CVData.CustomSection(id=section.id, title=section.title, content=section.text_content)
        else:
            items = [self._convert_custom_item_db_to_data(item) for item in section.items]
            items = [item for item in items if item is not None]
            return CVData.CustomSection(id=section.id, title=section.title, content=items)

    # endregion

    # region: - General Helpers

    def _year_month(self, date_like: ApproximateDate | None) -> tuple[int | None, int | None]:
        if date_like is None:
            return None, None
        return date_like.year, date_like.month

    def _approximate_date(self, year: int | None, month: int | None) -> ApproximateDate | None:
        if year is None:
            return None
        return ApproximateDate(month=month, year=year)

    @overload
    def _unescape(self, text: str) -> str: ...
    @overload
    def _unescape(self, text: None) -> None: ...
    def _unescape(self, text: str | None) -> str | None:
        """
        Unescape HTML entities that may have been double-escaped during parsing.
        `description` is HTML-formatted (and usually correct), but the model sometimes escapes
        other non-HTML fields; this removes that extra escaping.
        """
        if text is None:
            return None
        return html.unescape(text)

    # endregion
