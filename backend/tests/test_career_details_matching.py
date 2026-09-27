from datetime import date

from src.career_details._matching.utils import (
    EmploymentFingerprint,
    PersonIdentity,
    employments_match,
    normalize_employer,
    title_similarity,
)


def test_normalize_employer_strips_legal_suffixes():
    assert normalize_employer("Northstar AG") == "northstar"
    assert normalize_employer("Northstar") == "northstar"
    assert normalize_employer("Harbor Systems") == "harbor systems"


def test_person_key_prefers_email():
    maya = PersonIdentity("maya@example.com", "Maya", "Example", date(1990, 1, 1))
    maya_full = PersonIdentity("maya@example.com", "Maya Alexandra", "Example", date(1990, 1, 1))
    mia = PersonIdentity("mia@example.org", "Mia", "Example", date(1992, 8, 17))
    assert maya.key() == maya_full.key()
    assert maya.key() != mia.key()


def test_person_key_falls_back_to_first_name_token():
    maya = PersonIdentity(None, "Maya", "Example", date(1990, 1, 1))
    maya_full = PersonIdentity(None, "Maya Alexandra", "Example", date(1990, 1, 1))
    assert maya.key() == maya_full.key()


def test_maya_engineering_manager_roles_match_across_cvs():
    en = EmploymentFingerprint("Engineering Manager", "Northstar", "Zurich", 2024, None, None, None)
    de = EmploymentFingerprint("Engineering Managerin", "Northstar AG", "Zurich", 2024, None, None, None)
    varied = EmploymentFingerprint("Engineering Manager, Internal Platforms", "Northstar AG", "Zurich", 2024, 1, None, None)
    assert employments_match(en, de)
    assert employments_match(en, varied)
    assert employments_match(de, varied)


def test_maya_software_engineer_roles_match_across_cvs():
    en = EmploymentFingerprint("Software Engineer", "Northstar", "Zurich", 2020, 1, 2023, 12)
    de = EmploymentFingerprint("Softwareentwicklerin", "Northstar AG", "Zurich", 2020, 1, 2023, 12)
    varied = EmploymentFingerprint("Backend Software Engineer", "Northstar AG", "Zurich", 2020, 2, 2023, None)
    assert employments_match(en, de)
    assert employments_match(en, varied)


def test_distinct_roles_at_same_company_stay_separate():
    manager = EmploymentFingerprint("Engineering Manager", "Northstar", "Zurich", 2024, None, None, None)
    engineer = EmploymentFingerprint("Software Engineer", "Northstar", "Zurich", 2020, 1, 2023, 12)
    assert not employments_match(manager, engineer)


def test_harbor_role_does_not_match_northstar():
    harbor = EmploymentFingerprint("Junior Software Engineer", "Harbor Systems", "New York", 2016, 7, 2019, 12)
    northstar = EmploymentFingerprint("Software Engineer", "Northstar", "Zurich", 2020, 1, 2023, 12)
    assert not employments_match(harbor, northstar)


def test_mia_and_maya_northstar_manager_would_match_as_roles_but_people_differ():
    """Role fingerprints can look similar; person identity must keep accounts separate upstream."""
    maya = EmploymentFingerprint("Engineering Manager", "Northstar", "Zurich", 2024, None, None, None)
    mia = EmploymentFingerprint("Engineering Manager", "Northstar", "London", 2024, 1, None, None)
    # Same employer + dates: role matcher alone is not enough — matching service gates on person key.
    assert employments_match(maya, mia)


def test_title_similarity_handles_gendered_german_suffix():
    assert title_similarity("Engineering Manager", "Engineering Managerin") > 0.5
