"""Tests for the streaming-first agent runtime and its safety boundaries."""
import asyncio

import pytest

from body_of_secrets.brain.agent_runtime import (
    AgentRuntime, ModelEvent, PermissionPolicy, ToolCall, ToolRegistry, ToolSpec,
)


class FakeBackend:
    def __init__(self, turns):
        self.turns = list(turns)
        self.calls = []

    async def stream(self, messages, *, static_prompt, dynamic_prompt, tools):
        self.calls.append((list(messages), static_prompt, dynamic_prompt, list(tools)))
        for event in self.turns.pop(0):
            yield event


async def collect(runtime, prompt="hello"):
    return [event async for event in runtime.run(prompt)]


def test_streams_text_and_completes():
    backend = FakeBackend([[ModelEvent("text", text="hello "), ModelEvent("text", text="world"),
                            ModelEvent("complete")]])
    events = asyncio.run(collect(AgentRuntime(backend)))
    assert [e.data["text"] for e in events if e.kind == "text"] == ["hello ", "world"]
    assert events[-1].kind == "completed"
    assert events[-1].data["text"] == "hello world"


def test_unknown_tool_is_rejected_and_model_continues():
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("c1", "shell", {}))],
        [ModelEvent("text", text="I cannot run that tool."), ModelEvent("complete")],
    ])
    events = asyncio.run(collect(AgentRuntime(backend)))
    denied = next(e for e in events if e.kind == "tool_result")
    assert denied.data["status"] == "REJECTED"
    assert events[-1].kind == "completed"


def test_mutating_and_destructive_tools_are_denied_by_default():
    called = []
    registry = ToolRegistry()
    async def write_file(args):
        called.append(args)
    async def delete_file(args):
        called.append(args)
    registry.register(ToolSpec("write_file", write_file, is_read_only=False))
    registry.register(ToolSpec("delete_file", delete_file,
                               is_read_only=False, is_destructive=True))
    backend = FakeBackend([[
        ModelEvent("tool_call", tool_call=ToolCall("a", "write_file", {"path": "x"})),
        ModelEvent("tool_call", tool_call=ToolCall("b", "delete_file", {"path": "x"})),
    ], [ModelEvent("text", text="done"), ModelEvent("complete")]])
    events = asyncio.run(collect(AgentRuntime(backend, registry)))
    statuses = [e.data["status"] for e in events if e.kind == "tool_result"]
    assert statuses == ["DENIED", "DENIED"]
    assert called == []


def test_explicit_policy_allows_mutating_but_not_destructive():
    registry = ToolRegistry()
    called = []
    async def write_file(args):
        called.append(args)
    async def delete_file(args):
        called.append(args)
    registry.register(ToolSpec("write_file", write_file, is_read_only=False))
    registry.register(ToolSpec("delete_file", delete_file,
                               is_read_only=False, is_destructive=True))
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("a", "write_file", {"path": "x"})),
         ModelEvent("tool_call", tool_call=ToolCall("b", "delete_file", {"path": "x"}))],
        [ModelEvent("complete")],
    ])
    policy = PermissionPolicy(allow_mutating=True, allow_destructive=False)
    events = asyncio.run(collect(AgentRuntime(backend, registry, permissions=policy)))
    statuses = [e.data["status"] for e in events if e.kind == "tool_result"]
    assert statuses == ["OK", "DENIED"]
    assert called == [{"path": "x"}]


def test_read_only_concurrency_safe_tools_run_concurrently():
    active = 0
    peak = 0

    async def handler(args):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1
        return args["value"]

    registry = ToolRegistry()
    registry.register(ToolSpec("lookup", handler, is_read_only=True, is_concurrency_safe=True))
    backend = FakeBackend([[
        ModelEvent("tool_call", tool_call=ToolCall("a", "lookup", {"value": "A"})),
        ModelEvent("tool_call", tool_call=ToolCall("b", "lookup", {"value": "B"})),
    ], [ModelEvent("complete")]])
    asyncio.run(collect(AgentRuntime(backend, registry)))
    assert peak == 2


def test_tool_exception_is_recorded_and_does_not_abort_loop():
    def broken(args):
        raise RuntimeError("ordinary failure")
    registry = ToolRegistry()
    registry.register(ToolSpec("lookup", broken, is_read_only=True))
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("a", "lookup", {}))],
        [ModelEvent("text", text="recovered"), ModelEvent("complete")],
    ])
    events = asyncio.run(collect(AgentRuntime(backend, registry)))
    result = next(e for e in events if e.kind == "tool_result")
    assert result.data["status"] == "ERROR"
    assert events[-1].data["text"] == "recovered"


