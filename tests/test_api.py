"""Integration tests for the Meta-Oracle API."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from meta_oracle.api import app
from meta_oracle.models import GradeResponse

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"


@patch("meta_oracle.grader.ListGrader.grade")
def test_grade_endpoint_success(mock_grade):
    """Test successful grading via the API endpoint."""
    # Mock the grader response
    mock_grade.return_value = {
        "grade": "B",
        "score": 80,
        "analysis": {"home": "Good"},
        "council_verdict": {"prediction": "Win", "confidence": 0.8, "consensus_agents": ["home"]},
        "metadata": {"debate_id": "test-id", "rounds": 3, "processing_time_ms": 100}
    }
    
    payload = {
        "army_list": {
            "faction": "Space Marines",
            "units": [{"name": "Captain", "points": 100}]
        }
    }
    
    response = client.post("/api/v1/grade", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["grade"] == "B"
    assert data["score"] == 80


def test_grade_endpoint_invalid_payload():
    """Test API behavior with invalid request payloads."""
    # Missing units
    payload = {
        "army_list": {
            "faction": "Space Marines"
        }
    }
    response = client.post("/api/v1/grade", json=payload)
    assert response.status_code == 422  # Pydantic validation error
    
    # Empty units (should trigger our 400 or Pydantic validator)
    payload = {
        "army_list": {
            "faction": "Space Marines",
            "units": []
        }
    }
    response = client.post("/api/v1/grade", json=payload)
    # Since we added a field_validator that raises ValueError, this becomes 422
    assert response.status_code == 422
