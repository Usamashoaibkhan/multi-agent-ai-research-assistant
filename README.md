# Multi-Agent Research Assistant

A small team of LLM agents that researches a question on the web and returns a cited,
fact-checked answer. A planner writes search queries, a researcher runs a web-search tool,
a writer drafts the answer, and a validator checks it against the sources and sending it back
for a rewrite if it isn't grounded.

<!-- Add a terminal GIF of a research run here. -->
<!-- ![demo](docs/demo.gif) -->

## How it works

```
question → planner → researcher → writer → validator ──grounded?──▶ answer
                     (web search)      ▲                    │
                     └──── revise (max 2) ──────────────────┘
```

Built on LangGraph rather than a linear chain, because the validator→writer step is a
loop and needs a safe stop condition,a plain chain can't do that. The planner and
validator return validated Pydantic objects so the routing logic is reliable.

**Stack:** Python · LangGraph · Groq (`openai/gpt-oss-120b`) · Tavily · Pydantic

## Run it

Needs Python 3.11.

```bash
python -m venv .venv && .venv\Scripts\activate     # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
# add two keys to a .env file:
#   GROQ_API_KEY=...     (console.groq.com)
#   TAVILY_API_KEY=...   (app.tavily.com, free tier)

python -m src.multi_agent_research_assistant.app
```

Each run prints the answer and a status line: sources gathered, revisions, and whether the
validator passed it.

## Results

The eval suite checks the whole trajectory, not just the final text (`python evals/run_evals.py`):



## Notes

Structured output uses JSON mode (`method="json_mode"`), since the newer Groq models reject
tool-calling-based structured output. A revision cap stops the self-correction loop after
two attempts so it can't loop forever and waste tokens.