def test_turn_limit_is_bounded():
    backend = FakeBackend([[ModelEvent("tool_call", tool_call=ToolCall(str(i), "missing", {}))]
                           for i in range(3)])
    events = asyncio.run(collect(AgentRuntime(backend, max_turns=2)))
    assert events[-1].kind == "limit_reached"
    assert events[-1].data["max_turns"] == 2


def test_empty_prompt_is_rejected():
    backend = FakeBackend([])
    with pytest.raises(ValueError, match="prompt"):
        asyncio.run(collect(AgentRuntime(backend), prompt="  "))


def test_duplicate_tool_names_are_rejected():
    registry = ToolRegistry()
    registry.register(ToolSpec("lookup", lambda args: "ok", is_read_only=True))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(ToolSpec("lookup", lambda args: "again", is_read_only=True))



def test_sync_read_only_handler_does_not_block_event_loop_and_times_out():
    import time

    def slow_lookup(args):
        time.sleep(0.05)
        return "late"

    registry = ToolRegistry()
    registry.register(ToolSpec("lookup", slow_lookup, is_read_only=True))
    backend = FakeBackend([[
        ModelEvent("tool_call", tool_call=ToolCall("a", "lookup", {}))
    ], [ModelEvent("complete")]])
    events = asyncio.run(collect(AgentRuntime(
        backend, registry, tool_timeout_seconds=0.005
    )))
    result = next(e for e in events if e.kind == "tool_result")
    assert result.data["status"] == "TIMEOUT"


def test_sync_mutating_handler_is_rejected_at_registration():
    with pytest.raises(TypeError, match="mutating tools must use async"):
        ToolSpec("write_file", lambda args: "written", is_read_only=False)


def test_tool_call_messages_follow_structured_call_response_contract():
    registry = ToolRegistry()
    registry.register(ToolSpec("lookup", lambda args: "found", is_read_only=True))
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("call-1", "lookup", {"q": "x"}))],
        [ModelEvent("complete")],
    ])
    asyncio.run(collect(AgentRuntime(backend, registry)))
    second_request = backend.calls[1][0]
    assistant = next(message for message in second_request if message["role"] == "assistant")
    tool = next(message for message in second_request if message["role"] == "tool")
    assert assistant["tool_calls"][0]["id"] == "call-1"
    assert assistant["tool_calls"][0]["function"]["arguments"] == {"q": "x"}
    assert tool["tool_call_id"] == "call-1"
    assert tool["name"] == "lookup"


def test_backend_retry_only_occurs_before_any_stream_event():
    class RetryBackend:
        def __init__(self):
            self.calls = 0
        async def stream(self, messages, *, static_prompt, dynamic_prompt, tools):
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("not connected")
            yield ModelEvent("text", text="ok")
            yield ModelEvent("complete")

    backend = RetryBackend()
    events = asyncio.run(collect(AgentRuntime(backend, max_backend_retries=1)))
    assert backend.calls == 2
    assert sum(e.kind == "backend_retry" for e in events) == 1
    assert events[-1].data["text"] == "ok"


def test_backend_does_not_retry_after_partial_output():
    class PartialFailureBackend:
        def __init__(self):
            self.calls = 0
        async def stream(self, messages, *, static_prompt, dynamic_prompt, tools):
            self.calls += 1
            yield ModelEvent("text", text="partial")
            raise ConnectionError("connection dropped")

    backend = PartialFailureBackend()
    events = asyncio.run(collect(AgentRuntime(backend, max_backend_retries=3)))
    assert backend.calls == 1
    assert [e.data["text"] for e in events if e.kind == "text"] == ["partial"]
    assert events[-1].kind == "state"
    assert events[-1].data["status"] == "FAILED"


def test_invalid_context_compactor_result_fails_cleanly():
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("first", "missing", {}))],
        [ModelEvent("complete")],
    ])
    runtime = AgentRuntime(backend, compact_after_messages=2, compactor=lambda messages: "bad")
    events = asyncio.run(collect(runtime))
    assert events[-1].kind == "state"
    assert events[-1].data["status"] == "FAILED"
    assert any(e.kind == "error" for e in events)


def test_context_fallback_preserves_initial_user_prompt():
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("1", "missing", {}))],
        [ModelEvent("tool_call", tool_call=ToolCall("2", "missing", {}))],
        [ModelEvent("complete")],
    ])
    runtime = AgentRuntime(backend, max_turns=3, compact_after_messages=2,
                           keep_recent_messages=1)
    asyncio.run(collect(runtime, prompt="original request"))
    last_messages = backend.calls[-1][0]
    assert any(m.get("role") == "user" and m.get("content") == "original request"
               for m in last_messages)
    declared_ids = {
        call["id"]
        for message in last_messages
        if message.get("role") == "assistant"
        for call in message.get("tool_calls", [])
    }
    result_ids = {
        message["tool_call_id"]
        for message in last_messages
        if message.get("role") == "tool"
    }
    assert result_ids == declared_ids


