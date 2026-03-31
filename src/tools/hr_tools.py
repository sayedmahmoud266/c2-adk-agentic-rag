"""ADK tools wrapping the HR RAG retriever."""
from google.adk.tools import FunctionTool

from src.rag.retriever import HRRetriever


def create_hr_tools(retriever: HRRetriever) -> list:
    """Create ADK FunctionTool instances backed by the HR retriever."""

    def search_hr_documents(query: str) -> str:
        """Search the HR knowledge base for policies, procedures, and guidelines.

        Use this tool for any question about HR policies, benefits, leave,
        performance management, code of conduct, or general HR procedures.
        Results are re-ranked by semantic similarity and keyword relevance.

        Args:
            query: Natural language question or topic to search for.

        Returns:
            Relevant excerpts from HR documents with source citations.
        """
        return retriever.retrieve(query)

    def get_benefits_by_profile(department: str, position: str) -> str:
        """Retrieve benefits and entitlements relevant to a specific role.

        Use this tool when the user asks about their personal entitlements,
        allowances, or benefits that may vary by department or seniority level.

        Args:
            department: The user's department (e.g. 'Engineering', 'Finance').
            position: The user's job title (e.g. 'Senior Engineer', 'Analyst').

        Returns:
            Relevant entitlement and benefit information for the given profile.
        """
        role_query = f"benefits entitlements allowances for {position} in {department}"
        return retriever.retrieve(role_query)

    def get_full_document(source_filename: str) -> str:
        """Retrieve the complete content of a specific HR document.

        Use this when search results provide insufficient context, or when the
        user asks for comprehensive or detailed information about a topic and
        the retrieved chunks appear to be incomplete or truncated.

        Args:
            source_filename: Exact filename of the document as returned by
                list_hr_documents (e.g. 'leave_policy.txt').

        Returns:
            Full document text with all sections in order.
        """
        return retriever.retrieve_full_document(source_filename)

    def list_hr_documents() -> str:
        """List all HR documents available in the knowledge base.

        Use this to discover what documents are indexed before calling
        get_full_document, or when the user asks what HR documents exist.

        Returns:
            Formatted list of available document filenames.
        """
        return retriever.list_documents()

    return [
        FunctionTool(search_hr_documents),
        FunctionTool(get_benefits_by_profile),
        FunctionTool(get_full_document),
        FunctionTool(list_hr_documents),
    ]
