"""List Grader - Orchestrates list evaluation and scoring."""
import random
import time
from typing import Any

from meta_oracle.engine import DebateEngine
from meta_oracle.models import ArmyList, GradeRequest, GradeResponse, DebateTranscript


class ListGrader:
    """Orchestrates the army list grading process."""

    def __init__(self, engine: DebateEngine | None = None):
        self.engine = engine or DebateEngine()

    async def grade(self, request: GradeRequest) -> GradeResponse:
        """Grade a single army list.
        
        Args:
            request: The grading request containing the army list
            
        Returns:
            Structured grade response
        """
        start_time = time.time()
        
        # 1. Run the council debate session
        transcript = self.engine.run_grading_session(request.army_list)
        
        # 2. Extract council performance (0-100)
        council_consensus = transcript.consensus_confidence * 100
        
        # 3. Simulate/Calculate Primordia tactical score (0-100)
        # In a real system, this would call Primordia-AI
        primordia_score = self._calculate_primordia_score(request.army_list)
        
        # 4. Apply final scoring formula: 0.6 * council + 0.4 * primordia
        final_score = int(0.6 * council_consensus + 0.4 * primordia_score)
        
        # 5. Map numeric score to letter grade
        letter_grade = self._map_score_to_grade(final_score)
        
        # 6. Format analysis from agent roles
        analysis = self._format_analysis(transcript)
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return GradeResponse(
            grade=letter_grade,
            score=final_score,
            analysis=analysis,
            council_verdict={
                "prediction": transcript.consensus,
                "confidence": transcript.consensus_confidence,
                "consensus_agents": [v.agent_role.value for v in transcript.votes if v.prediction == transcript.consensus]
            },
            metadata={
                "debate_id": str(transcript.id),
                "rounds": len(transcript.rounds),
                "processing_time_ms": processing_time_ms
            }
        )

    def _calculate_primordia_score(self, army_list: ArmyList) -> int:
        """Stub for Primordia-AI tactical evaluation."""
        # Derived score from points efficiency (just a heuristic for the demo)
        total_points = sum(u.points for u in army_list.units)
        seed = len(army_list.units) + total_points
        random.seed(seed)
        return random.randint(40, 95)

    def _map_score_to_grade(self, score: int) -> str:
        """Map numeric score (0-100) to letter grade (A-F)."""
        if score >= 90:
            return "A"
        if score >= 75:
            return "B"
        if score >= 60:
            return "C"
        if score >= 40:
            return "D"
        return "F"

    def _format_analysis(self, transcript: DebateTranscript) -> dict[str, str]:
        """Extract agent reasoning for the response."""
        analysis = {}
        for vote in transcript.votes:
            role = vote.agent_role.value
            analysis[role] = vote.reasoning
        return analysis
