# Spike: Sosein artifact updates inside Codex

Tested 2026-09-07 (America/Los_Angeles).

## Finding

The desktop-bundled Codex backend receives `notifications/resources/updated`
but only logs it in this probe. It does not automatically reread the resource
or emit a corresponding app-server event. We observed neither
`resources/subscribe` nor `subscriptions/listen`.

Do not implement Sosein subscriptions expecting this alone to notify an agent.
Codex needs a host-side path that subscribes, refreshes the resource, and makes
the change visible to the relevant task.

## Experiment

- Executable: `/Applications/ChatGPT.app/Contents/Resources/codex`, version 0.153.4.
  The separate shell CLI is 0.143.0 and was not the test subject.
- Start a separate app-server process with existing configured integrations
  disabled via subprocess-only configuration overrides. No persistent config edits.
- Start an ephemeral backend session without a model turn, then list and read a
  synthetic resource advertised with `resources.subscribe: true`.
- After returning revision 1, the fixture changes it to revision 2 and sends a
  resource-update notification. Observe for three seconds, then explicitly reread.
- No model invocation, Sosein connection, production changes, or server agent.

The update is deliberately **unsolicited diagnostic injection** because Codex
did not subscribe. It tests notification handling, not successful subscription
delivery. A production server must honor client subscription filters.

| Observation | Result |
| --- | --- |
| Client initialization protocol offer | `2025-06-18` |
| Fixture initialization response | `2025-11-25`, accepted by client |
| First read | `revision 1` |
| Resource-update receipt | Runtime logs `MCP server resource updated` |
| Subscription request | None observed |
| Automatic read after notification | None observed |
| Resource-update app-server event | None observed |
| Explicit second read | `revision 2` |

The checked-in `evidence/` contains the successful run's request trace, compact
app-server results, and runtime log. It contains only synthetic fixture data.

## Source cross-check

Public Codex HEAD inspected: `e7637306bc9246a3e42e407cb94f96b7ed345e3e`.
This is not asserted to be the exact source revision of the bundled binary.

- [`LoggingClientHandler::on_resource_updated`](https://github.com/openai/codex/blob/e7637306bc9246a3e42e407cb94f96b7ed345e3e/codex-rs/rmcp-client/src/logging_client_handler.rs#L74)
  calls `info!` only, consistent with the runtime result.
- Searching the MCP wrapper and connection manager found resource list/read
  operations, but no resource subscription or `subscriptions/listen` path.
- The generated desktop app-server schema exposes resource reads; it has no
  resource-subscribe API. This is supporting evidence, not a complete UI audit.

## Protocol versus product support

[MCP 2026-07-28 subscriptions](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)
define a long-lived stream with explicit resource URI filters, an initial
acknowledgment, and resource-update notifications. A disconnect ends the stream;
the client must establish a new subscription. The protocol does not require the
host to wake a model or inject a conversation message.

This experiment uses the older initialization protocol and stdio. It does not
exercise the July protocol's `server/discover` and `subscriptions/listen` wire
format, Streamable HTTP, or an active desktop model turn. The result supports a
concrete limitation in the tested backend path, not a claim that every Codex
transport or future version behaves identically.

## Reproduce

Requires Python 3.11+ and a Codex executable. Run from the repository root:

```sh
python3 spikes/mcp-subscriptions/probe.py \
  --codex /Applications/ChatGPT.app/Contents/Resources/codex \
  --output /tmp/sosein-subscription-probe
```

The probe reads only integration names from the user configuration to disable
them for its subprocess. It does not modify the configuration or export its
values. Additional managed/project configuration can affect other machines;
inspect the trace before treating another run as equivalent.

## Next acceptance test

When Codex adds a subscription-to-agent path, test an active task that reads and
watches one artifact. Change the artifact independently, then verify that Codex
subscribes, receives the event, fetches the new revision, and makes the update
visible to the same task without a user prompt. Repeat after reconnect and ensure
the agent's own writes do not create a reaction loop.

Until then, an explicitly requested wait-for-change tool could be a separate
fallback experiment for a running task. That would still require the agent to
call and wait on a tool; it is not unsolicited push into an arbitrary Codex task.
