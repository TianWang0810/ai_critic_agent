"""
AI Critic Agent - Main Entry Point
Command-line interface for startup idea critique
"""

import os
import sys

# ===== MAC M4 PROTECTION: Must be BEFORE any imports =====
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

import json
from pathlib import Path
from typing import Optional

from reasoning.critic_agent import CriticAgent
from reasoning.formatter import CriticFormatter


def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 80)
    print(" " * 20 + "AI CRITIC AGENT FOR STARTUP IDEAS")
    print("=" * 80)
    print("\nThis agent will critically analyze your startup idea using:")
    print("  • Historical failure cases")
    print("  • Market evidence")
    print("  • Business logic\n")


def get_user_input() -> str:
    """Get startup idea from user"""
    print("=" * 80)
    print("Enter your startup idea")
    print("=" * 80)
    print("\nDescribe your startup in one or two sentences.")
    print("Example: 'A social network for dog owners to arrange playdates'\n")
    
    idea = input("Your idea: ").strip()
    
    if not idea:
        print("❌ Error: Idea cannot be empty")
        sys.exit(1)
    
    return idea


def save_output(response, output_dir: str = "output"):
    """Save critique to files"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    formatter = CriticFormatter()
    
    # Save JSON
    json_path = output_path / "critique.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(response.model_dump_json(indent=2))
    
    # Save Text
    text_path = output_path / "critique.txt"
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(formatter.to_text(response, verbose=True))
    
    # Save Markdown
    md_path = output_path / "critique.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(formatter.to_markdown(response))
    
    # Save HTML
    html_path = output_path / "critique.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(formatter.to_html(response))
    
    return {
        "json": json_path,
        "text": text_path,
        "markdown": md_path,
        "html": html_path
    }


def main(idea: Optional[str] = None, save: bool = True, verbose: bool = True):
    """
    Main execution function
    
    Args:
        idea: Startup idea (if None, will prompt user)
        save: Whether to save output files
        verbose: Whether to show formatted output
    """
    print_banner()
    
    # Get idea
    if idea is None:
        idea = get_user_input()
    else:
        print(f"Analyzing idea: '{idea}'\n")
    
    # Initialize agent
    print("🔧 Initializing AI Critic Agent...")
    try:
        agent = CriticAgent()
        formatter = CriticFormatter()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    # Run critique
    print(f"🔍 Starting analysis...\n")
    print("=" * 80)
    
    try:
        response = agent.critique_idea(idea)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Display results
    if verbose:
        print("\n" + "=" * 80)
        print(" " * 25 + "CRITIQUE RESULTS")
        print("=" * 80)
        print(formatter.to_text(response, verbose=True))
    
    # Save files
    if save:
        print("\n" + "=" * 80)
        print("Saving output files...")
        print("=" * 80)
        
        try:
            paths = save_output(response)
            print("\n✅ Files saved:")
            for format_type, path in paths.items():
                print(f"   • {format_type.upper()}: {path}")
        except Exception as e:
            print(f"\n⚠️  Warning: Could not save files: {e}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n📊 Overall Risk: {response.verdict.overall_risk.value.upper()}")
    print(f"📈 Success Probability: {response.verdict.success_probability.value.replace('_', ' ').title()}")
    print(f"\n🚨 Top {len(response.verdict.key_concerns)} Concerns:")
    for i, concern in enumerate(response.verdict.key_concerns, 1):
        print(f"\n{i}. {concern}")
    
    print("\n" + "=" * 80)
    print("Analysis complete. Review the output files for details.")
    print("=" * 80 + "\n")
    
    return response


if __name__ == "__main__":
    # Check for command-line arguments
    if len(sys.argv) > 1:
        # Idea provided as command-line argument
        cli_idea = " ".join(sys.argv[1:])
        main(idea=cli_idea, save=True, verbose=True)
    else:
        # Interactive mode
        main(idea=None, save=True, verbose=True)