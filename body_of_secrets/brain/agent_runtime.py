"""Streaming-first, permission-aware agent runtime for BODY OF SECRETS.

This is an orchestration layer, not a replacement for Brain, Archive, Memory,
or Expert. Backends and tools are injected; importing this module performs no
network access and executes no commands.
"""
from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Awaitable, Callable, Mapping, Protocol, Sequence


JsonObject = Mapping[str, Any]
ToolHandler = Callable[[JsonObject], Any | Awaitable[Any]]


class AgentStatus(str, Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_FOR_MODEL = "WAITING_FOR_MODEL"
    EXECUTING_TOOLS = "EXECUTING_TOOLS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    LIMIT_REACHED = "LIMIT_REACHED"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    handler: ToolHandler
    description: str = ""
    is_read_only: bool = True
    is_concurrency_safe: bool = False
    is_destructive: bool = False
    validate_input: Callable[[JsonObject], None] | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.replace("_", "").replace("-", "").isalnum():
            raise ValueError("tool name must contain only letters, digits, '_' or '-'")
        if self.is_destructive and self.is_read_only:
            raise ValueError("a destructive tool cannot be declared read-only")


class ToolRegistry:
    """Explicit allow-list of callable capabilities."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"unknown tool: {name}") from exc

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "name": item.name,
                "description": item.description,
                "is_read_only": item.is_read_only,
                "is_concurrency_safe": item.is_concurrency_safe,
                "is_destructive": item.is_destructive,
            }
            for item in sorted(self._tools.values(), key=lambda value: value.name)
        ]


@dataclass(frozen=True)
class PermissionPolicy:
    allow_read_only: bool = True
    allow_mutating: bool = False
    allow_destructive: bool = False

    def permits(self, tool: ToolSpec) -> bool:
        if tool.is_destructive:
            return self.allow_mutating and self.allow_destructive
        if tool.is_read_only:
            return self.allow_read_only
        return self.allow_mutating


@dataclass(frozen=True)
class ToolCall:
    call_id: str
    name: str
    arguments: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelEvent:
    """Backend event: 'text', 'tool_call', or 'complete'."""

    kind: str
    text: str = ""
    tool_call: ToolCall | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"text", "tool_call", "complete"}:
            raise ValueError(f"unsupported model event kind: {self.kind}")
        if self.kind == "tool_call" and self.tool_call is None:
            raise ValueError("tool_call event requires a ToolCall")


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    name: str
    output: str
    status: str


@dataclass
class AgentState:
    session_id: str
    status: AgentStatus = AgentStatus.READY
    messages: list[dict[str, str]] = field(default_factory=list)
    turn: int = 0
    transitions: list[str] = field(default_factory=list)
    final_text: str = ""
    last_error: str | None = None


@dataclass(frozen=True)
class AgentEvent:
    kind: str
    turn: int
    data: Mapping[str, Any] = field(default_factory=dict)


class StreamingBackend(Protocol):
    def stream(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        static_prompt: str,
        dynamic_prompt: str,
        tools: Sequence[Mapping[str, Any]],
    ) -> AsyncIterator[ModelEvent]: ...


ContextCompactor = Callable[[Sequence[Mapping[str, str]]], list[dict[str, str]]]


class AgentRuntime:
    """Bounded state-machine loop with explicit permissions and recovery."""

    def __init__(
        self,
        backend: StreamingBackend,
        tools: ToolRegistry | None = None,
        *,
        permissions: PermissionPolicy | None = None,
        max_turns: int = 8,
        tool_timeout_seconds: float = 15.0,
        model_idle_timeout_seconds: float = 60.0,
        max_backend_retries: int = 1,
        compact_after_messages: int = 40,
        keep_recent_messages: int = 12,
        compactor: ContextCompactor | None = None,
    ) -> None:
        if max_turns < 1 or tool_timeout_seconds <= 0 or model_idle_timeout_seconds <= 0:
            raise ValueError("turn and timeout limits must be positive")
        if max_backend_retries < 0 or compact_after_messages < 2 or keep_recent_messages < 1:
            raise ValueError("invalid retry or context limits")
        self.backend = backend
        self.tools = tools or ToolRegistry()
        self.permissions = permissions or PermissionPolicy()
        self.max_turns = max_turns
        self.tool_timeout_seconds = tool_timeout_seconds
        self.model_idle_timeout_seconds = model_idle_timeout_seconds
        self.max_backend_retries = max_backend_retries
        self.compact_after_messages = compact_after_messages
        self.keep_recent_messages = keep_recent_messages
        self.compactor = compactor

    async def run(
        self,
        prompt: str,
        *,
        session_id: str = "default",
        static_prompt: str = "",
        dynamic_prompt: str = "",
    ) -> AsyncIterator[AgentEvent]:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        state = AgentState(session_id=session_id)
        state.messages.append({"role": "user", "content": prompt})
        state.status = AgentStatus.RUNNING
        state.transitions.append("READY->RUNNING")
        yield AgentEvent("state", 0, {"status": state.status.value})

        while state.turn < self.max_turns:
            state.turn += 1
            state.status = AgentStatus.WAITING_FOR_MODEL
            state.transitions.append("RUNNING->WAITING_FOR_MODEL")
            if self._should_compact(state.messages):
                if self.compactor is not None:
                    state.messages = self.compactor(state.messages)
                    yield AgentEvent("context_compacted", state.turn, {
                        "message_count": len(state.messages)
                    })
                else:
                    state.messages = state.messages[-self.keep_recent_messages:]
                    yield AgentEvent("context_trimmed", state.turn, {
                        "message_count": len(state.messages),
                        "reason": "no compactor configured; retained recent messages only",
                    })

            text_parts: list[str] = []
            calls: list[ToolCall] = []
            completed = False
            try:
                for attempt in range(self.max_backend_retries + 1):
                    try:
                        async for item in self._stream_turn(
                            state.messages,
                            static_prompt=static_prompt,
                            dynamic_prompt=dynamic_prompt,
                        ):
                            if item.kind == "text":
                                text_parts.append(item.text)
                                yield AgentEvent("text", state.turn, {"text": item.text})
                            elif item.kind == "tool_call" and item.tool_call is not None:
                                calls.append(item.tool_call)
                                yield AgentEvent("tool_call_received", state.turn, {
                                    "call_id": item.tool_call.call_id,
                                    "name": item.tool_call.name,
                                })
                            elif item.kind == "complete":
                                completed = True
                        break
                    except (TimeoutError, OSError, ConnectionError) as exc:
                        if attempt >= self.max_backend_retries:
                            raise
                        yield AgentEvent("backend_retry", state.turn, {
                            "attempt": attempt + 1,
                            "error": type(exc).__name__,
                        })
            except Exception as exc:
                state.last_error = f"{type(exc).__name__}: {exc}"
                state.status = AgentStatus.FAILED
                state.transitions.append("WAITING_FOR_MODEL->FAILED")
                yield AgentEvent("error", state.turn, {"error": state.last_error})
                yield AgentEvent("state", state.turn, {"status": state.status.value})
                return

            assistant_text = "".join(text_parts)
            if assistant_text:
                state.messages.append({"role": "assistant", "content": assistant_text})
            if not calls:
                state.final_text = assistant_text
                state.status = AgentStatus.COMPLETED
                state.transitions.append("WAITING_FOR_MODEL->COMPLETED")
                yield AgentEvent("state", state.turn, {"status": state.status.value})
                yield AgentEvent("completed", state.turn, {"text": state.final_text})
                return

            state.status = AgentStatus.EXECUTING_TOOLS
            state.transitions.append("WAITING_FOR_MODEL->EXECUTING_TOOLS")
            results = await self._execute_calls(calls)
            for result in results:
                state.messages.append({
                    "role": "tool",
                    "content": f"{result.name} [{result.status}]: {result.output}",
                })
                yield AgentEvent("tool_result", state.turn, {
                    "call_id": result.call_id,
                    "name": result.name,
                    "status": result.status,
                    "output": result.output,
                })
            state.status = AgentStatus.RUNNING
            state.transitions.append("EXECUTING_TOOLS->RUNNING")

        state.status = AgentStatus.LIMIT_REACHED
        state.transitions.append("RUNNING->LIMIT_REACHED")
        yield AgentEvent("state", state.turn, {"status": state.status.value})
        yield AgentEvent("limit_reached", state.turn, {"max_turns": self.max_turns})

    async def _stream_turn(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        static_prompt: str,
        dynamic_prompt: str,
    ) -> AsyncIterator[ModelEvent]:
        stream = self.backend.stream(
            messages,
            static_prompt=static_prompt,
            dynamic_prompt=dynamic_prompt,
            tools=self.tools.describe(),
        )
        iterator = stream.__aiter__()
        while True:
            try:
                item = await asyncio.wait_for(
                    iterator.__anext__(), timeout=self.model_idle_timeout_seconds
                )
            except StopAsyncIteration:
                return
            yield item

    def _should_compact(self, messages: Sequence[Mapping[str, str]]) -> bool:
        return len(messages) >= self.compact_after_messages

    async def _invoke(self, tool: ToolSpec, arguments: Mapping[str, Any]) -> ToolResult:
        try:
            if tool.validate_input is not None:
                tool.validate_input(arguments)
            value = tool.handler(arguments)
            if inspect.isawaitable(value):
                value = await asyncio.wait_for(value, timeout=self.tool_timeout_seconds)
            output = str(value)
            return ToolResult("", tool.name, output, "OK")
        except asyncio.TimeoutError:
            return ToolResult("", tool.name, "tool execution timed out", "TIMEOUT")
        except Exception as exc:
            return ToolResult("", tool.name, f"{type(exc).__name__}: {exc}", "ERROR")

    async def _execute_calls(self, calls: Sequence[ToolCall]) -> list[ToolResult]:
        prepared: list[tuple[int, ToolCall, ToolSpec]] = []
        ordered: dict[int, ToolResult] = {}
        seen_ids: set[str] = set()
        for index, call in enumerate(calls):
            if not call.call_id or call.call_id in seen_ids:
                ordered[index] = ToolResult(
                    call.call_id, call.name, "missing or duplicate call ID", "REJECTED"
                )
                continue
            seen_ids.add(call.call_id)
            try:
                tool = self.tools.get(call.name)
            except KeyError as exc:
                ordered[index] = ToolResult(call.call_id, call.name, str(exc), "REJECTED")
                continue
            if not self.permissions.permits(tool):
                ordered[index] = ToolResult(
                    call.call_id, call.name, "permission denied", "DENIED"
                )
                continue
            if not isinstance(call.arguments, Mapping):
                ordered[index] = ToolResult(
                    call.call_id, call.name, "arguments must be an object", "REJECTED"
                )
                continue
            prepared.append((index, call, tool))

        if prepared and all(
            tool.is_read_only and tool.is_concurrency_safe for _, _, tool in prepared
        ):
            invoked = await asyncio.gather(
                *(self._invoke(tool, call.arguments) for _, call, tool in prepared)
            )
            for (index, call, _), result in zip(prepared, invoked):
                ordered[index] = ToolResult(
                    call.call_id, result.name, result.output, result.status
                )
        else:
            for index, call, tool in prepared:
                result = await self._invoke(tool, call.arguments)
                ordered[index] = ToolResult(
                    call.call_id, result.name, result.output, result.status
                )
        return [ordered[index] for index in range(len(calls))]
