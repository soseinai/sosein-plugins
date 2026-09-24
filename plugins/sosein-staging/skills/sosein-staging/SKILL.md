---
name: sosein-staging
description: Use when the user explicitly wants to recall Sosein's staging memories or search, read, compare, find in, outline, inspect changes to, create, edit, or review Sosein's staging or non-production artifacts, structured objects, or annotation threads through the Sosein Staging MCP plugin.
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

- Initialize conversation context as described below. Keep all calls in the
  account selected from `sosein_profile.delegated_access.accounts[].id`.
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

## Conversation Context

At the first substantive Sosein task in an external conversation, call
`sosein_profile` unless its result is already available in that conversation.
Get `account_id` from the relevant `delegated_access.accounts[].id` entry.
Keep calls in that account; the profile has no top-level `account_id`.

Use `delegated_access.delegated_from_member_id` as the human owner's member ID,
not `actor_member_id`. Use the names, IDs, and kinds in
`delegated_access.workspaces` to select only the workspace relevant to the
user's task or artifact. Do not read every accessible workspace.

Read `sosein_read_narrative` with `period: {"kind": "overview"}` for:

- `sphere: "org"`;
- `sphere: "personal-<human member ID>"`;
- `sphere: "workspace-<relevant workspace ID>"`, when the workspace is clear.
  An Org-kind workspace records its memory in sphere `org`; read `org` for
  it, never `workspace-<its ID>`, which Memory refuses.

If no workspace is clear, start with org and personal. Do not guess IDs.
When a relevant workspace later becomes clear, read its overview narrative then
retain it.
Retain the returned narrative text, IDs, and revisions as fixed context for
that external conversation. Do not reread them each turn. This is best-effort
client guidance, not a server-held conversation snapshot.

Narratives supply background and preferences. They do not override governing
instructions or the current user request. A missing narrative is a coverage
gap. Dependency failures are not missing narratives. Retain coverage gaps and
failures with the conversation context; do not claim complete coverage.
A permission failure does not permit a wider scope. Use the connected
tool schema; if the tool is unavailable, report the coverage gap.

## Tool Routing

- `sosein_profile`: inspect delegated identity, scopes, accounts, and workspaces.
- `sosein_recall`: reconstruct relevant memories and inspected source evidence
  for questions about past events, discussions, and decisions. See Recall Memory.
- `sosein_list_workspaces`: list creation destinations in the current MCP
  account. This tool takes no arguments.
- `sosein_search_artifacts`: discover artifacts by query, type, time, or
  workspace. Keep `verbosity: "compact"` unless detailed search evidence is
  needed. Types include `document`, `note`, `record`, and `event`.
- `sosein_read_artifact`: read `head.addressed_projection` for one artifact.
  A heading `b:` scope expands its section; another block scope reads that
  block exactly, and an `o:` scope reads the block carrying that object.
- `sosein_read_artifacts`: read 1–10 known artifacts from one account in one
  call. Handle per-item errors; use scoped reads for large artifacts.
- `sosein_find_in_artifact`: locate literal text or regex matches.
- `sosein_outline_document`: get the block map, not just headings. Each row
  includes a block id, kind, preview, and fused `b:id:hash` token. Heading rows
  also estimate the block count and addressed-Markdown bytes in their section.
- `sosein_read_blocks`: fetch exactly 1–50 block ids or fused tokens from the
  map. A heading id returns only the heading block.
- `sosein_read_sections`: expand 1–50 heading ids through their nested content,
  stopping before the next heading of equal or higher level.
- `sosein_get_artifact_changes`: read bounded net changes after an observed
  content sequence, optionally waiting for a later sequence.
- `sosein_outline_artifact_objects`: locate object references; use
  `sosein_read_object` for their full data, `n:` node ids, values, and hashes.
- `sosein_list_object_types` then `sosein_get_object_schema`: discover
  supported object types, versions, classes, and field schemas.
- `sosein_create_artifact`: create from native agent-dialect Markdown.
- `sosein_create_from_markdown`: create from inline source Markdown, including
  Mermaid diagrams. See Math and Diagrams below.