def test_invalid_model_event_is_reported_as_backend_failure():
    class InvalidBackend:
        async def stream(self, messages, *, static_prompt, dynamic_prompt, tools):
            yield "not a ModelEvent"

    events = asyncio.run(collect(AgentRuntime(InvalidBackend())))
    assert events[-1].data["status"] == "FAILED"
    assert any(e.kind == "error" for e in events)


def test_duplicate_tool_call_ids_fail_before_corrupting_tool_transcript():
    called = []
    registry = ToolRegistry()
    registry.register(ToolSpec("lookup", lambda args: called.append(args), is_read_only=True))
    backend = FakeBackend([[
        ModelEvent("tool_call", tool_call=ToolCall("same", "lookup", {})),
        ModelEvent("tool_call", tool_call=ToolCall("same", "lookup", {})),
    ]])
    events = asyncio.run(collect(AgentRuntime(backend, registry)))
    assert events[-1].data["status"] == "FAILED"
    assert any("duplicate tool call IDs" in e.data.get("error", "") for e in events)
    assert called == []



def test_backend_stream_is_closed_after_complete_event():
    class ClosingBackend:
        def __init__(self):
            self.closed = False
        async def stream(self, messages, *, static_prompt, dynamic_prompt, tools):
            try:
                yield ModelEvent("complete")
                yield ModelEvent("text", text="must not be consumed")
            finally:
                self.closed = True

    backend = ClosingBackend()
    events = asyncio.run(collect(AgentRuntime(backend)))
    assert backend.closed is True
    assert not any(e.kind == "text" for e in events)


def test_empty_context_compaction_is_rejected():
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("first", "missing", {}))],
        [ModelEvent("complete")],
    ])
    runtime = AgentRuntime(backend, compact_after_messages=2, compactor=lambda messages: [])
    events = asyncio.run(collect(runtime))
    assert events[-1].data["status"] == "FAILED"
    assert any(e.kind == "error" for e in events)



def test_tool_input_schema_is_exposed_to_backend():
    schema = {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    }
    registry = ToolRegistry()
    registry.register(ToolSpec("lookup", lambda args: "ok", is_read_only=True, input_schema=schema))
    backend = FakeBackend([[ModelEvent("complete")]])
    asyncio.run(collect(AgentRuntime(backend, registry)))
    assert backend.calls[0][3][0]["input_schema"] == schema


def test_invalid_tool_input_schema_type_is_rejected():
    with pytest.raises(TypeError, match="input_schema"):
        ToolSpec("lookup", lambda args: "ok", input_schema=["not", "a", "mapping"])



def test_async_tool_timeout_is_returned_without_crashing_session():
    async def slow_lookup(args):
        await asyncio.sleep(0.05)
        return "late"

    registry = ToolRegistry()
    registry.register(ToolSpec("lookup", slow_lookup, is_read_only=True))
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("a", "lookup", {}))],
        [ModelEvent("text", text="continued"), ModelEvent("complete")],
    ])
    events = asyncio.run(collect(AgentRuntime(
        backend, registry, tool_timeout_seconds=0.005
    )))
    result = next(e for e in events if e.kind == "tool_result")
    assert result.data["status"] == "TIMEOUT"
    assert events[-1].data["text"] == "continued"


def test_model_idle_timeout_fails_and_closes_backend_stream():
    class SlowBackend:
        def __init__(self):
            self.closed = False
        async def stream(self, messages, *, static_prompt, dynamic_prompt, tools):
            try:
                await asyncio.sleep(0.05)
                yield ModelEvent("complete")
            finally:
                self.closed = True

    backend = SlowBackend()
    events = asyncio.run(collect(AgentRuntime(
        backend, model_idle_timeout_seconds=0.005, max_backend_retries=0
    )))
    assert backend.closed is True
    assert events[-1].data["status"] == "FAILED"


def test_tool_schema_is_copied_and_must_be_json_compatible():
    schema = {"type": "object", "properties": {"q": {"type": "string"}}}
    tool = ToolSpec("lookup", lambda args: "ok", is_read_only=True, input_schema=schema)
    schema["properties"]["q"]["type"] = "integer"
    assert tool.input_schema["properties"]["q"]["type"] == "string"
    with pytest.raises(TypeError):
        tool.input_schema["properties"]["q"]["type"] = "integer"
    with pytest.raises(ValueError, match="JSON-compatible"):
        ToolSpec("bad", lambda args: "ok", is_read_only=True, input_schema={"bad": object()})



