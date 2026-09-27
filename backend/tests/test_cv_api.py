import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from server import app

ALICE = {"Authorization": "Bearer alice-token"}
BOB = {"Authorization": "Bearer bob-token"}
EXAMPLE = Path(__file__).parents[1] / "examples/cv-en.json"


def collect_ids(value: Any) -> set[str]:
    if isinstance(value, dict):
        result = {value["id"]} if "id" in value else set()
        for child in value.values():
            result.update(collect_ids(child))
        return result
    if isinstance(value, list):
        return set().union(*(collect_ids(child) for child in value))
    return set()


def test_routes_are_available_and_require_authentication():
    # These route/auth checks do not need database initialization through the lifespan.
    client = TestClient(app)
    try:
        schema = client.get("/openapi.json")
        assert schema.status_code == 200
        assert "/cv/import" in schema.json()["paths"]
        assert "/cv/{cv_id}/duplicate" in schema.json()["paths"]
        assert client.get("/cv/").status_code == 401
        assert client.get("/cv/", headers={"Authorization": "Bearer invalid"}).status_code == 401

    finally:
        client.close()


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("TEST_DB_URL"), reason="Set TEST_DB_URL to a local disposable database with the initial schema applied"
)
def test_persisted_cv_workflow_and_ownership():
    sample = json.loads(EXAMPLE.read_text())
    created: list[tuple[str, dict[str, str]]] = []
    with TestClient(app) as client:
        try:
            assert client.get("/ping").json() == {"status": "ok"}

            response = client.post("/cv/create-empty", json={"language": "en"}, headers=ALICE)
            assert response.status_code == 201, response.text
            empty = response.json()
            created.append((empty["id"], ALICE))
            assert empty["sections"][1]["employment"] == []

            response = client.post("/cv/import", json=sample, headers=ALICE)
            assert response.status_code == 201, response.text
            original = response.json()
            cv_id = original["id"]
            created.append((cv_id, ALICE))
            assert collect_ids(sample).isdisjoint(collect_ids(original))
            assert client.get(f"/cv/{cv_id}", headers=ALICE).json() == original

            response = client.post(f"/cv/{cv_id}/duplicate", headers=ALICE)
            assert response.status_code == 201, response.text
            duplicate = response.json()
            duplicate_id = duplicate["id"]
            created.append((duplicate_id, ALICE))
            assert collect_ids(original).isdisjoint(collect_ids(duplicate))
            assert client.get(f"/cv/{duplicate_id}", headers=ALICE).json() == duplicate

            response = client.post("/cv/import", json=sample, headers=BOB)
            assert response.status_code == 201, response.text
            other = response.json()
            created.append((other["id"], BOB))
            assert client.get(f"/cv/{cv_id}", headers=BOB).status_code == 404
            assert client.put(f"/cv/{cv_id}", json=original, headers=BOB).status_code == 404
            assert client.delete(f"/cv/{cv_id}", headers=BOB).status_code == 404
            assert client.post(f"/cv/{cv_id}/duplicate", headers=BOB).status_code == 404
            assert cv_id not in {cv["id"] for cv in client.get("/cv/", headers=BOB).json()}

            # Reject mismatched CV IDs and foreign nested IDs.
            assert client.put(f"/cv/{cv_id}", json=other, headers=ALICE).status_code == 400
            foreign_sections = original | {"sections": other["sections"]}
            assert client.put(f"/cv/{cv_id}", json=foreign_sections, headers=ALICE).status_code == 400

            duplicate["cv_name"] = "Edited copy"
            employment = next(s for s in duplicate["sections"] if s["kind"] == "employment")
            employment["employment"].reverse()
            employment["employment"][0]["description"] = "Changed only in the duplicate"
            employment["employment"].append(
                {
                    "id": None,
                    "job_title": "Consultant",
                    "employer": "Example Ltd",
                    "city": None,
                    "description": None,
                    "start_date": {"year": 2025, "month": None},
                    "end_date": None,
                }
            )
            duplicate["sections"].reverse()
            duplicate["sections"].append(
                {
                    "id": None,
                    "kind": "custom",
                    "title": "New section",
                    "content": {"content_type": "text", "text": "Independent copy"},
                }
            )
            response = client.put(f"/cv/{duplicate_id}", json=duplicate, headers=ALICE)
            assert response.status_code == 200, response.text
            updated = response.json()
            assert client.get(f"/cv/{duplicate_id}", headers=ALICE).json() == updated
            assert client.get(f"/cv/{cv_id}", headers=ALICE).json() == original
            saved_employment = next(s for s in updated["sections"] if s["kind"] == "employment")
            assert saved_employment["employment"][0]["description"] == "Changed only in the duplicate"
            assert saved_employment["employment"][-1]["id"] is not None
            assert saved_employment["employment"][-1]["start_date"] == {"year": 2025, "month": None}
            assert updated["sections"][-1]["title"] == "New section"

            # Existing update behaviour includes removing items and whole sections.
            saved_employment["employment"].pop()
            updated["sections"].pop()
            response = client.put(f"/cv/{duplicate_id}", json=updated, headers=ALICE)
            assert response.status_code == 200, response.text
            assert client.get(f"/cv/{duplicate_id}", headers=ALICE).json() == response.json()

            response = client.patch(f"/cv/{duplicate_id}/target-country", json={"target_country_code": " de "}, headers=ALICE)
            assert response.status_code == 200, response.text
            assert client.get(f"/cv/{duplicate_id}/target-country", headers=ALICE).json() == {"target_country_code": "DE"}
            assert client.get(f"/cv/{cv_id}/target-country", headers=ALICE).json() == {"target_country_code": "CH"}

            assert client.delete(f"/cv/{cv_id}", headers=ALICE).status_code == 204
            assert client.get(f"/cv/{cv_id}", headers=ALICE).status_code == 404
            assert client.get(f"/cv/{duplicate_id}", headers=ALICE).status_code == 200
            assert client.get(f"/cv/{uuid4()}", headers=ALICE).status_code == 404
        finally:
            for cv_id, headers in reversed(created):
                client.delete(f"/cv/{cv_id}", headers=headers)
