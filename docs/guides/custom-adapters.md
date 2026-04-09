# Custom Adapters

AgentSpec ships with adapters for OpenAI, Anthropic, and LangChain. You can build your own adapter for any framework.

## Adapter Architecture

All adapters extend `BaseAdapter` and implement two methods:

```python
from agentcontract.adapters.base import BaseAdapter

class MyFrameworkAdapter(BaseAdapter):
    def run(self, agent, input, context=None):
        """Synchronous agent execution with interception."""
        ...

    async def arun(self, agent, input, context=None):
        """Async agent execution with interception."""
        ...
```

## Building a Custom Adapter

### Step 1: Extend BaseAdapter

```python
from agentcontract.adapters.base import BaseAdapter
from typing import Any
import time

class CrewAIAdapter(BaseAdapter):
    """Adapter for CrewAI agents."""

    def run(self, agent, input, context=None):
        # Option A: If agent is a CrewAI Crew object
        if hasattr(agent, "kickoff"):
            return self._run_crew(agent, input, context)

        # Option B: If agent is a callable
        if callable(agent):
            return agent(input, interceptor=self._interceptor, **(context or {}))

        raise ValueError(f"Unsupported agent type: {type(agent)}")

    def _run_crew(self, crew, input, context=None):
        # Patch crew's tool execution to record calls
        original_execute = crew._execute_tool

        def patched_execute(tool_name, tool_input):
            start = time.time()
            result = original_execute(tool_name, tool_input)
            duration = (time.time() - start) * 1000
            self._interceptor.record(tool_name, tool_input, result, duration)
            return result

        crew._execute_tool = patched_execute
        try:
            return crew.kickoff(inputs=input if isinstance(input, dict) else {"input": input})
        finally:
            crew._execute_tool = original_execute

    async def arun(self, agent, input, context=None):
        if hasattr(agent, "akickoff"):
            # async version
            ...
        raise NotImplementedError("Async not supported for CrewAI adapter")
```

### Step 2: Register with ContractRunner

```python
runner = ContractRunner(adapter=CrewAIAdapter(interceptor))
```

Or manually:

```python
runner = ContractRunner()
runner._adapter = CrewAIAdapter(runner._interceptor)
```

## Using the Interceptor Directly

For frameworks where patching is impractical, pass the interceptor to your agent and call `record()` manually:

```python
def my_custom_agent(user_input, interceptor=None, **kwargs):
    # Your framework's tool calling logic
    result = my_framework.call_tool("search", {"q": user_input})

    # Record the call manually
    interceptor.record("search", {"q": user_input}, result)

    return result

runner = ContractRunner()  # No adapter needed
result = runner.run(agent=my_custom_agent, input="test")
result.must_call("search")
```

## Using the LangChain Callback Handler Standalone

The `AgentSpecCallbackHandler` can be used without the adapter:

```python
from agentcontract.adapters.langchain import AgentSpecCallbackHandler
from agentcontract.interceptor import TraceInterceptor

interceptor = TraceInterceptor()
handler = AgentSpecCallbackHandler(interceptor)

# Pass to any LangChain agent
agent.invoke({"input": "query"}, config={"callbacks": [handler]})
```

## Testing Your Adapter

```python
def test_my_adapter():
    interceptor = TraceInterceptor()
    adapter = CrewAIAdapter(interceptor)

    mock_agent = create_mock_crew()

    interceptor.start()
    adapter.run(mock_agent, input="test")
    interceptor.stop()

    assert len(interceptor.trace.tool_calls) > 0
```
