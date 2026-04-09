import asyncio
from typing import Any

import pytest

from agentspec.contract import ContractRunner, contract


async def async_tool(x: int) -> int:
    await asyncio.sleep(0.01)
    return x * 2


async def my_async_agent(input: str, interceptor: Any = None) -> str:
    # Manual tool wrapping for testing interceptor
    if interceptor:
        wrapped_tool = interceptor.wrap_tool_async(async_tool, "async_tool")
    else:
        wrapped_tool = async_tool

    res1 = await wrapped_tool(x=5)
    res2 = await wrapped_tool(x=10)
    return f"Done: {res1}, {res2}"


@pytest.mark.asyncio
async def test_async_agent_execution():
    runner = ContractRunner()
    result = await runner.arun(my_async_agent, "Do it")

    result.must_call("async_tool").exactly(2)
    result.must_call("async_tool").with_args(x=5)
    result.must_call("async_tool").with_args(x=10)
    result.assert_output_contains("Done: 10, 20")


@pytest.mark.asyncio
async def test_async_contract_decorator():
    @contract("async_test_contract")
    async def run_async_contract():
        runner = ContractRunner()
        result = await runner.arun(my_async_agent, "test")
        result.must_call("async_tool").exactly(2)
        return result

    result = await run_async_contract()
    assert result.trace.count_calls("async_tool") == 2
