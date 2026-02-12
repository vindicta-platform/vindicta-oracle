"""Demo: Run a sample Meta-Oracle debate with local models."""
from meta_oracle.models import DebateContext
from meta_oracle.engine import DebateEngine
from meta_oracle.ollama_client import OllamaConfig


def run_demo():
    """Run a complete demo debate between Space Marines and Tyranids."""
    print("\n" + "🎮" * 35)
    print("       META-ORACLE DEMO")
    print("🎮" * 35)
    print("\nRunning 5-agent council debate with local Ollama inference...")
    print("This may take a few minutes depending on your hardware.\n")
    
    # TODO: Setup with pydantic settings for env drive
    # Configure for local model - try common models
    config = OllamaConfig(
        model="llama3.2",  # Change to "mistral" or "gemma2" if needed
        temperature=0.7,
        max_tokens=512,
    )
    
    # Create a sample competitive matchup
    context = DebateContext(
        player1_faction="Space Marines (Gladius Task Force)",
        player1_list="""
HQ:
- Captain in Gravis Armour with Heavy Bolt Rifle (Warlord)
  - Enhancement: Adept of the Codex

Troops:
- 2x Assault Intercessor Squads (5 each)

Elites:
- Bladeguard Veterans (5) with Storm Shields

Heavy Support:
- Eradicator Squad (3) with Multi-meltas
- Repulsor Executioner with Heavy Laser Destroyer

Total: ~1000 points
""",
        player2_faction="Tyranids (Invasion Fleet)",
        player2_list="""
HQ:
- Winged Hive Tyrant (Warlord)
  - Psychic Powers: Onslaught, Catalyst
  - Enhancement: Alien Cunning

Troops:
- 2x Hormagaunt Broods (20 each)

Elites:
- Zoanthropes (3)

Heavy Support:
- Carnifex Brood (2) with Crushing Claws + Bio-plasma
- Exocrine

Total: ~1000 points
""",
        mission="Take and Hold (Leviathan Mission Pack)",
        terrain="Dense urban ruins with 6 large LOS-blocking buildings, scatter terrain throughout",
        additional_context="Tournament setting, competitive lists, both players are experienced",
    )
    
    # Run the debate with 3 rounds
    engine = DebateEngine(config=config, num_rounds=3)
    transcript = engine.run_debate(context)
    
    # Print full transcript
    print("\n\n" + "=" * 70)
    print("📜  FULL DEBATE TRANSCRIPT")
    print("=" * 70)
    
    for round_num, round_args in enumerate(transcript.rounds, 1):
        print(f"\n{'─' * 70}")
        print(f"ROUND {round_num}")
        print(f"{'─' * 70}")
        
        for arg in round_args:
            role_name = arg.agent_role.value.upper().replace("_", "-")
            print(f"\n[{role_name}]:")
            print(arg.content)
    
    print("\n\n" + "=" * 70)
    print("🗳️   DETAILED VOTES")
    print("=" * 70)
    
    for vote in transcript.votes:
        role_name = vote.agent_role.value.upper().replace("_", "-")
        print(f"\n[{role_name}]")
        print(f"  Prediction: {vote.prediction}")
        print(f"  Win Probability: {vote.win_probability * 100:.0f}%")
        print(f"  Reasoning:")
        # Wrap reasoning text
        reasoning_lines = vote.reasoning.split("\n")
        for line in reasoning_lines[:5]:  # Limit to 5 lines
            print(f"    {line}")
    
    # Save transcript to file
    print("\n\n" + "=" * 70)
    print("💾  SAVING TRANSCRIPT")
    print("=" * 70)
    
    output_file = "demo_transcript.json"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(transcript.model_dump_json(indent=2))
    
    print(f"\n✅ Full transcript saved to: {output_file}")
    print(f"\n🏆 Final Verdict: {transcript.consensus}")
    print(f"📊 Council Confidence: {transcript.consensus_confidence * 100:.0f}%")
    
    return transcript


if __name__ == "__main__":
    run_demo()
