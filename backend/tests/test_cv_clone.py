from __future__ import annotations

from uuid import uuid4

from src.cv.service import CVService
from src.cv.views.cv_data import ApproximateDate, CVData


def _build_sample_cv() -> CVData:
    pd = CVData.PersonalDetails(
        first_name="Jane",
        last_name="Doe",
        professional_title="Product Manager",
        email="jane@example.com",
        phone="+123456789",
        street_address="123 Main St",
        city="Springfield",
        state="IL",
        postal_code="62704",
        country="US",
        date_of_birth=None,
        place_of_birth=None,
        nationality=None,
        marital_status=None,
        driving_license=None,
        personal_website="https://janedoe.dev",
    )

    prof = CVData.ProfessionalSummary(summary="Product leader with 10+ years experience")

    def approx_date(y: int, m: int | None = None) -> ApproximateDate:
        return ApproximateDate(year=y, month=m)

    return CVData(
        id=uuid4(),
        cv_name="Base CV",
        cv_language="en",
        target_country_code="UZ",
        style=CVData.Style(
            template_id="classic",
            accent_color="#2563EB",
            section_spacing=1.1,
            line_spacing=0.9,
            margin_spacing=1.2,
            date_position="trailing",
            text_alignment="justify",
            font_size=1.2,
            font_family="georgia",
            content_font_scale=0.95,
            heading_font_scale=1.15,
        ),
        personal_details=pd,
        professional_summary=prof,
        sections=[
            CVData.SocialLinkSection(
                id=uuid4(),
                social_links=[CVData.SocialLinkSection.Item(id=uuid4(), label="LinkedIn", url="https://linkedin.com/in/jane")],
            ),
            CVData.EmploymentHistorySection(
                id=uuid4(),
                employment=[
                    CVData.EmploymentHistorySection.Item(
                        id=uuid4(),
                        start_date=approx_date(2019, 1),
                        end_date=approx_date(2021, 12),
                        job_title="Senior PM",
                        employer="Acme",
                        city="NYC",
                        description="<ul><li>Shipped X</li></ul>",
                    )
                ],
            ),
            CVData.EducationSection(
                id=uuid4(),
                education=[
                    CVData.EducationSection.Item(
                        id=uuid4(),
                        start_date=approx_date(2012, 9),
                        end_date=approx_date(2016, 6),
                        school_name="State University",
                        degree="BSc",
                        city="Townsville",
                        description="Graduated with honors",
                    )
                ],
            ),
            CVData.SkillsSection(
                id=uuid4(),
                groups=[
                    CVData.SkillsSection.SkillGroup(
                        name="Technical",
                        skills=[
                            CVData.SkillsSection.SkillGroup.Item(id=uuid4(), skill_name="Python", level="expert"),
                            CVData.SkillsSection.SkillGroup.Item(id=uuid4(), skill_name="SQL", level="experienced"),
                            CVData.SkillsSection.SkillGroup.Item(id=uuid4(), skill_name="Docker", level="skillful"),
                        ],
                    ),
                    CVData.SkillsSection.SkillGroup(
                        name="Soft Skills",
                        skills=[
                            CVData.SkillsSection.SkillGroup.Item(id=uuid4(), skill_name="Leadership", level="expert"),
                            CVData.SkillsSection.SkillGroup.Item(id=uuid4(), skill_name="Communication", level="experienced"),
                        ],
                    ),
                    CVData.SkillsSection.SkillGroup(
                        name=None,
                        skills=[
                            CVData.SkillsSection.SkillGroup.Item(id=uuid4(), skill_name="Analytics", level="experienced"),
                            CVData.SkillsSection.SkillGroup.Item(id=uuid4(), skill_name="Problem Solving", level="expert"),
                        ],
                    ),
                ],
            ),
            CVData.LanguagesSection(
                id=uuid4(),
                languages=[
                    CVData.LanguagesSection.Item(id=uuid4(), language="English", level="native"),
                    CVData.LanguagesSection.Item(id=uuid4(), language="German", level="professional"),
                ],
            ),
            CVData.AwardsSection(
                id=uuid4(),
                awards=[
                    CVData.AwardsSection.Item(
                        id=uuid4(),
                        name="Best Product",
                        city="Berlin",
                        start_date=approx_date(2020, 5),
                        end_date=approx_date(2020, 5),
                        description="Company-wide award",
                    )
                ],
            ),
            CVData.ExtraCurricularActivitiesSection(
                id=uuid4(),
                extra_curricular_activities=[
                    CVData.ExtraCurricularActivitiesSection.Item(
                        id=uuid4(),
                        function_title="Mentor",
                        employer="TechStars",
                        start_date=approx_date(2018),
                        end_date=None,
                        city="Remote",
                        description="Mentored startups",
                    )
                ],
            ),
            CVData.CoursesSection(
                id=uuid4(),
                courses=[
                    CVData.CoursesSection.Item(
                        id=uuid4(),
                        course="Data for PMs",
                        institution="Coursera",
                        start_date=None,
                        end_date=None,
                    )
                ],
            ),
            CVData.HobbiesSection(id=uuid4(), hobbies=[CVData.HobbiesSection.Item(id=uuid4(), hobby="Cycling")]),
            CVData.ReferencesSection(
                id=uuid4(),
                references=[
                    CVData.ReferencesSection.Item(
                        id=uuid4(),
                        referent_full_name="John Ref",
                        company_name="Acme",
                        phone=None,
                        email="john@ref.com",
                    )
                ],
            ),
            CVData.CustomSection(
                id=uuid4(),
                title="Projects",
                content=[
                    CVData.CustomSection.ContentItem(
                        id=uuid4(),
                        title="Big Launch",
                        start_date=None,
                        end_date=None,
                        city=None,
                        description="Scaled to 1M users",
                    )
                ],
            ),
            CVData.CustomSection(id=uuid4(), title="Summary", content="Plain custom text"),
        ],
        footer_sections=CVData.FooterSections(
            privacy_clause=CVData.FooterSections.PrivacyClause(),
            signature=CVData.FooterSections.Signature(location="NYC", include_date=True, show_name=False),
        ),
    )


