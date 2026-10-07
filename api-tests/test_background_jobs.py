import os

import pytest
import requests
from dotenv import load_dotenv


load_dotenv(".env")


BASE_URL = os.getenv(
    "RHOMBUS_API_BASE_URL",
    "https://api.rhombusai.com",
).rstrip("/")

ORG_ID = os.getenv("RHOMBUS_ORG_ID")
JOB_ID = os.getenv("RHOMBUS_JOB_ID")
ACCESS_TOKEN = os.getenv("RHOMBUS_ACCESS_TOKEN")


def require_env(name, value):
    if not value:
        pytest.fail(
            f"Missing required environment variable: {name}"
        )


def job_url(job_id):
    return (
        f"{BASE_URL}/api/background_jobs/"
        f"jobs/{job_id}/"
    )


@pytest.fixture
def authenticated_headers():
    require_env("RHOMBUS_ORG_ID", ORG_ID)
    require_env("RHOMBUS_ACCESS_TOKEN", ACCESS_TOKEN)

    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "X-Org-Id": ORG_ID,
    }


def test_get_pipeline_job_progress_authenticated(
    authenticated_headers,
):
    require_env("RHOMBUS_JOB_ID", JOB_ID)

    response = requests.get(
        job_url(JOB_ID),
        headers=authenticated_headers,
        params={
            "compact": "pipeline_progress",
        },
        timeout=30,
    )

    assert response.status_code == 200, (
        f"Expected HTTP 200, got {response.status_code}. "
        f"Response: {response.text[:500]}"
    )

    assert (
        "application/json"
        in response.headers.get("Content-Type", "")
    )

    data = response.json()

    assert data["id"] == JOB_ID
    assert data["type"] == "workflow-session"
    assert int(data["organization"]) == int(ORG_ID)

    assert "status" in data
    assert "result" in data
    assert isinstance(data["result"], dict)

    result = data["result"]

    assert "progress" in result
    assert isinstance(result["progress"], list)
    assert len(result["progress"]) > 0

    for step in result["progress"]:
        assert "step" in step
        assert "status" in step

    assert "selected_transformations" in result
    assert isinstance(
        result["selected_transformations"],
        list,
    )

    transformations = set(
        result["selected_transformations"]
    )

    assert "remove_duplicate" in transformations
    assert "type_convert" in transformations


def test_get_pipeline_job_progress_without_authentication():
    """
    Negative API test.

    The same job endpoint is called without the Bearer token.
    Rhombus returns 404 and does not expose the job to the
    unauthenticated caller.
    """
    require_env("RHOMBUS_ORG_ID", ORG_ID)
    require_env("RHOMBUS_JOB_ID", JOB_ID)

    response = requests.get(
        job_url(JOB_ID),
        headers={
            "Accept": "application/json",
            "X-Org-Id": ORG_ID,
        },
        params={
            "compact": "pipeline_progress",
        },
        timeout=30,
        allow_redirects=True,
    )

    assert response.status_code == 404, (
        f"Expected HTTP 404, got {response.status_code}. "
        f"Response: {response.text[:500]}"
    )

    assert (
        "application/json"
        in response.headers.get("Content-Type", "")
    )

    data = response.json()

    assert data == {
        "detail": "No Job matches the given query."
    }