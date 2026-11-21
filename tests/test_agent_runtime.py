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
    registry.register(ToolSpec("write_file", lambda args: called.append(args), is_read_only=False))
    registry.register(ToolSpec("delete_file", lambda args: called.append(args),
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
    registry.register(ToolSpec("write_file", lambda args: called.append(args),
                               is_read_only=False))
    registry.register(ToolSpec("delete_file", lambda args: called.append(args),
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
    registry.register(ToolSpec("lookup", broken))
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
    registry.register(ToolSpec("lookup", lambda args: "ok"))
    with pytest.raises(ValueError, match="already registered"):
        registry.register(ToolSpec("lookup", lambda args: "again"))
