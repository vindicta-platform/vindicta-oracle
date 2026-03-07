"""Debate Engine - Orchestrates the 5-agent council debate."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from vindicta_oracle.models import Argument, DebateContext, DebateTranscript
from vindicta_oracle.agents import (
    HomeAgent,
    AdversaryAgent,
    ArbiterAgent,
    RuleSageAgent,
    ChaosAgent,
)
from vindicta_oracle.ollama_client import OllamaClient, OllamaConfig

if TYPE_CHECKING:
    from vindicta_oracle.models import ArmyList


class DebateEngine:
    """Orchestrates the multi-round adversarial debate between 5 agents."""

    def __init__(self, config: OllamaConfig | None = None, num_rounds: int = 3):
        """Initialize the debate engine with all 5 council agents.

        Args:
            config: Ollama configuration (model, temperature, etc.)
            num_rounds: Number of debate rounds (default 3)
        """
        client = OllamaClient(config)
        self.agents = [
            HomeAgent(client),
            AdversaryAgent(client),
            ArbiterAgent(client),
            RuleSageAgent(client),
            ChaosAgent(client),
        ]
        self.num_rounds = num_rounds

    def run_debate(
        self,
        context: DebateContext | None = None,
        *,
        topic: str | None = None,
        player1_faction: str | None = None,
        player2_faction: str | None = None,
        player1_list: str = "",
        player2_list: str = "",
        mission: str | None = None,
        terrain: str | None = None,
        additional_context: str | None = None,
    ) -> DebateTranscript:
        """Execute the full debate protocol.

        Accepts either a pre-built DebateContext or individual keyword
        arguments for convenience. If ``context`` is provided the keyword
        arguments are ignored.

        Args:
            context: The matchup context (factions, lists, mission, etc.)
            topic: Convenience alias – mapped to additional_context.
            player1_faction: Faction name for player 1.
            player2_faction: Faction name for player 2.
            player1_list: Army list for player 1.
            player2_list: Army list for player 2.
            mission: Mission name.
            terrain: Terrain description.
            additional_context: Extra context for the debate.

        Returns:
            Complete debate transcript with all rounds, votes, and consensus
        """
        if context is None:
            context = DebateContext(
                player1_faction=player1_faction or "Unknown",
                player1_list=player1_list,
                player2_faction=player2_faction or "Unknown",
                player2_list=player2_list,
                mission=mission,
                terrain=terrain,
                additional_context=additional_context or topic,
            )

        transcript = DebateTranscript(context=context)

        self._print_header(context)

        # Run debate rounds
        for round_num in range(1, self.num_rounds + 1):
            self._print_round_header(round_num)

            round_arguments: list[Argument] = []
            for agent in self.agents:
                role_name = agent.role.value.upper().replace("_", "-")
                print(f"\n🎙️  [{role_name}] Speaking...")

                argument = agent.respond(transcript, round_num)
                round_arguments.append(argument)

                # Print truncated preview
                preview = argument.content[:300].replace("\n", " ")
                if len(argument.content) > 300:
                    preview += "..."
                print(f"   {preview}")

            transcript.rounds.append(round_arguments)

        # Voting phase
        self._print_voting_header()

        for agent in self.agents:
            role_name = agent.role.value.upper().replace("_", "-")
            print(f"\n🗳️  [{role_name}] Casting vote...")

            vote = agent.vote(transcript)
            transcript.votes.append(vote)

            print(
                f"   → {vote.prediction} ({vote.win_probability * 100:.0f}% confidence)"
            )

        # Calculate consensus
        transcript.consensus, transcript.consensus_confidence = (
            self._calculate_consensus(transcript)
        )

        self._print_verdict(transcript)

        return transcript

    def _calculate_consensus(self, transcript: DebateTranscript) -> tuple[str, float]:
        """Calculate the council's consensus prediction.

        Uses simple majority voting with averaged confidence.
        """
        votes = transcript.votes
        predictions = [v.prediction for v in votes]

        # Simple majority
        vote_counts = Counter(predictions)
        winner = vote_counts.most_common(1)[0][0]

        # Average probability of agents who voted for the winner
        winning_probs = [v.win_probability for v in votes if v.prediction == winner]
        avg_confidence = (
            sum(winning_probs) / len(winning_probs) if winning_probs else 0.5
        )

        return winner, avg_confidence

    def _print_header(self, context: DebateContext) -> None:
        """Print the debate header."""
        print("\n" + "=" * 70)
        print("🏛️   META-ORACLE COUNCIL CONVENES")
        print("=" * 70)
        print(f"\n📋 MATCHUP: {context.player1_faction} vs {context.player2_faction}")
        print(f"📍 Mission: {context.mission or 'Standard'}")
        if context.terrain:
            print(f"🏔️  Terrain: {context.terrain}")

    def _print_round_header(self, round_num: int) -> None:
        """Print a round header."""
        print(f"\n{'─' * 70}")
        print(f"🔔 ROUND {round_num}")
        print(f"{'─' * 70}")

    def _print_voting_header(self) -> None:
        """Print the voting phase header."""
        print(f"\n{'=' * 70}")
        print("🗳️   VOTING PHASE")
        print(f"{'=' * 70}")

    def _print_verdict(self, transcript: DebateTranscript) -> None:
        """Print the final council verdict."""
        print(f"\n{'=' * 70}")
        print("🏆  COUNCIL VERDICT")
        print(f"{'=' * 70}")
        print(f"\n🎯 Prediction: {transcript.consensus}")
        print(f"📊 Confidence: {transcript.consensus_confidence * 100:.0f}%")

        # Show vote breakdown
        print("\n📜 Vote Breakdown:")
        for vote in transcript.votes:
            role = vote.agent_role.value.upper().replace("_", "-")
            print(f"   • {role}: {vote.prediction} ({vote.win_probability * 100:.0f}%)")

    def run_grading_session(self, army_list: ArmyList) -> DebateTranscript:
        """Execute a debate to grade a single army list.

        Args:
            army_list: The army list to grade

        Returns:
            Transcript containing the evaluation debate
        """
        # Format units into a readable string
        unit_details = "\n".join(
            [
                f"- {u.name} ({u.points} pts): {', '.join(u.wargear)}"
                for u in army_list.units
            ]
        )
        player1_list = f"Faction: {army_list.faction}\nDetachment: {army_list.detachment or 'Unknown'}\nUnits:\n{unit_details}"

        context = DebateContext(
            player1_faction=army_list.faction,
            player1_list=player1_list,
            player2_faction="Meta Challenger",
            player2_list="A generic competitive list representing the current tournament meta.",
            mission="Grand Tournament: Leviathan",
            terrain="WTC Standard Layout",
            additional_context="Grading requested for competitive viability.",
        )

        return self.run_debate(context)
