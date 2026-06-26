# LangChain and LangGraph Adapters

AgentSpec uses LangChain-compatible callbacks to record tool calls from
LangChain runnables, legacy `AgentExecutor` objects, and LangGraph compiled
graphs.

Install the optional dependencies:

```bash
pip install "agentspec-contracts[langchain]"
```

## Adapter Usage

```python
from agentspec import ContractRunner


runner = ContractRunner(adapter="langchain", persist=False)
result = runner.run(agent=compiled_graph, input={"messages": ["book NYC"]})

result.must_call("search_flights")
result.must_call("reserve_flight").after("search_flights")
```

The adapter passes `config={"callbacks": [handler]}` when the agent exposes
`.invoke()` or `.ainvoke()`.

## Direct Callback Usage

```python
from agentspec.adapters.langchain import AgentSpecCallbackHandler
from agentspec.interceptor import TraceInterceptor


interceptor = TraceInterceptor()
handler = AgentSpecCallbackHandler(interceptor)

interceptor.start()
graph.invoke({"messages": ["book NYC"]}, config={"callbacks": [handler]})
interceptor.stop()
```

See:

- `examples/langchain_adapter_example.py`
- `examples/langgraph_adapter_example.py`
