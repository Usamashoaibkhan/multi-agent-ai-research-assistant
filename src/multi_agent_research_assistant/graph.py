"""Builds and compiles the LangGraph: nodes, edges, and the revise/stop decision."""
from langgraph.graph import StateGraph, END
from src.multi_agent_research_assistant.agents import (
    ResearchState, MAX_REVISIONS,
    plan_node, research_node, write_node, validate_node,
)


def route_after_validation(state: ResearchState) -> str:
    """Conditional edge: stop if grounded or out of retries, else revise."""
    if state["valid"] or state["revision_count"] >= MAX_REVISIONS:
        return "end"
    return "revise"


def build_app():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", plan_node)
    graph.add_node("researcher", research_node)
    graph.add_node("writer", write_node)
    graph.add_node("validator", validate_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "validator")

    # The cycle: validator decides whether to loop back to the writer or finish.
    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {"revise": "writer", "end": END},
    )

    return graph.compile()


# Build once at import so app.py and evals reuse it.
research_app = build_app()


def research(question: str) -> dict:
    """Run the full pipeline. Returns the final state; answer is in ['draft']."""
    return research_app.invoke({"question": question, "revision_count": 0})