"""Interactive CLI for the multi-agent research assistant."""
from dotenv import load_dotenv
load_dotenv()                      # load GROQ_API_KEY and TAVILY_API_KEY before imports use them

from src.multi_agent_research_assistant.graph import research

print("Multi-Agent Research Assistant — ask a research question. Ctrl+C to exit.\n")
while True:
    try:
        q = input("Question: ").strip()
        if not q:
            continue
        result = research(q)
        print("\n--- Answer ---")
        print(result["draft"])
        print(f"\n(sources gathered: {len(result['research'])}, "
              f"revisions: {result['revision_count']}, grounded: {result['valid']})\n")
    except KeyboardInterrupt:
        print("\nGoodbye!")
        break