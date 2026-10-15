"""Trajectory + grounding evals for the multi-agent system.
Checks each stage did its job, not just the final text.
"""
import sys, os, re, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv
load_dotenv()
from graph import research

QUESTIONS = [
    "What are the main differences between LangChain and LangGraph?",
    "What is retrieval-augmented generation used for?",
    "What is the Model Context Protocol (MCP)?",
]


def urls_in(text):
    return set(re.findall(r"https?://[^\s\)\]]+", text))


def run():
    rows = []
    for q in QUESTIONS:
        t0 = time.time()
        state = research(q)
        dt = time.time() - t0

        planned = len(state.get("plan", []))                      # planner worked?
        gathered = len(state.get("research", []))                 # tool use worked?
        source_urls = {f["url"] for f in state.get("research", [])}
        cited = urls_in(state.get("draft", ""))
        grounded_cite = bool(cited & source_urls)                 # cites real sources?

        rows.append({
            "q": q, "planned": planned, "gathered": gathered,
            "cites_real_source": grounded_cite,
            "validator_passed": state.get("valid"),
            "revisions": state.get("revision_count"), "secs": round(dt, 1),
        })

    print(f"{'planned':>7} {'sources':>7} {'cites':>6} {'valid':>6} {'rev':>4} {'sec':>5}  question")
    for r in rows:
        print(f"{r['planned']:>7} {r['gathered']:>7} {str(r['cites_real_source']):>6} "
              f"{str(r['validator_passed']):>6} {r['revisions']:>4} {r['secs']:>5}  {r['q'][:40]}")

    hit = sum(r["cites_real_source"] for r in rows)
    print(f"\nGrounded-citation rate: {hit}/{len(rows)}")


if __name__ == "__main__":
    run()