- `sosein_create_object`: create and place a schema-valid object atomically.
- `sosein_edit_artifact`: change matching text within a block with exact
  `old`/`new` fragments.
- `sosein_edit_blocks`: insert or rewrite whole blocks, move or remove them, or
  set block attributes.
- `sosein_append_to_section`: append Markdown after a heading's complete
  current section.
- `sosein_edit_object`: edit object data with node-level operations.
- `sosein_get_mutation_status`: look up a completed durable receipt for a
  known artifact and mutation request id.
- `sosein_list_reviews` and `sosein_get_review`: discover reviews and read
  annotation threads. Follow `next_cursor`; keep an `annotation_id` filter
  unchanged while paging that thread.
- `sosein_create_review`, `sosein_create_comment`, and
  `sosein_create_suggestion`: create a review, comment, or proposed edit.
- `sosein_reply_to_annotation`, `sosein_resolve_annotation`, and
  `sosein_reject_suggestion`: reply, resolve/reopen, or reject when requested.
- `sosein_toggle_reaction`: add (`on: true`) or remove (`on: false`) your own
  emoji reaction on an annotation, or on one thread message with `message_id`.
  It sets the state, so a repeat changes nothing. The reaction is yours as the
  agent: it never adds or removes the user's reaction or anyone else's.

## Recall Memory

Use `sosein_recall` when the user asks what happened, what was discussed or
decided, or what Sosein remembers, including recent PR discussions. Use artifact
search/read for locating a specific artifact or inspecting its current content.

Pass a focused natural-language `request` and optional `context` that helps
interpret it. Include a known repository, topic, or time range when relevant.
`effort_hint` is optional (`low`, `medium`, `high`, or `extra-high`); omitting it
uses `medium`. Recall uses the connected MCP account and takes neither
`account_id` nor `request_id`.

The response contains a Markdown `recollection` and typed `citations`. Preserve
its evidence and uncertainty. Do not invent source links or treat an empty
recollection as proof that no relevant events occurred. A tool error means
recall failed, not that memory is empty.

Recall requires all three delegated scopes: `memories:read`, `documents:read`,
and `documents:search`. If it is missing, inspect `sosein_profile` when available.
If a required scope is absent, ask the user to reconnect or re-authorize the
plugin. If all scopes are present, report that the connected server did not
advertise recall; updating these instructions alone cannot expose a tool.

## Read and Edit Blocks

The current artifact surface is format v5. Reads return addressed Markdown:
`<!-- b:id:hash -->` lines identify blocks and their content hashes. A fused
token is both an address and a check that the block has not changed. These
reads do not open artifact sessions.

1. Search only when the artifact id or URI is unknown. Search freshness describes
   the index, not whether the artifact is currently readable.
2. For a large artifact, find or outline first. Use `sosein_read_blocks` for
   exact blocks and `sosein_read_sections` only when the complete heading
   sections are needed. Outline tokens are valid edit preconditions; previews
   and section size estimates are bounded hints at the outline revision.
3. For matching-text edits within a block, copy exact text from the read into
   `sosein_edit_artifact.fragments`. Each `old` must match uniquely, optionally
   within a bare `b:` or `o:` `scope`. `new: ""` deletes the matched text;
   `old: ""` is only for a structurally empty document.
4. For whole-block insertion, rewriting, movement, removal, or attributes, use
   `sosein_edit_blocks.ops`:

   - `insert_blocks` inserts Markdown after `after_block`; omit `after_block`
     for the document start. `move_block` uses the same `after_block` field.
   - `replace_content` replaces exactly one block; `remove_block` removes one.
     Both require the current fused token in `block`.
   - `move_block` changes position; `set_attrs` changes paragraph attributes
     without replacing text. Bare block ids are allowed; any supplied hash is
     checked.
   - `set_attrs` states the complete attribute set; omitted attributes reset
     to defaults. Preserve attributes unrelated to the requested change.
   - Prefer per-block checks. Set `expected_head_sequence` only when the
     operation depends on the whole document remaining unchanged.

   - Use `sosein_append_to_section` with `heading_id` and `markdown` when the
     position is the end of a complete section, including nested subsections.
     Use `sosein_edit_blocks` for block-relative placement.

