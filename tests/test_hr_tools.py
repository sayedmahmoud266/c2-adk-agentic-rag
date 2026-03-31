"""Tests for src/tools/hr_tools.py."""
from unittest.mock import MagicMock

from src.tools.hr_tools import create_hr_tools


def _make_retriever(return_value: str = "mock result") -> MagicMock:
    retriever = MagicMock()
    retriever.retrieve.return_value = return_value
    return retriever


def test_create_hr_tools_returns_two_tools():
    tools = create_hr_tools(_make_retriever())
    assert len(tools) == 2


def test_search_hr_documents_calls_retriever():
    retriever = _make_retriever("Annual leave is 25 days.")
    tools = create_hr_tools(retriever)

    # Find the search_hr_documents tool and call its underlying function
    search_tool = next(t for t in tools if t.name == "search_hr_documents")
    result = search_tool.func("annual leave policy")

    retriever.retrieve.assert_called_once_with("annual leave policy")
    assert "Annual leave is 25 days." in result


def test_get_benefits_by_profile_builds_query():
    retriever = _make_retriever("Benefits for engineers.")
    tools = create_hr_tools(retriever)

    benefits_tool = next(t for t in tools if t.name == "get_benefits_by_profile")
    result = benefits_tool.func("Engineering", "Senior Engineer")

    call_arg = retriever.retrieve.call_args[0][0]
    assert "Senior Engineer" in call_arg
    assert "Engineering" in call_arg
    assert "Benefits for engineers." in result
