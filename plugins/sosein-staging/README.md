# Sosein Staging Plugin

This package connects your agent (Codex or Claude Code) to Sosein Staging.

```text
https://app.staging.sosein.ai/mcp
```

The agent discovers OAuth from the MCP server's protected-resource metadata,
registers as a public client, and completes authorization with PKCE. The MCP
actor uses access delegated from the signed-in human user. If access is missing,
connect or re-authorize the plugin; do not supply bearer tokens to the agent.

## Agent Surface

Tools are discovered from the connected MCP server. OAuth scopes and delegated
permissions determine which tools the connected agent can use. The connected
tool schemas are authoritative for exact arguments.

| Need | Tool |
| --- | --- |
| Inspect identity, account, and delegated scopes | `sosein_profile` |
| Read maintained narrative context for a sphere and period | `sosein_read_narrative` |
| Recall prior events, discussions, and decisions | `sosein_recall` |
| Find workspaces where the user can create artifacts | `sosein_list_workspaces` |
| Search documents, notes, records, and events | `sosein_search_artifacts` |
| Read one artifact or a batch of 1–10 | `sosein_read_artifact`, `sosein_read_artifacts` |
| Find text or inspect the block map | `sosein_find_in_artifact`, `sosein_outline_document` |
| Read exact blocks or complete heading sections | `sosein_read_blocks`, `sosein_read_sections` |
| Observe net changes after a content sequence | `sosein_get_artifact_changes` |
| Locate and read structured objects | `sosein_outline_artifact_objects`, `sosein_read_object` |
| Discover object types and field schemas | `sosein_list_object_types`, `sosein_get_object_schema` |
| Create from native agent Markdown or source Markdown | `sosein_create_artifact`, `sosein_create_from_markdown` |
| Create and place a structured object | `sosein_create_object` |
| Edit text, whole blocks, or object fields, or append to a section | `sosein_edit_artifact`, `sosein_edit_blocks`, `sosein_append_to_section`, `sosein_edit_object` |
| Recover a completed mutation receipt | `sosein_get_mutation_status` |
| Find and read reviews and annotation threads | `sosein_list_reviews`, `sosein_get_review` |
| Create a review, comment, or proposed edit | `sosein_create_review`, `sosein_create_comment`, `sosein_create_suggestion` |
| Reply, resolve/reopen, or reject a suggestion | `sosein_reply_to_annotation`, `sosein_resolve_annotation`, `sosein_reject_suggestion` |
| Add or remove your emoji reaction on an annotation or thread message | `sosein_toggle_reaction` |

Search requires an `account_id`; select the relevant
`sosein_profile.delegated_access.accounts[].id` entry. The profile has no
top-level `account_id`.
Search results are discovery metadata, not proof of current content or access.
Read the artifact or object before using its content.

## Narrative Context

At the first substantive Sosein task in a conversation, use the profile to
select the human owner and relevant workspace, then read their overview
narratives and the org overview narrative. Follow the skill's Conversation Context rules.
`sosein_read_narrative` takes `sphere` and `period`; account and caller authority
come from the connected MCP host. Do not pass `account_id` or a mutation
`request_id`.

Narrative reads require `memories:read` and delegated access to the selected
sphere. An older grant may need re-authorization before the tool is available.
A `missing` result is a coverage gap, not evidence that nothing happened.
Dependency failures are not missing narratives. Retain gaps and failures with
the conversation context; do not claim complete coverage or widen scope after
a permission failure. Retain returned narrative text, IDs, and revisions for
the conversation; do not reread each turn. If a relevant workspace later becomes
clear, read its overview narrative then retain it.

## Recall Memory

Use `sosein_recall` for questions about prior events, discussions, and decisions,
such as recent PR discussions. It accepts a natural-language `request`, optional
`context`, and optional `effort_hint` (`low`, `medium`, `high`, or `extra-high`;
default `medium`). It uses the connected MCP account, so do not pass `account_id`
or a mutation `request_id`. The result is a Markdown `recollection` with typed
`citations`; preserve the evidence and uncertainty when answering.

Recall requires `memories:read`, `documents:read`, and `documents:search`.
An older OAuth grant may need re-authorization before the server advertises the
tool. The plugin does not define a static tool allowlist. Updating the package
adds guidance; the deployed server and delegated scopes control availability.
Use artifact search/read when you need a specific artifact's current content.

