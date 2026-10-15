"""The agents: LLM setup, structured-output schemas, prompts, and node functions.
Each node is a function: state -> partial state update.
"""
from typing import TypedDict, List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from src.multi_agent_research_assistant.tools import web_search

CHAT_MODEL = "openai/gpt-oss-120b" 
MAX_REVISIONS = 2

llm = ChatGroq(model=CHAT_MODEL, temperature=0)


# --- Shared state: the whiteboard every node reads/writes ---
class ResearchState(TypedDict):
    question: str
    plan: List[str]          # search queries from the planner
    research: List[dict]     # findings from the researcher
    draft: str               # the writer's answer
    valid: bool              # validator verdict
    reason: str              # why the validator passed/failed it
    revision_count: int      # guards against infinite loops


# --- Structured-output schemas (reliable, machine-readable agent outputs) ---
class SearchPlan(BaseModel):
    queries: List[str] = Field(description="2 to 4 focused web-search queries")

class Validation(BaseModel):
    grounded: bool = Field(description="True if the answer is fully supported by the sources")
    reason: str = Field(default="", description="One sentence explaining the verdict")


# --- Node 1: PLANNER — question -> search queries ---
planner_llm = llm.with_structured_output(SearchPlan, method="json_mode")

def plan_node(state: ResearchState) -> dict:
    q = state["question"]
    plan = planner_llm.invoke(
        f"You are a research planner. Break this question into 2-4 focused, "
        f"non-overlapping web search queries. Respond in JSON.\n\nQuestion: {q}"
    )
    return {"plan": plan.queries}

# --- Node 2: RESEARCHER — runs the search tool for each query ---
def research_node(state: ResearchState) -> dict:
    findings = []
    for query in state["plan"]:
        findings.extend(web_search(query, max_results=3))
    return {"research": findings}


# --- Node 3: WRITER — findings -> cited answer ---
def _format_findings(findings: List[dict]) -> str:
    return "\n\n".join(
        f"[{i}] {f['title']} ({f['url']})\n{f['content']}"
        for i, f in enumerate(findings, 1)
    )

def write_node(state: ResearchState) -> dict:
    context = _format_findings(state["research"])
    feedback = ""
    if state.get("reason") and not state.get("valid", True):
        feedback = f"\n\nYour previous draft was rejected because: {state['reason']}. Fix it."
    prompt = (
        f"You are a research writer. Answer the question using ONLY the sources below. "
        f"Cite sources inline with their [number]. If the sources don't fully answer it, "
        f"say what is missing rather than inventing facts.{feedback}\n\n"
        f"Question: {state['question']}\n\nSources:\n{context}"
    )
    draft = llm.invoke(prompt).content
    return {"draft": draft}


# --- Node 4: VALIDATOR — is the draft grounded in the sources? ---
validator_llm = llm.with_structured_output(Validation, method="json_mode")

def validate_node(state: ResearchState) -> dict:
    context = _format_findings(state["research"])
    verdict = validator_llm.invoke(
        f"You are a fact-checker. Decide whether the ANSWER is fully supported by the "
        f"SOURCES. If any claim is not backed by the sources, it is NOT grounded. "
        f'Respond in JSON with exactly two keys: "grounded" (true or false) and '
        f'"reason" (one sentence explaining the verdict).\n\n'
        f"SOURCES:\n{context}\n\nANSWER:\n{state['draft']}"
    )
    count = state.get("revision_count", 0)
    if not verdict.grounded:
        count += 1
    return {"valid": verdict.grounded, "reason": verdict.reason, "revision_count": count}