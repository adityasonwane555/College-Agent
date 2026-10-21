import httpx
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from ..config import settings
from ..security.url_validation import is_safe_url


def clean_html_content(html: str, max_chars: int = 1500) -> str:
    """Extracts readable text from HTML safely."""
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


async def search_internet(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Performs external web search via SearXNG when enabled.
    Returns safe grounded search snippets with URLs.
    """
    if not settings.WEB_SEARCH_ENABLED:
        return {
            "status": "disabled",
            "message": "Web search is disabled in configuration. External Internet information cannot be retrieved.",
            "sources": []
        }

    if not settings.SEARXNG_BASE_URL:
        return {
            "status": "unavailable",
            "message": "No SearXNG search endpoint configured.",
            "sources": []
        }

    search_url = f"{settings.SEARXNG_BASE_URL.rstrip('/')}/search"
    params = {
        "q": query,
        "format": "json",
        "language": "en"
    }

    try:
        async with httpx.AsyncClient(timeout=settings.WEB_SEARCH_TIMEOUT_SECONDS) as client:
            resp = await client.get(search_url, params=params)
            if resp.status_code != 200:
                return {
                    "status": "error",
                    "message": f"SearXNG returned HTTP {resp.status_code}.",
                    "sources": []
                }
            data = resp.json()
            results = data.get("results", [])[:num_results]

            filtered_sources = []
            snippets = []

            for item in results:
                raw_url = item.get("url", "")
                is_safe, reason = is_safe_url(raw_url)
                if not is_safe:
                    continue  # Skip unsafe / internal URLs

                title = item.get("title", "Web Result")
                snippet = item.get("content", "")
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
                    "sources": []
                }

            return {
                "status": "success",
                "content": "\n\n".join(snippets),
                "sources": filtered_sources
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to execute web search: {str(e)}",
            "sources": []
        }
