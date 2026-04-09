import pytest
from typing import Any

from agentcontract.contract import ContractRunner
from agentcontract.exceptions import ToolNotCalled, ToolCalledUnexpectedly

def tool_a(x: int) -> int:
    return x + 1

def tool_b(y: int) -> int:
    return y * 2

def my_multi_agent(input: str, interceptor: Any = None) -> str:
    # Agent 1 calls tool_a
    wrapped_a = interceptor.wrap_tool(tool_a, "tool_a", agent_id="agent_1")
    wrapped_a(x=5)
    
    # Agent 2 calls tool_b
    wrapped_b = interceptor.wrap_tool(tool_b, "tool_b", agent_id="agent_2")
    wrapped_b(y=10)
    
    # Agent 1 calls tool_b
    wrapped_b_for_1 = interceptor.wrap_tool(tool_b, "tool_b", agent_id="agent_1")
    wrapped_b_for_1(y=3)
    
    return "Done"

def test_multi_agent_execution():
    runner = ContractRunner()
    result = runner.run(my_multi_agent, "Do it")
    
    # Assertions across all agents
    result.must_call("tool_a").exactly(1)
    result.must_call("tool_b").exactly(2)
    
    # Assertions for agent_1
    result.must_call("tool_a", agent_id="agent_1").exactly(1)
    result.must_call("tool_b", agent_id="agent_1").exactly(1)
    result.must_not_call("tool_c", agent_id="agent_1")
    
    # Assertions for agent_2
    result.must_not_call("tool_a", agent_id="agent_2")
    result.must_call("tool_b", agent_id="agent_2").exactly(1)
    
    # Check args for specific agent
    result.must_call("tool_b", agent_id="agent_2").with_args(y=10)
    result.must_call("tool_b", agent_id="agent_1").with_args(y=3)
    
    # Check order for specific agent
    result.must_call("tool_a", agent_id="agent_1").before("tool_b", other_agent_id="agent_1")
    
    # Check tool_call_count
    result.tool_call_count("tool_a", agent_id="agent_1").exactly(1)
    result.tool_call_count("tool_a", agent_id="agent_2").exactly(0)
