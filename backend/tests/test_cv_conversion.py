import datetime
import uuid

# Ensure all SQLModel models are registered before creating instances
import src.db.models  # noqa: F401
from src.cv._conversion.service import CVDatabaseConversionService
from src.cv.models.cv_section import CVSectionType
from src.cv.views.cv_data import ApproximateDate, CVData


def build_sample_cv_data() -> CVData:
    """Build a CVData instance covering all section types."""
    return CVData(
        id=uuid.uuid4(),
        cv_name="Test CV",
        cv_language="en",
        target_country_code="UZ",
        style=CVData.Style(
            template_id="classic",
            accent_color="#2563EB",
            section_spacing=0.9,
            line_spacing=1.1,
            margin_spacing=1.2,
            date_position="trailing",
            text_alignment="justify",
            font_size=0.85,
            font_family="georgia",
            content_font_scale=0.95,
            heading_font_scale=1.15,
        ),
        personal_details=CVData.PersonalDetails(
            first_name="John",
            last_name="Doe",
            professional_title="Software Engineer",
            email="john@example.com",
            phone="123",
            street_address="123 Street",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA",
            date_of_birth=datetime.date(1990, 1, 1),
            place_of_birth="Springfield",
            nationality="American",
            marital_status="Single",
            driving_license="B",
            personal_website="https://example.com",
        ),
        professional_summary=CVData.ProfessionalSummary(summary="Experienced developer"),
        sections=[
            CVData.SocialLinkSection(
                id=uuid.uuid4(),
                social_links=[
                    CVData.SocialLinkSection.Item(
                        id=uuid.uuid4(),
                        label="LinkedIn",
                        url="https://linkedin.com/in/john",
                    ),
                    CVData.SocialLinkSection.Item(
                        id=uuid.uuid4(),
                        label="GitHub",
                        url="https://github.com/johndoe",
                    ),
                ],
            ),
            CVData.EmploymentHistorySection(
                id=uuid.uuid4(),
                employment=[
                    CVData.EmploymentHistorySection.Item(
                        id=uuid.uuid4(),
                        start_date=ApproximateDate(month=1, year=2020),
                        end_date=ApproximateDate(month=12, year=2021),
                        job_title="Developer",
                        employer="Company",
                        city="New York",
                        description="Worked on projects",
                    ),
                    CVData.EmploymentHistorySection.Item(
                        id=uuid.uuid4(),
                        start_date=ApproximateDate(month=1, year=2018),
                        end_date=ApproximateDate(month=12, year=2019),
                        job_title="Engineer",
                        employer="Other Co",
                        city="Boston",
                        description="Built tools",
                    ),
                ],
            ),
            CVData.EducationSection(
                id=uuid.uuid4(),
                education=[
                    CVData.EducationSection.Item(
                        id=uuid.uuid4(),
                        start_date=ApproximateDate(month=9, year=2010),
                        end_date=ApproximateDate(month=6, year=2014),
                        school_name="University",
                        degree="BSc CS",
                        city="New York",
                        description="Studied computer science",
                    ),
                    CVData.EducationSection.Item(
                        id=uuid.uuid4(),
                        start_date=ApproximateDate(month=9, year=2014),
                        end_date=ApproximateDate(month=6, year=2016),
                        school_name="University",
                        degree="MSc CS",
                        city="New York",
                        description="Advanced studies",
                    ),
                ],
            ),
            CVData.SkillsSection(
                id=uuid.uuid4(),
                groups=[
                    CVData.SkillsSection.SkillGroup(
                        name="Programming",
                        skills=[
                            CVData.SkillsSection.SkillGroup.Item(id=uuid.uuid4(), skill_name="Python", level="expert"),
                            CVData.SkillsSection.SkillGroup.Item(id=uuid.uuid4(), skill_name="SQL", level="skillful"),
                        ],
                    ),
                    CVData.SkillsSection.SkillGroup(
                        name="DevOps",
                        skills=[
                            CVData.SkillsSection.SkillGroup.Item(id=uuid.uuid4(), skill_name="Docker", level=None),
                            CVData.SkillsSection.SkillGroup.Item(id=uuid.uuid4(), skill_name="Kubernetes", level="beginner"),
                        ],
                    ),
                    CVData.SkillsSection.SkillGroup(
                        name=None,
                        skills=[
                            CVData.SkillsSection.SkillGroup.Item(id=uuid.uuid4(), skill_name="Problem Solving", level="experienced"),
                            CVData.SkillsSection.SkillGroup.Item(id=uuid.uuid4(), skill_name="Communication", level="expert"),
                        ],
                    ),
                ],
            ),
            CVData.LanguagesSection(
                id=uuid.uuid4(),
                languages=[
                    CVData.LanguagesSection.Item(id=uuid.uuid4(), language="English", level="C2"),
                    CVData.LanguagesSection.Item(id=uuid.uuid4(), language="Spanish", level="B2"),
                    # Include a None-level language to ensure it round-trips without loss
                    CVData.LanguagesSection.Item(id=uuid.uuid4(), language="German", level=None),
                ],
            ),
            CVData.AwardsSection(
                id=uuid.uuid4(),
                awards=[
                    CVData.AwardsSection.Item(
                        id=uuid.uuid4(),
                        name="Best Developer",
                        city="New York",
                        start_date=ApproximateDate(month=1, year=2019),
                        end_date=ApproximateDate(month=2, year=2019),
                        description="Received award",
                    ),
                    CVData.AwardsSection.Item(
                        id=uuid.uuid4(),
                        name="Top Performer",
                        city="Boston",
                        start_date=ApproximateDate(month=3, year=2017),
                        end_date=ApproximateDate(month=4, year=2017),
                        description="Recognized for performance",
                    ),
                ],
            ),
            CVData.ExtraCurricularActivitiesSection(
                id=uuid.uuid4(),
                extra_curricular_activities=[
                    CVData.ExtraCurricularActivitiesSection.Item(
                        id=uuid.uuid4(),
                        function_title="Volunteer",
                        employer="Nonprofit",
                        start_date=ApproximateDate(month=3, year=2018),
                        end_date=ApproximateDate(month=6, year=2018),
                        city="New York",
                        description="Community service",
                    ),
                    CVData.ExtraCurricularActivitiesSection.Item(
                        id=uuid.uuid4(),
                        function_title="Tutor",
                        employer="Education Center",
                        start_date=ApproximateDate(month=1, year=2017),
                        end_date=ApproximateDate(month=5, year=2017),
                        city="Boston",
                        description="Taught programming",
                    ),
                ],
            ),
            CVData.CoursesSection(
                id=uuid.uuid4(),
                courses=[
                    CVData.CoursesSection.Item(
                        id=uuid.uuid4(),
                        course="Algorithms",
                        institution="Institute",
                        start_date=ApproximateDate(month=1, year=2015),
                        end_date=ApproximateDate(month=2, year=2015),
                    ),
                    CVData.CoursesSection.Item(
                        id=uuid.uuid4(),
                        course="Data Structures",
                        institution="Academy",
                        start_date=ApproximateDate(month=3, year=2015),
                        end_date=ApproximateDate(month=4, year=2015),
                    ),
                ],
            ),
            CVData.HobbiesSection(
                id=uuid.uuid4(),
                hobbies=[
                    CVData.HobbiesSection.Item(id=uuid.uuid4(), hobby="Guitar"),
                    CVData.HobbiesSection.Item(id=uuid.uuid4(), hobby="Hiking"),
                    CVData.HobbiesSection.Item(id=uuid.uuid4(), hobby="Photography"),
                ],
            ),
            CVData.ReferencesSection(
                id=uuid.uuid4(),
                references=[
                    CVData.ReferencesSection.Item(
                        id=uuid.uuid4(),
                        referent_full_name="Jane Smith",
                        company_name="Company",
                        phone="456",
                        email="jane@example.com",
                    ),
                    CVData.ReferencesSection.Item(
                        id=uuid.uuid4(),
                        referent_full_name="Bob Johnson",
                        company_name="Another Co",
                        phone="789",
                        email="bob@example.com",
                    ),
                ],
            ),
            CVData.CustomSection(
                id=uuid.uuid4(),
                title="Projects",
                content=[
                    CVData.CustomSection.ContentItem(
                        id=uuid.uuid4(),
                        title="Project X",
                        start_date=ApproximateDate(month=1, year=2022),
                        end_date=ApproximateDate(month=12, year=2022),
                        city="Los Angeles",
                        description="Secret project",
                    ),
                    CVData.CustomSection.ContentItem(
                        id=uuid.uuid4(),
                        title="Project Y",
                        start_date=ApproximateDate(month=1, year=2021),
                        end_date=ApproximateDate(month=6, year=2021),
                        city="San Francisco",
                        description="Another secret project",
                    ),
                ],
            ),
        ],
        footer_sections=CVData.FooterSections(
            privacy_clause=CVData.FooterSections.PrivacyClause(),
            signature=CVData.FooterSections.Signature(location="New York", include_date=True, show_name=True),
        ),
    )


