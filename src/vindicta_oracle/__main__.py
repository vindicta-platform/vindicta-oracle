"""Meta-Oracle CLI - Run AI council debates locally."""
import argparse
import json

from meta_oracle.models import DebateContext
from meta_oracle.engine import DebateEngine
from meta_oracle.ollama_client import OllamaConfig


def main():
    """Run a Meta-Oracle council debate from the command line."""
    parser = argparse.ArgumentParser(
        description="Meta-Oracle: AI Council for Warhammer Predictions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m meta_oracle
  python -m meta_oracle --model mistral --rounds 2
  python -m meta_oracle --p1-faction "Orks" --p2-faction "Imperial Knights"
        """
    )
    parser.add_argument(
        "--model", 
        default="llama3.2", 
        help="Ollama model to use (default: llama3.2)"
    )
    parser.add_argument(
        "--rounds", 
        type=int, 
        default=3, 
        help="Number of debate rounds (default: 3)"
    )
    parser.add_argument(
        "--p1-faction", 
        default="Space Marines", 
        help="Player 1 faction (default: Space Marines)"
    )
    parser.add_argument(
        "--p2-faction", 
        default="Tyranids", 
        help="Player 2 faction (default: Tyranids)"
    )
    parser.add_argument(
        "--output", 
        default="debate_transcript.json",
        help="Output file for transcript (default: debate_transcript.json)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="LLM temperature (default: 0.7)"
    )
    
    args = parser.parse_args()
    
    # Configure Ollama
    config = OllamaConfig(
        model=args.model,
        temperature=args.temperature,
    )
    
    # Create debate engine
    engine = DebateEngine(config=config, num_rounds=args.rounds)
    
    # Set up the matchup context
    context = DebateContext(
        player1_faction=args.p1_faction,
        player1_list=_get_sample_list(args.p1_faction),
        player2_faction=args.p2_faction,
        player2_list=_get_sample_list(args.p2_faction),
        mission="Take and Hold (Leviathan)",
        terrain="Mixed urban ruins with scatter terrain",
    )
    
    # Run the debate
    transcript = engine.run_debate(context)
    
    # Save transcript
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(transcript.model_dump_json(indent=2))
    
    print(f"\n📄 Full transcript saved to {args.output}")


def _get_sample_list(faction: str) -> str:
    """Return a sample army list for a given faction."""
    lists = {
        "Space Marines": """Gladius Task Force:
- Captain in Gravis Armour (Warlord)
- 2x Assault Intercessor Squads (5 each)
- Eradicator Squad (3) with Multi-meltas
- Repulsor Executioner
- Bladeguard Veterans (5)""",
        
        "Tyranids": """Invasion Fleet:
- Winged Hive Tyrant (Warlord)
- 2x Hormagaunt Broods (20 each)
- Carnifex Brood (2) with Crushing Claws
- Exocrine
- Zoanthropes (3)""",
        
        "Orks": """Waaagh! Detachment:
- Warboss in Mega Armour (Warlord)
- 30 Boyz with Choppas
- 10 Nobz with Power Klaws
- Battlewagon with Deffrolla
- 3 Deffkoptas""",
        
        "Imperial Knights": """Noble Lance:
- Knight Castellan (Warlord)
- 2x Armiger Helverins
- Knight Gallant
- 2x Armiger Warglaives""",
        
        "Necrons": """Awakened Dynasty:
- Overlord with Resurrection Orb (Warlord)
- 20 Necron Warriors
- 10 Immortals with Tesla Carbines
- 3 Skorpekh Destroyers
- Doom Scythe""",
    }
    
    return lists.get(faction, f"Standard competitive {faction} list")


if __name__ == "__main__":
    main()
