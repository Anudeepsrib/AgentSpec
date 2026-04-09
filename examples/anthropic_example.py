"""Example: Testing an Anthropic-based research agent with agentspec."""

from typing import Any

from agentspec import ContractRunner, contract


class ResearchAgent:
    """A research agent using Anthropic-style tool use."""

    def __init__(self) -> None:
        self.tools = {
            "web_search": self._web_search,
            "extract_info": self._extract_info,
            "synthesize": self._synthesize,
        }

    def _web_search(self, query: str) -> dict:
        """Search the web."""
        return {"results": [{"title": f"Result for {query}", "url": "https://example.com"}]}

    def _extract_info(self, url: str, question: str) -> dict:
        """Extract information from a URL."""
        return {"answer": f"Information about {question}", "source": url}

    def _synthesize(self, findings: list[dict]) -> dict:
        """Synthesize findings into a report."""
        return {"report": "Synthesized research report", "citations": len(findings)}

    def run(self, query: str, interceptor: Any = None) -> dict:
        """Execute research workflow."""
        # Simulate Claude-style tool use sequence
        # 1. Search for information
        search_result = self.tools["web_search"](query)
        if interceptor:
            interceptor.record("web_search", {"query": query}, search_result)

        # 2. Extract from top result
        if search_result["results"]:
            url = search_result["results"][0]["url"]
            extract_result = self.tools["extract_info"](url, query)
            if interceptor:
                interceptor.record("extract_info", {"url": url, "question": query}, extract_result)

            # 3. Synthesize
            synthesis = self.tools["synthesize"]([extract_result])
            if interceptor:
                interceptor.record("synthesize", {"findings": [extract_result]}, synthesis)

            return {
                "output": synthesis["report"],
                "citations": synthesis["citations"],
            }

        return {"output": "No results found", "citations": 0}


@contract("research_workflow")
def test_research_agent_executes_full_pipeline() -> None:
    """Test that research agent follows the expected workflow."""
    agent = ResearchAgent()
    runner = ContractRunner()

    result = runner.run(
        agent=agent.run, input="What are the latest developments in quantum computing?"
    )

    # Verify the research pipeline
    result.must_call("web_search")
    result.must_call("extract_info").immediately_after("web_search")
    result.must_call("extract_info").with_args_containing(url="https://")
    result.must_call("synthesize").after("extract_info")
    result.assert_output_contains("research report")


@contract("research_ordering")
def test_research_tools_execute_in_order() -> None:
    """Test that research tools execute in the correct order."""
    agent = ResearchAgent()
    runner = ContractRunner()

    result = runner.run(agent=agent.run, input="Research topic X")

    # Chain ordering assertions
    result.must_call("web_search")
    result.must_call("extract_info").after("web_search")
    result.must_call("synthesize").after("extract_info")

    # Verify we have exactly 3 calls in order
    result.assert_completed_in(3)


@contract("research_args")
def test_research_passes_correct_arguments() -> None:
    """Test that research agent passes correct arguments to tools."""
    agent = ResearchAgent()
    runner = ContractRunner()

    result = runner.run(agent=agent.run, input="quantum computing developments")

    # Check web search got the query
    result.must_call("web_search").with_args_containing(query="quantum computing")

    # Check synthesis received findings
    result.must_call("synthesize")


if __name__ == "__main__":
    test_research_agent_executes_full_pipeline()
    print("✓ test_research_agent_executes_full_pipeline passed")

    test_research_tools_execute_in_order()
    print("✓ test_research_tools_execute_in_order passed")

    test_research_passes_correct_arguments()
    print("✓ test_research_passes_correct_arguments passed")

    print("\nAll Anthropic example tests passed!")
