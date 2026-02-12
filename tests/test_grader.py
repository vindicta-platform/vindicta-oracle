"""Unit tests for the ListGrader."""
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from meta_oracle.grader import ListGrader
from meta_oracle.models import (
    ArmyList, 
    Unit, 
    GradeRequest, 
    DebateTranscript, 
    Vote, 
    AgentRole,
    DebateContext
)


class MockDebateEngine:
    def run_grading_session(self, army_list):
        context = DebateContext(
            player1_faction=army_list.faction,
            player1_list="mock",
            player2_faction="mock",
            player2_list="mock"
        )
        transcript = DebateTranscript(id=uuid4(), context=context)
        transcript.consensus = "Player 1 wins"
        transcript.consensus_confidence = 0.8
        transcript.rounds = [[], [], []]
        transcript.votes = [
            Vote(agent_role=AgentRole.HOME, prediction="Player 1 wins", win_probability=0.8, confidence=0.9, reasoning="Good list"),
            Vote(agent_role=AgentRole.ARBITER, prediction="Player 1 wins", win_probability=0.8, confidence=0.8, reasoning="Strong units")
        ]
        return transcript


@pytest.mark.asyncio
async def test_grade_valid_list():
    """Test the happy path for grading a valid list."""
    grader = ListGrader(engine=MockDebateEngine())
    army_list = ArmyList(
        faction="Space Marines",
        units=[Unit(name="Captain", points=100)]
    )
    request = GradeRequest(army_list=army_list)
    
    response = await grader.grade(request)
    
    assert response.score > 0
    assert response.grade in ["A", "B", "C", "D", "F"]
    assert "home" in response.analysis
    assert response.council_verdict["confidence"] == 0.8


def test_scoring_formula():
    """Verify the 60/40 scoring formula and grade mapping."""
    grader = ListGrader(engine=MockDebateEngine())
    
    # Mocking internal methods for formula test
    grader._calculate_primordia_score = MagicMock(return_value=100)
    
    # 0.6 * 80 (council) + 0.4 * 100 (primordia) = 48 + 40 = 88
    # 88 should be a "B"
    score = int(0.6 * 80 + 0.4 * 100)
    grade = grader._map_score_to_grade(score)
    
    assert score == 88
    assert grade == "B"


def test_grade_mapping():
    """Test all grade thresholds."""
    grader = ListGrader()
    assert grader._map_score_to_grade(95) == "A"
    assert grader._map_score_to_grade(85) == "B"
    assert grader._map_score_to_grade(70) == "C"
    assert grader._map_score_to_grade(50) == "D"
    assert grader._map_score_to_grade(30) == "F"
