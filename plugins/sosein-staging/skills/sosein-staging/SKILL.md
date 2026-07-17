---
name: sosein-staging
description: Use when the user explicitly asks the agent to search, read, find in, outline, create, edit, or reason over Sosein Staging or non-production Sosein Markdown artifacts through the Sosein Staging MCP plugin.
---

# Sosein Staging

Use the Sosein Staging MCP tools when the user explicitly asks about documents,
notes, drafts, workspaces, or search results stored in Sosein Staging.

The plugin connects to staging at `https://app.staging.sosein.ai/mcp`. Use the
production Sosein plugin for ordinary Sosein requests unless the user explicitly
asks for staging, testing, or non-production data.

The MCP connection authenticates with OAuth. Treat the connected MCP actor as an
agent identity whose access is delegated from the signed-in human user. If access
is missing, ask the user to connect or re-authorize the plugin rather than
requesting bearer tokens.

## Tool Choice

Prefer the narrowest tool that answers the request:

- `sosein_profile`: confirm delegated owner, agent, scopes, accounts, and
  workspace context. Use this first when identity or permissions matter.
- `sosein_search_artifacts`: find artifacts by title, topic, phrase, question,
  recency, type, account, or workspace. It requires `account_id`; get that from
  `sosein_profile` when it is not already known. Pass `type: "document"` or
  `type: "note"` when the request is type-specific.
- `sosein_read_artifact`: read a known artifact id or URI.
- `sosein_read_object`: read full canonical data for a projected object marker
  such as `read_object(o:00000001)`.
- `sosein_edit_object`: mutate one referenced object with structured operations
  against `n:` node ids returned by `sosein_read_object`. Use this for object
  data edits; `sosein_write_object` is not part of the current tool surface.
- `sosein_find_in_artifact`: find literal text or regex inside a known artifact.
  Use for discovery when target text might be ambiguous or when line/heading
  context helps locate the target; do not use find output as an edit anchor.
- `sosein_outline_document`: get Markdown heading paths and section ranges. Use
  for discovery before heading-scoped edits; do not use outline output as an
  edit anchor.
- `sosein_create_artifact`: create a new Markdown artifact. Pass `type:
  "document"` or `type: "note"`; omit it only when a document is intended.
- `sosein_edit_artifact`: change an existing artifact with anchored fragments
  built from a fresh `sosein_read_artifact` projection.

Prefer MCP resource links returned by search/read/create/edit tool calls when present.
List resources only after a specific artifact id or URI is known.

## Find And Outline

`sosein_find_in_artifact` defaults to literal, case-sensitive search with 2
context lines and 20 matches. Use `mode: "regex"` only when literal matching is
not enough. Use `case_sensitive: false` intentionally; do not hide casing
differences when the edit itself needs exact Markdown.

Find results return line ranges, byte ranges, heading paths, and surrounding
context. Use those to choose exact anchors, but remember that
`sosein_edit_artifact` does not accept byte offsets. Before editing, re-read the
artifact and build fragments from the returned projection.

## Existing Artifact Edits

Do not use unified diffs or full-document replacement for existing artifacts.
Use `sosein_edit_artifact` with anchored fragments against the latest committed
projection.

Workflow:

1. Locate the artifact with search if needed.
2. Read the latest head with `sosein_read_artifact`.
3. Keep `artifact_session_id` from the response when present and pass
   `head.projection_version` as `projection_version`.
4. Narrow the target with `sosein_find_in_artifact` or
   `sosein_outline_document` when the edit target is not obviously unique, then
   re-read before constructing the write.
5. Build anchored fragments against exactly the projection you read.
6. Use `dry_run: true` for multi-edit, section, or high-risk changes; inspect the
   preview before committing.
7. Commit with `dry_run` omitted or false. Re-read after commit when the user
   needs confirmation or when the follow-up answer depends on the final text.

Fragment targeting:

- `old` is exact projected Markdown that must still match uniquely.
- `new` is the replacement Markdown; use `new: ""` to delete `old`.
- `scope` is optional. Use a `b:` heading id or `o:` object id from the read
  projection when the same text appears more than once.
- Prefer a longer exact `old` with surrounding Markdown over relying on a very
  short fragment.
- Manage newlines explicitly in `new`. The server inserts exactly what you send.

Compact edit payload shape:

```json
{
  "artifact_id": "<uuid>",
  "artifact_session_id": "<uuid from read response when present>",
  "projection_version": 3,
  "dry_run": true,
  "fragments": [
    {
      "old": "exact Markdown from the read projection",
      "new": "replacement Markdown",
      "scope": "b:00000001"
    }
  ]
}
```

## Existing Object Edits

Do not replace whole object records. For projected object data, read the object
with `sosein_read_object`, then call `sosein_edit_object` with
`object_type`, `schema_version`, a stable `request_id`, and structured ops.

Use ids and preconditions directly from the read response:

- `add_field`: creates one absent field on an existing node. Collection fields
  must be created as `[]`; populate them with `insert`.
- `update_field`: changes one scalar field only. Use the current scalar value as
  `expect`.
- `remove_field`: removes one field. Include the current value as `expect`; for
  object-valued fields, include that value's `__id`. Non-empty collections must
  be emptied with `delete` before the field itself can be removed.
- `insert`: adds one object node to a collection. The server strips incoming
  `__id` values and mints fresh ids for the inserted node and nested nodes.
  Arrays in literate objects may contain only objects, so wrap primitive array
  values in object nodes with a `value` field unless the schema defines a more
  specific field, for example `{ "value": "red" }`.
- `delete`: removes one collection node by `id`, `parent`, `field`, and the
  node's `expect_hash` from `sosein_read_object.nodes`.
- `move`: relocates one collection node while preserving its `n:` id. Use
  `from`, `from_field`, `into`, `field`, and optional `before` ids from the read.

When an object edit is rejected as stale, read the object again and regenerate
ops against the current node ids, hashes, and field values.

## Failure Handling

When an edit fails because the artifact is stale, do not retry the same fragment
payload. If the tool reports a projection version conflict, exact text matched
zero times, exact text matched multiple times, an invalid scope, or overlapping
fragments, read the latest head again, regenerate or rebase the fragments
against the new projection, explain the conflict if it affects the user-visible
edit, and submit the new fragments with the new `head.projection_version`.

When summarizing artifact content, distinguish direct artifact facts from your own inference.
