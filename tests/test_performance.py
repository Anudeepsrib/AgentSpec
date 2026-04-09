import time
import pytest
from typing import Any

from agentcontract.contract import ContractRunner
from agentcontract.exceptions import ContractViolation

def slow_tool(t: float) -> str:
    time.sleep(t)
    return "Done"

def agent_with_slow_tool(input: float, interceptor: Any = None) -> str:
    wrapped = interceptor.wrap_tool(slow_tool, "slow_tool")
    wrapped(t=input)
    return "Done"

def test_performance_assertions():
    runner = ContractRunner()
    # Runs in ~100ms
    result = runner.run(agent_with_slow_tool, 0.1)
    
    # Should pass
    result.assert_total_duration_under(200)
    result.must_call("slow_tool").within_ms(150)
    
    # Should fail assertion
    with pytest.raises(ContractViolation, match="exceeding limit of 50ms"):
        result.assert_total_duration_under(50)
        
    with pytest.raises(ContractViolation, match="completed within 50ms"):
        result.must_call("slow_tool").within_ms(50)
