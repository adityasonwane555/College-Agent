import asyncio
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.agent.orchestrator import AgentOrchestrator

queries = [
    "Who is the HOD of Computer Engineering?",
    "Who is the HOD of IT?",
    "Who is the HOD of AI and Data Science?",
    "Who is the HOD of Civil Engineering?",
    "Who is the HOD of Mechanical Engineering?",
    "Who is the HOD of E&TC?",
    "Who is the HOD of MCA?",
    "Who is the Principal?",
    "Tell me about Dr Rama Gaikwad",
    "Where is Dr Amit Kadam cabin?",
    "Where is the Computer department located?"
]

async def main():
    orchestrator = AgentOrchestrator()
    for q in queries:
        res = await orchestrator.run(q)
        print(f"QUERY: {q}")
        print(f"ANSWER:\n{res['response']}")
        cites = [f"[{c.source} p.{c.page} - {c.snippet}]" for c in res.get("citations", [])]
        print(f"CITATIONS: {' | '.join(cites)}")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