def _strip_ids(value):
    """Recursively remove any 'id' keys from nested dict/list structures."""
    if isinstance(value, dict):
        return {key: _strip_ids(nested_value) for key, nested_value in value.items() if key != "id"}
    if isinstance(value, list):
        return [_strip_ids(item) for item in value]
    return value


def _assert_model_style_matches_cv_data(model, cv_data: CVData):
    assert model.template_id == cv_data.style.template_id
    assert model.accent_color == cv_data.style.accent_color
    assert model.section_spacing == cv_data.style.section_spacing
    assert model.line_spacing == cv_data.style.line_spacing
    assert model.margin_spacing == cv_data.style.margin_spacing
    assert model.date_position is not None
    assert model.date_position.value == cv_data.style.date_position
    assert model.text_alignment is not None
    assert model.text_alignment.value == cv_data.style.text_alignment
    assert model.font_size == cv_data.style.font_size
    assert model.font_family == cv_data.style.font_family
    assert model.content_font_scale == cv_data.style.content_font_scale
    assert model.heading_font_scale == cv_data.style.heading_font_scale


def test_round_trip_conversion():
    service = CVDatabaseConversionService()
    original = build_sample_cv_data()

    # Pass a test user_id when converting to model
    test_user_id = "test-user-123"
    model = service.convert_cv_data_to_model(original, test_user_id)

    # Verify user_id is set correctly
    assert model.user_id == test_user_id
    assert model.target_country_code == "UZ"

    # Verify signature fields are set correctly on DB model
    assert model.signature_enabled is True
    assert model.signature_location == "New York"
    assert model.signature_include_date is True
    assert model.signature_show_name is True
    assert model.privacy_clause_enabled is True

    # Verify new personal details fields are set correctly on DB model
    assert model.professional_title == "Software Engineer"
    assert model.marital_status == "Single"
    _assert_model_style_matches_cv_data(model, original)

    # ensure all expected section types exist
    section_types = {section.type for section in model.sections}
    assert section_types == {
        CVSectionType.social_links,
        CVSectionType.employment,
        CVSectionType.education,
        CVSectionType.skills,
        CVSectionType.languages,
        CVSectionType.awards,
        CVSectionType.extracurricular,
        CVSectionType.courses,
        CVSectionType.hobbies,
        CVSectionType.references,
        CVSectionType.custom,
    }

    converted = service.convert_model_to_cv_data(model)

    # Verify skill groups round-trip correctly
    skills_section = next(s for s in converted.sections if isinstance(s, CVData.SkillsSection))
    assert len(skills_section.groups) == 3
    assert skills_section.groups[0].name == "Programming"
    assert len(skills_section.groups[0].skills) == 2
    assert skills_section.groups[0].skills[0].skill_name == "Python"
    assert skills_section.groups[0].skills[0].level == "expert"
    assert skills_section.groups[0].skills[1].skill_name == "SQL"
    assert skills_section.groups[1].name == "DevOps"
    assert len(skills_section.groups[1].skills) == 2
    assert skills_section.groups[1].skills[0].skill_name == "Docker"
    assert skills_section.groups[1].skills[0].level is None
    assert skills_section.groups[1].skills[1].skill_name == "Kubernetes"
    assert skills_section.groups[2].name is None
    assert len(skills_section.groups[2].skills) == 2
    assert skills_section.groups[2].skills[0].skill_name == "Problem Solving"
    assert skills_section.groups[2].skills[1].skill_name == "Communication"

    # Verify signature is correctly converted back
    assert converted.footer_sections.signature is not None
    assert converted.footer_sections.signature.location == "New York"
    assert converted.footer_sections.signature.include_date is True
    assert converted.footer_sections.signature.show_name is True
    assert converted.footer_sections.privacy_clause is not None

    # Verify new personal details fields are correctly converted back
    assert converted.personal_details.professional_title == "Software Engineer"
    assert converted.personal_details.marital_status == "Single"

    # Compare while ignoring any regenerated IDs
    original_dump = _strip_ids(original.model_dump())
    converted_dump = _strip_ids(converted.model_dump())
    assert converted_dump == original_dump


def test_round_trip_conversion_allows_missing_target_country():
    service = CVDatabaseConversionService()
    original = build_sample_cv_data()
    original.target_country_code = None

    model = service.convert_cv_data_to_model(original, "test-user-123")

    assert model.target_country_code is None
    _assert_model_style_matches_cv_data(model, original)

    converted = service.convert_model_to_cv_data(model)

    assert converted.target_country_code is None
