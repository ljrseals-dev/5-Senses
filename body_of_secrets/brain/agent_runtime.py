"""Streaming-first, permission-aware agent runtime for BODY OF SECRETS.

This is an orchestration layer, not a replacement for Brain, Archive, Memory,
or Expert. Backends and tools are injected; importing this module performs no
network access and executes no commands.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import math
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, AsyncIterator, Awaitable, Callable, Mapping, Protocol, Sequence


JsonObject = Mapping[str, Any]
ToolHandler = Callable[[JsonObject], Any | Awaitable[Any]]


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _validate_json_keys(value: Any, active: set[int] | None = None) -> None:
    if active is None:
        active = set()
    if not isinstance(value, (Mapping, list, tuple)):
        return
    identity = id(value)
    if identity in active:
        raise ValueError("cyclic values are not valid JSON")
    active.add(identity)
    try:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                _validate_json_keys(item, active)
        else:
            for item in value:
                _validate_json_keys(item, active)
    finally:
        active.remove(identity)


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
    is_read_only: bool = False
    is_concurrency_safe: bool = False
    is_destructive: bool = False
    validate_input: Callable[[JsonObject], Any | Awaitable[Any]] | None = None
    input_schema: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or not self.name
            or not self.name.replace("_", "").replace("-", "").isalnum()
        ):
            raise ValueError("tool name must contain only letters, digits, '_' or '-'")
        if not callable(self.handler):
            raise TypeError("tool handler must be callable")
        if not isinstance(self.description, str):
            raise TypeError("tool description must be a string")
        if not isinstance(self.input_schema, Mapping):
            raise TypeError("input_schema must be a mapping")
        try:
            _validate_json_keys(self.input_schema)
            schema_json = json.dumps(dict(self.input_schema), allow_nan=False)
        except (TypeError, ValueError, RecursionError) as exc:
            raise ValueError("input_schema must contain only JSON-compatible values") from exc
        object.__setattr__(self, "input_schema", _freeze_json(json.loads(schema_json)))
        if not all(isinstance(flag, bool) for flag in (
            self.is_read_only, self.is_concurrency_safe, self.is_destructive
        )):
            raise TypeError("tool capability flags must be booleans")
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
        if not isinstance(tool, ToolSpec):
            raise TypeError("only ToolSpec instances can be registered")
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
                "input_schema": _thaw_json(item.input_schema),
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

    def __post_init__(self) -> None:
        if not all(isinstance(flag, bool) for flag in (
            self.allow_read_only, self.allow_mutating, self.allow_destructive
        )):
            raise TypeError("permission policy values must be booleans")

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
        if not isinstance(self.call_id, str) or not self.call_id.strip():
            raise ValueError("tool call ID must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("tool name must be a non-empty string")
        if not isinstance(self.arguments, Mapping):
            raise TypeError("tool call arguments must be a mapping")
        try:
            _validate_json_keys(self.arguments)
            arguments_json = json.dumps(dict(self.arguments), allow_nan=False)
        except (TypeError, ValueError, RecursionError) as exc:
            raise ValueError(
                "tool call arguments must contain only JSON-compatible values"
            ) from exc
        object.__setattr__(self, "arguments", json.loads(arguments_json))


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
    messages: list[dict[str, Any]] = field(default_factory=list)
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
        max_response_chars_per_turn: int = 200_000,
        max_tool_calls_per_turn: int = 32,
        max_tool_output_chars: int = 20_000,
        compactor: ContextCompactor | None = None,
    ) -> None:
        if isinstance(max_turns, bool) or not isinstance(max_turns, int) or max_turns < 1:
            raise ValueError("max_turns must be a positive integer")
        if (
            isinstance(max_backend_retries, bool)
            or not isinstance(max_backend_retries, int)
            or max_backend_retries < 0
        ):
            raise ValueError("max_backend_retries must be a non-negative integer")
        if (
            isinstance(compact_after_messages, bool)
            or not isinstance(compact_after_messages, int)
            or compact_after_messages < 2
        ):
            raise ValueError("compact_after_messages must be an integer of at least 2")
        if (
            isinstance(keep_recent_messages, bool)
            or not isinstance(keep_recent_messages, int)
            or keep_recent_messages < 1
        ):
            raise ValueError("keep_recent_messages must be a positive integer")
        for name, value in (
            ("max_response_chars_per_turn", max_response_chars_per_turn),
            ("max_tool_calls_per_turn", max_tool_calls_per_turn),
            ("max_tool_output_chars", max_tool_output_chars),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if not all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0
            for value in (tool_timeout_seconds, model_idle_timeout_seconds)
        ):
            raise ValueError("timeouts must be finite positive numbers")
        if not callable(getattr(backend, "stream", None)):
            raise TypeError("backend must provide a callable stream method")
        if tools is not None and not isinstance(tools, ToolRegistry):
            raise TypeError("tools must be a ToolRegistry")
        if permissions is not None and not isinstance(permissions, PermissionPolicy):
            raise TypeError("permissions must be a PermissionPolicy")
        if compactor is not None and not callable(compactor):
            raise TypeError("compactor must be callable")
        self.backend = backend
        self.tools = tools or ToolRegistry()
        self.permissions = permissions or PermissionPolicy()
        self.max_turns = max_turns
        self.tool_timeout_seconds = tool_timeout_seconds
        self.model_idle_timeout_seconds = model_idle_timeout_seconds
        self.max_backend_retries = max_backend_retries
        self.compact_after_messages = compact_after_messages
        self.keep_recent_messages = keep_recent_messages
        self.max_response_chars_per_turn = max_response_chars_per_turn
        self.max_tool_calls_per_turn = max_tool_calls_per_turn
        self.max_tool_output_chars = max_tool_output_chars
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
            response_chars = 0
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
                        state.messages = self._fallback_compact(state.messages)
                        yield AgentEvent("context_trimmed", state.turn, {
                            "message_count": len(state.messages),
                            "reason": (
                                "no compactor configured; retained initial user request, "
                                "recent messages, and complete tool-call groups"
                            ),
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
                                response_chars += len(item.text)
                                if response_chars > self.max_response_chars_per_turn:
                                    raise ValueError(
                                        "model response exceeded per-turn character limit"
                                    )
                                text_parts.append(item.text)
                                yield AgentEvent("text", state.turn, {"text": item.text})
                            elif item.kind == "tool_call" and item.tool_call is not None:
                                if len(calls) >= self.max_tool_calls_per_turn:
                                    raise ValueError("model exceeded per-turn tool-call limit")
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
                state.last_error = f"{type(exc).__name__}: {exc}"[:1000]
                state.status = AgentStatus.FAILED
                state.transitions.append("WAITING_FOR_MODEL->FAILED")
                yield AgentEvent("error", state.turn, {"error": state.last_error})
                yield AgentEvent("state", state.turn, {"status": state.status.value})
                return

            assistant_text = "".join(text_parts)
            call_ids = [call.call_id for call in calls]
            if len(call_ids) != len(set(call_ids)):
                state.last_error = "backend returned duplicate tool call IDs"
                state.status = AgentStatus.FAILED
                state.transitions.append("WAITING_FOR_MODEL->FAILED")
                yield AgentEvent("error", state.turn, {"error": state.last_error})
                yield AgentEvent("state", state.turn, {"status": state.status.value})
                return
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
        try:
            while True:
                try:
                    item = await asyncio.wait_for(
                        iterator.__anext__(), timeout=self.model_idle_timeout_seconds
                    )
                except StopAsyncIteration:
                    return
                if not isinstance(item, ModelEvent):
                    raise TypeError("backend must yield ModelEvent instances")
                yield item
                if item.kind == "complete":
                    return
        finally:
            close = getattr(iterator, "aclose", None)
            if close is not None:
                close_result = close()
                if inspect.isawaitable(close_result):
                    await close_result

    def _fallback_compact(
        self, messages: Sequence[Mapping[str, Any]]
    ) -> list[dict[str, Any]]:
        start = max(0, len(messages) - self.keep_recent_messages)
        if start < len(messages) and messages[start].get("role") == "tool":
            first_tool_id = messages[start].get("tool_call_id")
            for index in range(start - 1, -1, -1):
                message = messages[index]
                if message.get("role") != "assistant":
                    continue
                declared_ids = {
                    item.get("id")
                    for item in message.get("tool_calls", [])
                    if isinstance(item, Mapping)
                }
                if first_tool_id in declared_ids:
                    start = index
                    break

        recent = [dict(message) for message in messages[start:]]
        declared_ids = {
            item.get("id")
            for message in recent
            if message.get("role") == "assistant"
            for item in message.get("tool_calls", [])
            if isinstance(item, Mapping)
        }
        recent = [
            message for message in recent
            if message.get("role") != "tool"
            or message.get("tool_call_id") in declared_ids
        ]
        first_user = next(
            (message for message in messages if message.get("role") == "user"),
            None,
        )
        if first_user is not None and not any(
            message.get("role") == "user" and message.get("content") == first_user.get("content")
            for message in recent
        ):
            recent.insert(0, dict(first_user))
        return recent

    def _should_compact(self, messages: Sequence[Mapping[str, Any]]) -> bool:
        return len(messages) >= self.compact_after_messages

    @staticmethod
    def _validate_compacted_messages(messages: Any) -> None:
        if not isinstance(messages, list) or not messages:
            raise TypeError("context compactor must return a non-empty list of messages")
        pending_calls: set[str] = set()
        seen_calls: set[str] = set()
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                raise TypeError(f"compacted message {index} must be a dictionary")
            if not isinstance(message.get("role"), str):
                raise TypeError(f"compacted message {index} requires a string role")
            if not isinstance(message.get("content", ""), str):
                raise TypeError(f"compacted message {index} content must be a string")
            try:
                _validate_json_keys(message)
                json.dumps(message, allow_nan=False)
            except (TypeError, ValueError, RecursionError) as exc:
                raise ValueError(
                    f"compacted message {index} is not JSON-compatible"
                ) from exc

            if message["role"] == "assistant":
                calls = message.get("tool_calls", [])
                if not isinstance(calls, list):
                    raise TypeError("assistant tool_calls must be a list")
                for call in calls:
                    if not isinstance(call, Mapping):
                        raise TypeError("assistant tool call must be an object")
                    call_id = call.get("id")
                    function = call.get("function")
                    if not isinstance(call_id, str) or not call_id.strip():
                        raise ValueError("compacted tool call ID must be non-empty")
                    if call_id in seen_calls:
                        raise ValueError("compacted transcript contains duplicate tool call IDs")
                    if not isinstance(function, Mapping) or not isinstance(
                        function.get("name"), str
                    ):
                        raise ValueError("compacted tool call requires a named function")
                    if not isinstance(function.get("arguments"), Mapping):
                        raise ValueError("compacted tool call arguments must be an object")
                    seen_calls.add(call_id)
                    pending_calls.add(call_id)
            elif message["role"] == "tool":
                call_id = message.get("tool_call_id")
                if not isinstance(call_id, str) or call_id not in pending_calls:
                    raise ValueError("compacted transcript contains an orphan tool result")
                pending_calls.remove(call_id)
        if pending_calls:
            raise ValueError("compacted transcript contains unanswered tool calls")

    async def _invoke(self, tool: ToolSpec, arguments: Mapping[str, Any]) -> ToolResult:
        try:
            if tool.validate_input is not None:
                validator = tool.validate_input
                if inspect.iscoroutinefunction(validator) or inspect.iscoroutinefunction(
                    getattr(validator, "__call__", None)
                ):
                    await asyncio.wait_for(
                        validator(arguments), timeout=self.tool_timeout_seconds
                    )
                else:
                    validation_result = await asyncio.wait_for(
                        asyncio.to_thread(validator, arguments),
                        timeout=self.tool_timeout_seconds,
                    )
                    if inspect.isawaitable(validation_result):
                        await asyncio.wait_for(
                            validation_result, timeout=self.tool_timeout_seconds
                        )
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
            if len(output) > self.max_tool_output_chars:
                output = output[:self.max_tool_output_chars] + "\n...[truncated]"
            return ToolResult("", tool.name, output, "OK")
        except asyncio.TimeoutError:
            return ToolResult("", tool.name, "tool execution timed out", "TIMEOUT")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"[:1000]
            return ToolResult("", tool.name, error, "ERROR")

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
