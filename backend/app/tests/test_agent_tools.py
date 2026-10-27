import pytest
from app.agent.tool_registry import execute_tool, TOOL_FUNCTIONS
from app.agent.orchestrator import session_manager, orchestrator
from app.database.seed import seed_database
from app.documents.ingestion import ingest_sample_documents
from app.config import DATA_DIR


@pytest.fixture(autouse=True)
def setup_test_data():
    seed_database()
    sample_docs_dir = DATA_DIR / "sample_documents"
    ingest_sample_documents(sample_docs_dir)


@pytest.mark.asyncio
async def test_tool_execution_registered():
    # Test existing registered tool
    res = await execute_tool("get_department", {"name": "Computer"})
    assert "Computer Engineering" in res
    assert "Floor" in res

    # Test unknown tool handling
    unknown_res = await execute_tool("non_existent_tool", {})
    assert "not registered" in unknown_res


@pytest.mark.asyncio
async def test_missing_college_information_handling():
    res = await execute_tool("get_faculty", {"name": "NonExistentProfessorXYZ"})
    assert "No faculty member matching" in res


@pytest.mark.asyncio
async def test_document_search_citations():
    res = await execute_tool("search_college_documents", {"query": "admission eligibility marks"})
    assert isinstance(res, dict)
    assert res["status"] == "found"
    assert len(res["citations"]) > 0
    citation = res["citations"][0]
    assert len(citation["source"]) > 0
    assert citation["page"] >= 1
    assert len(citation["snippet"]) > 0


def test_session_isolation():
    session_manager.reset_session("session_user_A")
    session_manager.reset_session("session_user_B")

    session_manager.add_message("session_user_A", {"role": "user", "content": "My secret key is ALPHA123"})
    session_manager.add_message("session_user_B", {"role": "user", "content": "Hello Buddy"})

    history_A = session_manager.get_history("session_user_A")
    history_B = session_manager.get_history("session_user_B")

    # Verify session A contains ALPHA123, but session B does not
    assert any("ALPHA123" in m.get("content", "") for m in history_A)
    assert not any("ALPHA123" in m.get("content", "") for m in history_B)


@pytest.mark.asyncio
async def test_orchestrator_run_with_tools():
    # Test orchestrator running with simulated reception agent
    res = await orchestrator.run(
        user_message="Where is the Computer Science department and who is the HOD?",
        session_id="test_orchestrator_sess"
    )
    assert res["response"] is not None
    assert "Computer" in res["response"] or "Rama" in res["response"]
    assert res["tool_iterations"] <= 5