def test_tool_call_arguments_are_copied_and_json_validated():
    arguments = {"query": ["one", "two"]}
    call = ToolCall("call-1", "lookup", arguments)
    arguments["query"].append("mutated")
    assert call.arguments == {"query": ["one", "two"]}
    with pytest.raises(ValueError, match="JSON-compatible"):
        ToolCall("call-2", "lookup", {"bad": object()})
    with pytest.raises(ValueError, match="keys must be strings"):
        ToolCall("call-3", "lookup", {1: "not a JSON object key"})
    cyclic = {}
    cyclic["self"] = cyclic
    with pytest.raises(ValueError, match="JSON-compatible"):
        ToolCall("call-4", "lookup", cyclic)



def test_unclassified_tool_is_denied_by_default():
    called = []
    async def maybe_mutating(args):
        called.append(args)
        return "ran"

    registry = ToolRegistry()
    registry.register(ToolSpec("unclassified", maybe_mutating))
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("c1", "unclassified", {}))],
        [ModelEvent("complete")],
    ])
    events = asyncio.run(collect(AgentRuntime(backend, registry)))
    result = next(event for event in events if event.kind == "tool_result")
    assert result.data["status"] == "DENIED"
    assert called == []



def test_model_response_size_is_bounded_per_turn():
    backend = FakeBackend([[
        ModelEvent("text", text="ab"),
        ModelEvent("text", text="cd"),
    ]])
    events = asyncio.run(collect(AgentRuntime(
        backend, max_response_chars_per_turn=3
    )))
    assert [e.data["text"] for e in events if e.kind == "text"] == ["ab"]
    assert events[-1].data["status"] == "FAILED"
    assert any("character limit" in e.data.get("error", "") for e in events)


def test_tool_call_count_is_bounded_before_any_tool_runs():
    called = []
    registry = ToolRegistry()
    registry.register(ToolSpec(
        "lookup", lambda args: called.append(args), is_read_only=True
    ))
    backend = FakeBackend([[
        ModelEvent("tool_call", tool_call=ToolCall("one", "lookup", {})),
        ModelEvent("tool_call", tool_call=ToolCall("two", "lookup", {})),
    ]])
    events = asyncio.run(collect(AgentRuntime(
        backend, registry, max_tool_calls_per_turn=1
    )))
    assert events[-1].data["status"] == "FAILED"
    assert called == []


def test_tool_output_is_truncated_before_entering_context():
    registry = ToolRegistry()
    registry.register(ToolSpec(
        "lookup", lambda args: "abcdefghij", is_read_only=True
    ))
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("one", "lookup", {}))],
        [ModelEvent("complete")],
    ])
    events = asyncio.run(collect(AgentRuntime(
        backend, registry, max_tool_output_chars=5
    )))
    result = next(event for event in events if event.kind == "tool_result")
    assert result.data["output"] == "abcde\n...[truncated]"


def test_invalid_payload_limits_are_rejected():
    backend = FakeBackend([])
    with pytest.raises(ValueError, match="max_tool_calls_per_turn"):
        AgentRuntime(backend, max_tool_calls_per_turn=0)



def test_async_input_validator_is_awaited_before_tool_execution():
    called = []
    async def validate(args):
        await asyncio.sleep(0)
        if "query" not in args:
            raise ValueError("query is required")

    registry = ToolRegistry()
    registry.register(ToolSpec(
        "lookup",
        lambda args: called.append(args) or "ok",
        is_read_only=True,
        validate_input=validate,
    ))
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("one", "lookup", {"query": "x"}))],
        [ModelEvent("complete")],
    ])
    events = asyncio.run(collect(AgentRuntime(backend, registry)))
    result = next(event for event in events if event.kind == "tool_result")
    assert result.data["status"] == "OK"
    assert called == [{"query": "x"}]


def test_async_input_validator_failure_prevents_tool_execution():
    called = []
    async def validate(args):
        raise ValueError("invalid input")

    registry = ToolRegistry()
    registry.register(ToolSpec(
        "lookup",
        lambda args: called.append(args),
        is_read_only=True,
        validate_input=validate,
    ))
    backend = FakeBackend([
        [ModelEvent("tool_call", tool_call=ToolCall("one", "lookup", {}))],
        [ModelEvent("complete")],
    ])
    events = asyncio.run(collect(AgentRuntime(backend, registry)))
    result = next(event for event in events if event.kind == "tool_result")
    assert result.data["status"] == "ERROR"
    assert called == []
