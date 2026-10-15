"""The web-search tool the Researcher agent uses.
A 'tool' is just a function the system can call; here it wraps Tavily's API.
"""
import os
from tavily import TavilyClient

_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def web_search(query: str, max_results: int = 3) -> list[dict]:
    """Search the web and return a clean list of {title, url, content}."""
    resp = _client.search(query=query, max_results=max_results)
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
        for r in resp.get("results", [])
    ]