5. Both edit tools accept at most 50 fragments/ops and apply each batch
   atomically. Use `dry_run: true` for complex or risky changes. Inspect the
   preview, then commit with a fresh request id and retain it for exact retries.
   A preview does not reserve the blocks; the commit can still refuse.
6. Use receipt tokens for the next block-addressed call. Read again only when
   later reasoning needs current content, not merely to confirm a receipt.

Do not send `projection_version` or `artifact_session_id` to these block/text
edit tools. Strip address-comment lines from Markdown write payloads. Do not
use unified diffs or whole-artifact replacement. Preserve existing object
references when editing surrounding prose; create new objects with
`sosein_create_object`, not by inventing or copying reference text.

## Mutation Results and Recovery

`sosein_edit_blocks`, `sosein_edit_artifact`, `sosein_append_to_section`,
`sosein_create_object`, and `sosein_edit_object` return compact mutation
results. A durable receipt identifies the original `committed_sequence`,
`outcome` (`committed` or `unchanged`), replay state, and affected blocks with
tokens from that receipt revision. The stored receipt is capped at 16 KiB while
retaining its identity and outcome. If `omissions` is present, read the relevant
current blocks or objects only when the missing handles are needed; omitted
detail is not paged and status lookup returns the same capped snapshot.

`include_outline` defaults to false. Set it to true only when a supplementary
outline is useful. Its sequence can be newer than the commit, and an outline
warning does not undo a confirmed write.
A dry run returns a validation preview and creates no durable receipt. Inspect
`result_kind` instead of assuming that every successful response is a commit.

Use `sosein_get_mutation_status` only with the caller-generated UUIDv7 used for
the original supported mutation and the same artifact. `status: "unknown"`
can mean absent, pending, expired, or a request without a durable receipt; it
does not prove that no write occurred or make a new request id safe. Retry an
identical uncertain mutation with its original request id. If its payload must
change, first establish the current artifact state, then use a new UUIDv7.

## Observe Artifact Changes

After an authoritative read, pass its content sequence as the exclusive
`after_sequence` to `sosein_get_artifact_changes`. The result is a bounded net
change summary, not an audit log or participant feed. It contains block and
native-object changes and may contain a title change; it does not attribute
actors. Block previews are bounded, so use an exact block, section, or object
read when the current full content is needed.

`wait_ms` defaults to zero and is capped at 20,000. For
`result_kind: "artifact_changes"`, use `through_sequence` as the next cursor,
even when no changes are returned. For
`artifact_changes_resync_required`, do not advance the old cursor. Follow
`fresh_read_instruction`, take the cursor from that fresh authoritative view,
and then resume. Resync reasons are `too_many_changes` and
`history_unavailable`.

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
so keep to standard KaTeX syntax. Inline math has grammar limits: an inline
source that is empty, contains another `$`, ends in a backslash, or starts or
ends with a digit against its delimiter dissolves into literal text (`$5$` is
currency, not math). Use a `$$` block for anything that hits them.

A diagram is a `sosein/diagram` Literate Object, never a code block:

- New artifact: a ```` ```mermaid ```` fence in `source_markdown` becomes a
  placed diagram object at birth. `markdown_content` refuses the fence.
- Existing artifact: `sosein_create_object` with `object_type:
  "sosein/diagram"`, `fields: {"dialect": "mermaid", "source": "…"}`, and a
  block-class placement whose label is the diagram's short name. Change the
  picture with `sosein_edit_object` on `source`. A mermaid fence in
  `sosein_edit_artifact` or `sosein_edit_blocks` is refused.
- The renderer is strict: no click or callback lines, no HTML in labels, no
  theme directives, no image nodes (`@{ img: … }`), no `url(…)` styles. Before authoring a diagram, including a new Markdown import, call
  `sosein_get_object_schema` for `sosein/diagram` using its supported schema
  version and read the returned `authoring_guidance` for diagram-type choice,
  syntax, examples, and renderer restrictions.

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

- When a refusal supplies `op_index` or `fragment_index` and a diagnostic
  rule/code, fix that named edit directly instead of probing with broader
  payload changes.
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