def test_clone_regenerates_all_ids_and_preserves_content():
    service = CVService()
    original = _build_sample_cv()

    # snapshot of original ids
    orig_cv_id = original.id
    orig_section_ids = [s.id for s in original.sections]
    orig_nested_ids = []
    for s in original.sections:
        if isinstance(s, CVData.SocialLinkSection):
            orig_nested_ids.extend([i.id for i in s.social_links])
        elif isinstance(s, CVData.EmploymentHistorySection):
            orig_nested_ids.extend([i.id for i in s.employment])
        elif isinstance(s, CVData.EducationSection):
            orig_nested_ids.extend([i.id for i in s.education])
        elif isinstance(s, CVData.SkillsSection):
            for group in s.groups:
                orig_nested_ids.extend([i.id for i in group.skills])
        elif isinstance(s, CVData.LanguagesSection):
            orig_nested_ids.extend([i.id for i in s.languages])
        elif isinstance(s, CVData.AwardsSection):
            orig_nested_ids.extend([i.id for i in s.awards])
        elif isinstance(s, CVData.ExtraCurricularActivitiesSection):
            orig_nested_ids.extend([i.id for i in s.extra_curricular_activities])
        elif isinstance(s, CVData.CoursesSection):
            orig_nested_ids.extend([i.id for i in s.courses])
        elif isinstance(s, CVData.HobbiesSection):
            orig_nested_ids.extend([i.id for i in s.hobbies])
        elif isinstance(s, CVData.ReferencesSection):
            orig_nested_ids.extend([i.id for i in s.references])
        elif isinstance(s, CVData.CustomSection) and isinstance(s.content, list):
            orig_nested_ids.extend([i.id for i in s.content])

    clone = service._clone_cv_data_with_new_ids(original, new_cv_name="Tailored for Foo")

    # top-level invariants
    assert clone.id != orig_cv_id
    assert clone.cv_name == "Tailored for Foo"
    assert clone.cv_language == original.cv_language
    assert clone.style == original.style
    assert clone.personal_details == original.personal_details
    assert clone.professional_summary == original.professional_summary
    assert clone.footer_sections == original.footer_sections
    assert clone.footer_sections.privacy_clause is not None
    assert clone.footer_sections.signature is not None
    assert clone.footer_sections.signature.location == "NYC"
    assert clone.footer_sections.signature.include_date is True
    assert clone.footer_sections.signature.show_name is False

    # structure preserved
    assert len(clone.sections) == len(original.sections)
    for orig_section, new_section in zip(original.sections, clone.sections, strict=True):
        assert new_section.kind == orig_section.kind
        assert new_section.id != orig_section.id

    # nested ids changed, representative checks on content
    new_nested_ids = []
    for s in clone.sections:
        if isinstance(s, CVData.SocialLinkSection):
            new_nested_ids.extend([i.id for i in s.social_links])
            assert s.social_links[0].label == "LinkedIn"
        elif isinstance(s, CVData.EmploymentHistorySection):
            new_nested_ids.extend([i.id for i in s.employment])
            assert s.employment[0].job_title == "Senior PM"
        elif isinstance(s, CVData.EducationSection):
            new_nested_ids.extend([i.id for i in s.education])
            assert s.education[0].school_name == "State University"
        elif isinstance(s, CVData.SkillsSection):
            for group in s.groups:
                new_nested_ids.extend([i.id for i in group.skills])
            # Verify group structure and content preserved
            assert len(s.groups) == 3
            assert s.groups[0].name == "Technical"
            assert len(s.groups[0].skills) == 3
            assert s.groups[0].skills[0].skill_name == "Python"
            assert s.groups[0].skills[1].skill_name == "SQL"
            assert s.groups[0].skills[2].skill_name == "Docker"
            assert s.groups[1].name == "Soft Skills"
            assert len(s.groups[1].skills) == 2
            assert s.groups[1].skills[0].skill_name == "Leadership"
            assert s.groups[1].skills[1].skill_name == "Communication"
            assert s.groups[2].name is None
            assert len(s.groups[2].skills) == 2
            assert s.groups[2].skills[0].skill_name == "Analytics"
            assert s.groups[2].skills[1].skill_name == "Problem Solving"
        elif isinstance(s, CVData.LanguagesSection):
            new_nested_ids.extend([i.id for i in s.languages])
            assert s.languages[0].language == "English"
        elif isinstance(s, CVData.AwardsSection):
            new_nested_ids.extend([i.id for i in s.awards])
            assert s.awards[0].name == "Best Product"
        elif isinstance(s, CVData.ExtraCurricularActivitiesSection):
            new_nested_ids.extend([i.id for i in s.extra_curricular_activities])
            assert s.extra_curricular_activities[0].function_title == "Mentor"
        elif isinstance(s, CVData.CoursesSection):
            new_nested_ids.extend([i.id for i in s.courses])
            assert s.courses[0].course == "Data for PMs"
        elif isinstance(s, CVData.HobbiesSection):
            new_nested_ids.extend([i.id for i in s.hobbies])
            assert s.hobbies[0].hobby == "Cycling"
        elif isinstance(s, CVData.ReferencesSection):
            new_nested_ids.extend([i.id for i in s.references])
            assert s.references[0].referent_full_name == "John Ref"
        elif isinstance(s, CVData.CustomSection):
            if isinstance(s.content, list):
                new_nested_ids.extend([i.id for i in s.content])
                assert s.content[0].title == "Big Launch"
            else:
                assert s.content == "Plain custom text"

    assert set(new_nested_ids).isdisjoint(set(orig_nested_ids))

    # source object not mutated
    assert original.id == orig_cv_id
    assert [s.id for s in original.sections] == orig_section_ids