## Creation and Placement

Both artifact creation tools support `document`, `note`, and `record`.
Call `sosein_list_workspaces` for a shared destination and pass its
`workspace_id`. Omit `workspace_id` for a private artifact.

Use `sosein_create_artifact` for native agent-dialect `markdown_content`, which
may be empty. Use `sosein_create_from_markdown` for non-empty inline
`source_markdown`, including Mermaid. It is not a file-upload or conversion
job interface. Both support an optional caller-owned `external_uri`.

New object references cannot be supplied in native artifact creation. Create the
artifact, discover the object schema, then use `sosein_create_object`. That
tool creates the object and its placement in one mutation. Placement requires
a visible label and must match the object's block or inline class.

## Editing Existing Artifacts

The current format-v5 read surface returns `head.addressed_projection`:
Markdown with `<!-- b:id:hash -->` lines. A fused `b:id:hash` token identifies
one block and checks that its content has not changed. The block map returned
by `sosein_outline_document` contains these tokens. `sosein_read_blocks`
fetches exactly the named blocks, including only the heading block for a heading
id. `sosein_read_sections` expands heading ids through nested content until the
next heading of equal or higher level. Heading outline rows include estimated
section block and byte counts to help bound the read. The existing
`sosein_read_artifact(scope)` behavior still expands a heading scope.

Use `sosein_edit_artifact` for exact `old`/`new` fragments, optionally scoped
to a bare `b:` or `o:` id. Use `sosein_edit_blocks` for block insertion,
replacement, attributes, moves, and removal. Replacement and removal require
the fused token. Both paths apply an atomic batch of at most 50 fragments/ops.
They do not take `projection_version` or `artifact_session_id`.

Block insertion and movement use `after_block`; omit it for document start.
Use `sosein_append_to_section` with `heading_id` and `markdown` to append after
the section's nested content.

Strip address comments from Markdown write payloads. Do not use unified diffs
or whole-artifact replacement. Read object data with `sosein_read_object` and
edit its fields through `sosein_edit_object`; document reads show references,
not full object records.

Each write requires a caller-stable UUIDv7 `request_id`. Reuse it only for an
exact retry. Use `dry_run` to preview complex text/block changes, then commit
with a fresh request id. If a block or anchor changed, use the typed refusal's
current content or read again, rebuild the write, and use a new request id.

The block/text, section-append, object-create, and object-edit tools return
compact mutation results. A durable receipt preserves the original outcome,
committed sequence, replay state, and affected block tokens from that receipt
revision. The stored receipt is capped at 16 KiB; `omissions` counts removed whole
entries, which are not paged. `include_outline` defaults to false; a requested
outline is supplementary current state and can be newer than the receipt. Dry
runs have no durable receipt. `sosein_get_mutation_status` returns
the same stored receipt when available; `unknown` does not prove no write
occurred, so retry an identical uncertain request only with its original UUIDv7.

`sosein_get_artifact_changes` returns bounded net changes after an exclusive
`after_sequence`; it is not an audit or presence feed and has no actor
attribution. Its block previews are not full content; read the exact block or
section when needed. `wait_ms` defaults to zero and is capped at 20,000. Advance to
`through_sequence` for every `artifact_changes` result, including an unchanged
one. A resync-required result has no new cursor: follow its fresh-read
instruction and resume from the fresh view.

## Reviews

Comments can target the artifact, exact text within one witnessed block, or an
object reference. Suggestions propose a change, deletion, or insertion without
changing the artifact. There is no MCP tool to accept a suggestion; resolving
an annotation is not acceptance. Rejection is terminal.

## Skills

The bundled skill contains the detailed workflow, placement forms, review
anchors, retry rules, and error recovery. It also keeps production and staging
requests separate.

Diagram authoring guidance comes from `sosein_get_object_schema` for
`sosein/diagram`: diagram-type selection, Mermaid syntax, renderer restrictions,
and placement workflow. The agent reads it before authoring a diagram; no
separate Mermaid skill is installed. Math needs no skill: `$$` display fences
and `$…$` inline spans are ordinary content on every create and edit path.
