---
name: sosein-staging
description: Use when the user explicitly wants to search, read, compare, find in, outline, create, edit, or review Sosein's staging or non-production artifacts, structured objects, or annotation threads through the Sosein Staging MCP plugin.
---

# Sosein Staging

Use the Sosein Staging MCP tools for non-production data at
`https://app.staging.sosein.ai/mcp`. Use production Sosein for ordinary Sosein
requests unless the user explicitly asks for staging, testing, or
non-production data.

The connection uses OAuth. Access and available tools reflect permissions
delegated by the signed-in user. If access is missing, ask the user to connect
or re-authorize the plugin; never request bearer tokens.

## Core Rules

- Get `account_id` from `sosein_profile` when the user, prior results, or current
  context do not identify it. Keep all artifact and review calls in that account.
- Use the connected tool schemas for exact arguments and supported operations.
  If the connected server lacks a tool, report the limit; do not invent a call.
- Prefer the narrowest tool and smallest read that completes the task. Search
  hits, text matches, and outline previews are not full artifact content.
- For every mutation, generate a valid caller-stable UUIDv7 `request_id`. Reuse
  it only for an exact retry, including a later tool invocation. Use a new UUIDv7
  when the payload changes or for an independent mutation.
- Prefer artifact and review resource links returned by MCP tools. Resource
  listing is scoped to a known account/artifact, not a browsable artifact catalog.
- Separate facts read from Sosein from your own inference.

## Tool Routing

- `sosein_profile`: inspect delegated identity, scopes, accounts, and workspaces.
- `sosein_list_workspaces`: list creation destinations in the current MCP
  account. This tool takes no arguments.
- `sosein_search_artifacts`: discover artifacts by query, type, time, or
  workspace. Keep `verbosity: "compact"` unless detailed search evidence is
  needed. Types include `document`, `note`, `record`, and `event`.
- `sosein_read_artifact`: read `head.addressed_projection` for one artifact.
  Use a `b:` block or `o:` object `scope` for a subtree.
- `sosein_read_artifacts`: read 1–10 known artifacts from one account in one
  call. Handle per-item errors; use scoped reads for large artifacts.
- `sosein_find_in_artifact`: locate literal text or regex matches.
- `sosein_outline_document`: get the block map, not just headings. Each row
  includes a block id, kind, preview, and fused `b:id:hash` token.
- `sosein_read_blocks`: fetch 1–50 block ids or fused tokens from the map.
  A heading id returns its whole section.
- `sosein_outline_artifact_objects`: locate object references; use
  `sosein_read_object` for their full data, `n:` node ids, values, and hashes.
- `sosein_list_object_types` then `sosein_get_object_schema`: discover
  supported object types, versions, classes, and field schemas.
- `sosein_create_artifact`: create from native agent-dialect Markdown.
- `sosein_create_from_markdown`: create from inline source Markdown, including
  Mermaid diagrams. See Math and Diagrams below.
- `sosein_create_object`: create and place a schema-valid object atomically.
- `sosein_edit_artifact`: edit prose with exact `old`/`new` fragments.
- `sosein_edit_blocks`: insert, replace, move, remove, or set block attributes.
- `sosein_edit_object`: edit object data with node-level operations.
- `sosein_list_reviews` and `sosein_get_review`: discover reviews and read
  annotation threads. Follow `next_cursor`; keep an `annotation_id` filter
  unchanged while paging that thread.
- `sosein_create_review`, `sosein_create_comment`, and
  `sosein_create_suggestion`: create a review, comment, or proposed edit.
- `sosein_reply_to_annotation`, `sosein_resolve_annotation`, and
  `sosein_reject_suggestion`: reply, resolve/reopen, or reject when requested.

## Read and Edit Blocks

The current artifact surface is format v5. Reads return addressed Markdown:
`<!-- b:id:hash -->` lines identify blocks and their content hashes. A fused
token is both an address and a check that the block has not changed. These
reads do not open artifact sessions.

1. Search only when the artifact id or URI is unknown. Search freshness describes
   the index, not whether the artifact is currently readable.
2. For a large artifact, find or outline first, then read the relevant blocks.
   Outline tokens are valid edit preconditions; previews can be truncated.
3. For prose edits, copy exact text from the read into
   `sosein_edit_artifact.fragments`. Each `old` must match uniquely, optionally
   within a bare `b:` or `o:` `scope`. `new: ""` deletes the matched text;
   `old: ""` is only for a structurally empty document.
4. For structural edits, use `sosein_edit_blocks.ops`:

   - `insert_blocks` inserts Markdown after `after`; omit `after` for the start.
   - `replace_content` replaces exactly one block; `remove_block` removes one.
     Both require the current fused token in `block`.
   - `move_block` changes position; `set_attrs` changes paragraph attributes
     without replacing text. Bare block ids are allowed; any supplied hash is
     checked.
   - `set_attrs` states the complete attribute set; omitted attributes reset
     to defaults. Preserve attributes unrelated to the requested change.
   - Prefer per-block checks. Set `expected_head_sequence` only when the
     operation depends on the whole document remaining unchanged.

5. Both edit tools accept at most 50 fragments/ops and apply each batch
   atomically. Use `dry_run: true` for complex or risky changes. Inspect the
   preview, then commit with a fresh request id and retain it for exact retries.
   A preview does not reserve the blocks; the commit can still refuse.
6. Re-read after commit when confirmation or later reasoning needs final content.

