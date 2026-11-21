# BODY OF SECRETS Agent Runtime

## Status

This is an independently implemented orchestration layer inspired by the
architecture diagrams in the supplied `claude-code-architecture` archive.
It does not contain or reproduce Claude Code source code.

## Boundaries

- Existing Brain, Archive, Memory, Expert, and classical language/neural
  components remain separate domain systems.
- The runtime accepts an injected streaming backend; it does not select a
  vendor, make network calls, or require an LLM.
- Tools are explicit allow-listed capabilities. There is no shell tool,
  arbitrary Python execution, or implicit filesystem access.
- Read-only tools are permitted by default. Mutating tools require an explicit
  `PermissionPolicy(allow_mutating=True)`; destructive tools additionally
  require `allow_destructive=True`.
- Tool input validation is performed by the registered tool's validator.
- Mutating and destructive handlers must be asynchronous. Synchronous
  handlers are accepted only for tools declared read-only.
- Synchronous read-only handlers run in worker threads so they do not block
  the event loop. A timed-out worker thread cannot be forcibly stopped; the
  read-only declaration is therefore a trust boundary, not a sandbox.
- Only read-only tools explicitly marked concurrency-safe may run concurrently.
- Model streaming has an idle timeout and bounded retry count. Backend retries
  occur only before the first event; after partial output, the runtime fails
  rather than replaying duplicate text or tool calls.
- Tool execution has a timeout for asynchronous handlers and for waiting on
  synchronous read-only handlers. Async cancellation is cooperative; handlers
  must not suppress cancellation if they need timeout guarantees.
- Tool-call requests and tool results are preserved as correlated structured
  messages using the call ID. Results are emitted in original request order.
- Ordinary tool errors are returned to the model as results instead of
  crashing the session.
- The state machine has a maximum turn count and records transitions.
- Static and dynamic prompt regions are separate backend arguments.

## Current integration contract

The runtime is exposed as `body_of_secrets.brain.agent_runtime.AgentRuntime`.
It is deliberately not wired into the existing synchronous `Engine.ask()`
or default CLI path in this first slice: the existing `LLMProvider.complete()`
protocol is synchronous and has no structured tool-call contract. Adapting
vendor providers or changing `ask()` would be a separate compatibility
decision. A backend can be integrated by implementing `StreamingBackend`.

## Example

```python
from body_of_secrets.brain.agent_runtime import (
    AgentRuntime, PermissionPolicy, ToolRegistry, ToolSpec
)

registry = ToolRegistry()
registry.register(ToolSpec(
    name="archive_search",
    description="Search local provenance-bearing documents",
    handler=lambda args: archive.search(args["query"]),
    is_read_only=True,
    is_concurrency_safe=True,
))

runtime = AgentRuntime(
    backend=my_streaming_backend,
    tools=registry,
    permissions=PermissionPolicy(),  # read-only only
)

async for event in runtime.run("Find documents about Hopfield energy"):
    if event.kind == "text":
        print(event.data["text"], end="", flush=True)
```

## Recovery semantics

| Condition | Behavior |
|---|---|
| Unknown tool | Reject and return a tool result |
| Permission denied | Deny without invoking handler |
| Invalid input | Return validation error |
| Tool exception | Return bounded error status; continue loop |
| Async tool timeout | Return TIMEOUT; continue loop |
| Backend timeout / connection failure | Retry up to configured bound |
| Other backend exception | Mark session FAILED |
| Turn limit | Mark LIMIT_REACHED |

Context compaction is injected via a caller-supplied function and its output
is validated before replacing the live transcript. If the message threshold is
reached without a compactor, the initial user request and the configured
number of recent messages are retained; an explicit event reports this lossy
fallback.
