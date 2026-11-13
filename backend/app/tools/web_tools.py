"""
BUDDY AI 2.0 — External Web Research & Search Toolset

Architecture & Search Strategy:
  - Dual-Engine Fallback Pipeline:
      - Primary Engine (SearXNG): Fast local/remote metasearch query returning structured JSON results.
      - Secondary Engine (DuckDuckGo Lite): Zero-config public search fallback when local SearXNG is unavailable or offline.
  - Security & SSRF Protection:
      - Every extracted result URL is filtered through is_safe_url() to prevent Server-Side Request Forgery (SSRF),
        local IP scraping (127.0.0.1, 192.168.x.x, 10.x.x.x), or internal network probing.
  - HTML Cleansing & Noise Filtering:
      - Strips scripts, styles, navigations, footers, and headers via BeautifulSoup to produce clean text snippets.
  - Grounded Citation Assembly:
      - Normalizes web search results into CitationModel dictionaries containing titles, source URLs, and contextual snippets.
"""

import httpx
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from ..config import settings
from ..security.url_validation import is_safe_url


def clean_html_content(html: str, max_chars: int = 1500) -> str:
    """
    Extracts readable plain text from raw HTML content, removing scripts, stylesheets, and navigation tags.

    Args:
        html: Raw HTML string.
        max_chars: Maximum character limit for output text (default: 1500).

    Returns:
        str: Cleaned, whitespace-normalized plain text snippet.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
        text = soup.get_text(separator=" ", strip=True)
        # Collapse multiple whitespaces
        cleaned = " ".join(text.split())
        return cleaned[:max_chars]
    except Exception:
        return ""


async def _search_searxng(query: str, num_results: int = 4) -> List[Dict[str, str]]:
    """
    Queries the configured SearXNG metasearch instance via its JSON API.

    Args:
        query: User's search query string.
        num_results: Maximum number of candidate results to return (default: 4).

    Returns:
        List[Dict[str, str]]: Parsed search results with title, url, and snippet fields.
    """
    if not settings.SEARXNG_BASE_URL:
        return []
    search_url = f"{settings.SEARXNG_BASE_URL.rstrip('/')}/search"
    params = {"q": query, "format": "json", "language": "en"}
    try:
        async with httpx.AsyncClient(timeout=min(settings.WEB_SEARCH_TIMEOUT_SECONDS, 4.0)) as client:
            resp = await client.get(search_url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("results", [])[:num_results]:
                    results.append({
                        "title": item.get("title", "Web Result"),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", "")
                    })
                return results
    except Exception:
        pass
    return []


async def _search_duckduckgo(query: str, num_results: int = 4) -> List[Dict[str, str]]:
    """
    Scrapes DuckDuckGo Lite HTML interface as a zero-dependency fallback when SearXNG is unavailable.

    Args:
        query: User's search query string.
        num_results: Maximum number of candidate results to return (default: 4).

    Returns:
        List[Dict[str, str]]: Extracted search results with title, url, and snippet fields.
    """
    url = "https://lite.duckduckgo.com/lite/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.post(url, data={"q": query}, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                links = soup.find_all("a", class_="result-link")
                snippets = soup.find_all("td", class_="result-snippet")
                results = []
                for a, s in list(zip(links, snippets))[:num_results]:
                    href = a.get("href", "")
                    title = a.get_text(strip=True)
                    snippet = s.get_text(strip=True)
                    if href and title:
                        results.append({
                            "title": title,
                            "url": href,
                            "snippet": snippet
                        })
                return results
    except Exception:
        pass
    return []


async def search_internet(query: str, num_results: int = 4) -> Dict[str, Any]:
    """
    Performs external web research using SearXNG with seamless failover to DuckDuckGo Lite.
    Filters result URLs against SSRF threats and formats findings with grounded citations.

    Args:
        query: Search keywords or topic phrase.
        num_results: Maximum number of verified results to return (default: 4).

    Returns:
        Dict[str, Any]: Search report containing aggregated content text, citations, and source metadata.
    """
    if not settings.WEB_SEARCH_ENABLED:
        return {
            "status": "disabled",
            "message": "Web search is disabled in configuration.",
            "sources": []
        }

    # Strategy 1: Attempt configured SearXNG
    results = await _search_searxng(query, num_results)

    # Strategy 2: Seamless fallback to DuckDuckGo Lite if SearXNG is offline
    if not results:
        results = await _search_duckduckgo(query, num_results)

    filtered_sources = []
    snippets = []

    for item in results:
        raw_url = item.get("url", "")
        is_safe, reason = is_safe_url(raw_url)
        if not is_safe:
            continue

        title = item.get("title", "Web Result")
        snippet = item.get("snippet", "")
        filtered_sources.append({
            "title": title,
            "url": raw_url,
            "snippet": snippet
        })
        snippets.append(f"Title: {title}\nURL: {raw_url}\nSnippet: {snippet}")

    if not filtered_sources:
        return {
            "status": "not_found",
            "message": f"No accessible web search results found for '{query}'.",
            "citations": [],
            "sources": []
        }

    citations = []
    for item in filtered_sources:
        citations.append({
            "source": item.get("url") or item.get("title"),
            "section": item.get("title"),
            "page": None,
            "relevance_score": 0.95,
            "snippet": item.get("snippet", "")
        })

    return {
        "status": "success",
        "content": "\n\n".join(snippets),
        "citations": citations,
        "sources": filtered_sources
    }
