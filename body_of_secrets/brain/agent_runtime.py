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
        if not isinstance(self.name, str) or not self.name or not self.name.replace("_", "").replace("-", "").isalnum():
            raise ValueError("tool name must contain only letters, digits, '_' or '-'")
        if not callable(self.handler):
            raise TypeError("tool handler must be callable")
        if not isinstance(self.description, str):
            raise TypeError("tool description must be a string")
        if self.is_destructive and self.is_read_only:
            raise ValueError("a destructive tool cannot be declared read-only")
        if self.is_concurrency_safe and not self.is_read_only:
            raise ValueError("only read-only tools may be marked concurrency-safe")
        if self.validate_input is not None and not callable(self.validate_input):
            raise TypeError("validate_input must be callable")
        if not self.is_read_only and not (
            inspect.iscoroutinefunction(self.handler)
            or inspect.iscoroutinefunction(getattr(self.handler, "__call__", None))
        ):
            raise TypeError(
                "mutating tools must use async handlers; synchronous handlers cannot "
                "be safely cancelled after a timeout"
            )


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

    def __post_init__(self) -> None:
        if not isinstance(self.call_id, str) or not isinstance(self.name, str):
            raise TypeError("tool call ID and name must be strings")


@dataclass(frozen=True)
class ModelEvent:
    """Backend event: 'text', 'tool_call', or 'complete'."""

    kind: str
    text: str = ""
    tool_call: ToolCall | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"text", "tool_call", "complete"}:
            raise ValueError(f"unsupported model event kind: {self.kind}")
        if self.kind == "text" and not isinstance(self.text, str):
            raise TypeError("text event content must be a string")
        if self.kind == "tool_call" and not isinstance(self.tool_call, ToolCall):
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
        messages: Sequence[Mapping[str, Any]],
        *,
        static_prompt: str,
        dynamic_prompt: str,
        tools: Sequence[Mapping[str, Any]],
    ) -> AsyncIterator[ModelEvent]: ...


ContextCompactor = Callable[[Sequence[Mapping[str, Any]]], list[dict[str, Any]]]


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
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if not isinstance(session_id, str) or not session_id.strip():
            raise ValueError("session_id must be a non-empty string")
        if not isinstance(static_prompt, str) or not isinstance(dynamic_prompt, str):
            raise TypeError("prompt regions must be strings")
        state = AgentState(session_id=session_id)
        state.messages.append({"role": "user", "content": prompt})
        state.status = AgentStatus.RUNNING
        state.transitions.append("READY->RUNNING")
        yield AgentEvent("state", 0, {"status": state.status.value})

        while state.turn < self.max_turns:
            state.turn += 1
            state.status = AgentStatus.WAITING_FOR_MODEL
            state.transitions.append("RUNNING->WAITING_FOR_MODEL")
            text_parts: list[str] = []
            calls: list[ToolCall] = []
            try:
                if self._should_compact(state.messages):
                    if self.compactor is not None:
                        compacted = self.compactor(list(state.messages))
                        self._validate_compacted_messages(compacted)
                        state.messages = compacted
                        yield AgentEvent("context_compacted", state.turn, {
                            "message_count": len(state.messages)
                        })
                    else:
                        first_user = next(
                            (message for message in state.messages if message.get("role") == "user"),
                            None,
                        )
                        recent = state.messages[-self.keep_recent_messages:]
                        if first_user is not None and first_user not in recent:
                            recent = [first_user, *recent[-(self.keep_recent_messages - 1):]]
                        state.messages = recent
                        yield AgentEvent("context_trimmed", state.turn, {
                            "message_count": len(state.messages),
                            "reason": "no compactor configured; retained initial user request and recent messages",
                        })

                for attempt in range(self.max_backend_retries + 1):
                    received_event = False
                    try:
                        async for item in self._stream_turn(
                            state.messages,
                            static_prompt=static_prompt,
                            dynamic_prompt=dynamic_prompt,
                        ):
                            received_event = True
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
                                break
                        break
                    except (TimeoutError, OSError, ConnectionError) as exc:
                        # Retrying after any emitted event would duplicate user-visible
                        # text or tool calls. Only retry failures before the first event.
                        if attempt >= self.max_backend_retries or received_event:
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
            if assistant_text or calls:
                assistant_message: dict[str, Any] = {
                    "role": "assistant",
                    "content": assistant_text,
                }
                if calls:
                    assistant_message["tool_calls"] = [
                        {
                            "id": call.call_id,
                            "type": "function",
                            "function": {
                                "name": call.name,
                                "arguments": dict(call.arguments)
                                if isinstance(call.arguments, Mapping)
                                else call.arguments,
                            },
                        }
                        for call in calls
                    ]
                state.messages.append(assistant_message)
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
                    "tool_call_id": result.call_id,
                    "name": result.name,
                    "content": f"[{result.status}] {result.output}",
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
        messages: Sequence[Mapping[str, Any]],
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

    def _should_compact(self, messages: Sequence[Mapping[str, Any]]) -> bool:
        return len(messages) >= self.compact_after_messages

    @staticmethod
    def _validate_compacted_messages(messages: Any) -> None:
        if not isinstance(messages, list):
            raise TypeError("context compactor must return a list of messages")
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                raise TypeError(f"compacted message {index} must be a dictionary")
            if not isinstance(message.get("role"), str):
                raise TypeError(f"compacted message {index} requires a string role")
            if not isinstance(message.get("content", ""), str):
                raise TypeError(f"compacted message {index} content must be a string")

    async def _invoke(self, tool: ToolSpec, arguments: Mapping[str, Any]) -> ToolResult:
        try:
            if tool.validate_input is not None:
                tool.validate_input(arguments)
            if inspect.iscoroutinefunction(tool.handler) or inspect.iscoroutinefunction(
                getattr(tool.handler, "__call__", None)
            ):
                value = tool.handler(arguments)
                value = await asyncio.wait_for(value, timeout=self.tool_timeout_seconds)
            else:
                # Synchronous read-only handlers run off-loop so they cannot stall
                # model streaming or other sessions. A worker thread cannot be
                # forcibly stopped, so only read-only sync tools are accepted.
                value = await asyncio.wait_for(
                    asyncio.to_thread(tool.handler, arguments),
                    timeout=self.tool_timeout_seconds,
                )
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
