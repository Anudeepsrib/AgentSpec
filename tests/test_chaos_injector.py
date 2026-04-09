import contextlib
from typing import Any

import pytest

from agentspec.chaos.injector import ChaosInjector
from agentspec.contract import ContractRunner


def normal_tool(x: int) -> int:
    return x * 2


async def async_tool(x: int) -> int:
    return x * 2


def my_agent(input: str, interceptor: Any = None, chaos: Any = None) -> str:
    tool_to_wrap = chaos.apply("normal_tool", normal_tool) if chaos else normal_tool
    wrapped = interceptor.wrap_tool(tool_to_wrap, "normal_tool")

    with contextlib.suppress(Exception):
        wrapped(x=5)

    with contextlib.suppress(Exception):
        wrapped(x=10)
    return "Done"


async def my_async_agent(input: str, interceptor: Any = None, chaos: Any = None) -> str:
    tool_to_wrap = chaos.apply_async("async_tool", async_tool) if chaos else async_tool
    wrapped = interceptor.wrap_tool_async(tool_to_wrap, "async_tool")

    with contextlib.suppress(Exception):
        await wrapped(x=5)

    with contextlib.suppress(Exception):
        await wrapped(x=10)
    return "Done"


def test_chaos_random_failures():
    injector = ChaosInjector(seed=42)
    injector.random_failures(probability=1.0)  # Always fail

    runner = ContractRunner()
    result = runner.run(my_agent, "Do it", context={"chaos": injector})

    # Tools should have failed with random error, but they were still called.
    # The trace records exceptions as well.
    assert result.trace.count_calls("normal_tool") == 2
    for call in result.trace.tool_calls:
        assert isinstance(call.response, RuntimeError)


@pytest.mark.asyncio
async def test_chaos_async():
    injector = ChaosInjector()
    injector.fail_tool("async_tool", after_calls=0, error="ValueError", message="Crash")

    runner = ContractRunner()
    result = await runner.arun(my_async_agent, "Do it", context={"chaos": injector})

    assert result.trace.count_calls("async_tool") == 2
    for call in result.trace.tool_calls:
        assert isinstance(call.response, ValueError)