Do not send `projection_version` or `artifact_session_id` to these block/text
edit tools. Strip address-comment lines from Markdown write payloads. Do not
use unified diffs or whole-artifact replacement. Preserve existing object
references when editing surrounding prose; create new objects with
`sosein_create_object`, not by inventing or copying reference text.

## Artifact Creation

Both creation tools require `account_id`, title, and UUIDv7 `request_id`.
Choose `document` (the default), `note`, or `record` explicitly as needed.
Events can be searched and read but are not created or edited here.

For a shared destination, call `sosein_list_workspaces` and pass the requested
`workspace_id`. Omit it for a private artifact. If the requested destination is
unclear, ask before creating; do not silently make a shared request private.

Use `sosein_create_artifact.markdown_content` for the native agent dialect;
omit it or pass an empty string for an empty artifact. It refuses object
references at birth and does not support Mermaid. Create the artifact first,
then create and place supported objects.

Use `sosein_create_from_markdown.source_markdown` for non-empty source Markdown
or Mermaid. This is synchronous inline creation, not a file-upload or conversion
job tool. Both tools accept optional `external_uri` for a caller-owned canonical
identity; do not invent one or use the reserved `sosein-ext` scheme.

## Math and Diagrams

Math is a spelling, not a tool. Write display math as a `$$` fence with each
delimiter alone on its own line, and inline math as `$…$`, with KaTeX LaTeX
inside. Both work in `markdown_content`, `source_markdown`, edit fragments,
and block payloads, and read back exactly as written. Nothing validates the
LaTeX on write; the Doc app renders an unparseable formula in an error colour,
so keep to standard KaTeX syntax. A `$` inside inline math ends the formula,
and an inline source must not end in a backslash.

A diagram is a `sosein/diagram` Literate Object, never a code block:

- New artifact: a ```` ```mermaid ```` fence in `source_markdown` becomes a
  placed diagram object at birth. `markdown_content` refuses the fence.
- Existing artifact: `sosein_create_object` with `object_type:
  "sosein/diagram"`, `fields: {"dialect": "mermaid", "source": "…"}`, and a
  block-class placement whose label is the diagram's short name. Change the
  picture with `sosein_edit_object` on `source`. A mermaid fence in
  `sosein_edit_artifact` or `sosein_edit_blocks` is refused.
- The renderer is strict: no click or callback lines, no HTML in labels, no
  theme directives. Load the `mermaid` skill for diagram-type choice and
  syntax.

## Object Writes

Before creation, call the type catalog and schema tools. Use their `class` and
field schema, not a guessed type or a fixed list of supported types. Read the
destination, then supply schema-valid `fields` and mandatory `placement`:

- Block-class: `{kind: "document_start", label}` or
  `{kind: "after_block", block_id: "b:…", label}`.
- Inline-class: `{kind: "inline", block: "b:…:hash", label,
  anchor: {text: "exact text", side: "before" | "after"}}`.

Every placement needs a non-empty, single-line visible label. The block-class
placement uses a bare block id; inline placement uses a fused token and exact
text anchor. Do not send the old projection-version or projection-anchor shape.
Sosein allocates the object id and commits the object and reference together.

For edits, call `sosein_read_object`, then `sosein_edit_object` with the returned
`object_type`, `schema_version`, and current `n:` ids, values, and hashes.
Use `add_field`, `update_field`, `remove_field`, `insert`, `delete`, or `move`
as specified by the schema, not whole-object replacement. Collections contain
objects only; Sosein allocates new node ids. If an object tool returns an
`artifact_session_id`, preserve it only on later tools whose schema accepts it.

## Reviews and Suggestions

Read an existing review before adding to it. Create a review only when the
request needs a new container. The default `audience_threshold` is `reviewer`;
use `edit` only when the requested audience calls for it.

- A comment with no target is artifact-wide. For a text comment, read the block,
  copy its fused token into `block`, and copy exact projected text into `quote`.
  Quotes cannot cross blocks. Set the 1-based `occurrence` if the quote repeats.
- For a direct object comment, use `literate_object_ref` with its exact `o:` id
  and the first 7 lowercase hex characters of `sosein_read_object.record_hash`.
- A suggestion needs `block`, `quote`, and exactly one `edit` kind:
  `change: {text}`, `delete: {}`, or `insert: {side, text}`. For insertion,
  quote existing adjacent text, not the new text. Suggestions do not modify the
  artifact. Add an explanation with `sosein_reply_to_annotation`.
- There is no accept-suggestion MCP tool. Do not substitute a direct edit for
  acceptance. Resolving/reopening an annotation is not accepting a suggestion.
  Rejection is terminal; use it only when the user requests rejection.
- Inspect `placement` and `target_status` when returned. Missing placement
  metadata does not prove an anchor is orphaned.

## Recovery

- On `block_hash_mismatch`, use the refusal's current block content when it is
  sufficient; otherwise read the block again. Rebuild the edit and use a fresh id.
- On a missing block, use returned nearby ids or refresh the block map.
- On missing/ambiguous text, invalid scope, overlap, or a stale object
  precondition, read the affected content and rebuild with a fresh request id.
- On `request_id_conflict`, reuse the old id only for the identical request;
  use a new UUIDv7 for a changed payload.
- On `unsupported_format_version`, report the limit; do not send legacy fields.
- On missing scope/tool/permission, inspect `sosein_profile`, then ask the user
  to re-authorize when the required capability is not delegated.
