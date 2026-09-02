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

The current server catalog contains 26 tools. OAuth scopes and delegated
permissions determine which tools the connected agent can use. The connected
tool schemas are authoritative for exact arguments.

| Need | Tool |
| --- | --- |
| Inspect identity, account, and delegated scopes | `sosein_profile` |
| Find workspaces where the user can create artifacts | `sosein_list_workspaces` |
| Search documents, notes, records, and events | `sosein_search_artifacts` |
| Read one artifact or a batch of 1–10 | `sosein_read_artifact`, `sosein_read_artifacts` |
| Find text or inspect the block map | `sosein_find_in_artifact`, `sosein_outline_document` |
| Read selected blocks or sections | `sosein_read_blocks` |
| Locate and read structured objects | `sosein_outline_artifact_objects`, `sosein_read_object` |
| Discover object types and field schemas | `sosein_list_object_types`, `sosein_get_object_schema` |
| Create from native agent Markdown or source Markdown | `sosein_create_artifact`, `sosein_create_from_markdown` |
| Create and place a structured object | `sosein_create_object` |
| Edit prose, block structure, or object fields | `sosein_edit_artifact`, `sosein_edit_blocks`, `sosein_edit_object` |
| Find and read reviews and annotation threads | `sosein_list_reviews`, `sosein_get_review` |
| Create a review, comment, or proposed edit | `sosein_create_review`, `sosein_create_comment`, `sosein_create_suggestion` |
| Reply, resolve/reopen, or reject a suggestion | `sosein_reply_to_annotation`, `sosein_resolve_annotation`, `sosein_reject_suggestion` |

Search requires an `account_id`; get it from `sosein_profile` when unknown.
Search results are discovery metadata, not proof of current content or access.
Read the artifact or object before using its content.

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
by `sosein_outline_document` contains these tokens; `sosein_read_blocks`
fetches selected blocks, or a whole section when given a heading id.

Use `sosein_edit_artifact` for exact `old`/`new` fragments, optionally scoped
to a bare `b:` or `o:` id. Use `sosein_edit_blocks` for block insertion,
replacement, attributes, moves, and removal. Replacement and removal require
the fused token. Both paths apply an atomic batch of at most 50 fragments/ops.
They do not take `projection_version` or `artifact_session_id`.

Strip address comments from Markdown write payloads. Do not use unified diffs
or whole-artifact replacement. Read object data with `sosein_read_object` and
edit its fields through `sosein_edit_object`; document reads show references,
not full object records.

Each write requires a caller-stable UUIDv7 `request_id`. Reuse it only for an
exact retry. Use `dry_run` to preview complex text/block changes, then commit
with a fresh request id. If a block or anchor changed, use the typed refusal's
current content or read again, rebuild the write, and use a new request id.

## Reviews

Comments can target the artifact, exact text within one witnessed block, or an
object reference. Suggestions propose a change, deletion, or insertion without
changing the artifact. There is no MCP tool to accept a suggestion; resolving
an annotation is not acceptance. Rejection is terminal.

## Skill

The bundled skill contains the detailed workflow, placement forms, review
anchors, retry rules, and error recovery. It also keeps production and staging
requests separate.
