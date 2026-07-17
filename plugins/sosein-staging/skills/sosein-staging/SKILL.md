---
name: sosein-staging
description: Use when the user explicitly wants to search, read, compare, find in, outline, create, edit, or reason over Sosein's staging or non-production artifacts or their structured objects through the Sosein Staging MCP plugin.
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
  context do not identify it. Use the requested workspace when several exist.
- Prefer the narrowest tool and smallest read that completes the task. Preserve
  `artifact_session_id` across calls for the same artifact when returned.
- Treat search, find, and outline results as discovery metadata. Read the
  artifact or object before relying on its current content or writing to it.
- For every mutation, generate a valid caller-stable UUIDv7 `request_id`. Reuse
  it only for an exact retry (including committing an unchanged dry run); use a
  new UUIDv7 whenever the payload changes or for an independent mutation.
- Prefer artifact resource links returned by MCP tools when referencing results.
- Use tool calls for discovery. MCP resource listing is scoped to a known
  account and artifact; it is not a browsable artifact catalog.
- Separate facts read from Sosein from your own inference.

## Tool Routing

- `sosein_profile`: inspect delegated identity, scopes, accounts, and workspaces.
- `sosein_search_artifacts`: discover artifacts by query, type, time, or
  workspace. Keep `verbosity: "compact"` unless full ranking evidence or search
  diagnostics are needed. Search can return documents, notes, and events.
- `sosein_read_artifact`: read one known artifact. Use `scope` with a `b:`
  heading id or `o:` object id when only one subtree is needed.
- `sosein_read_artifacts`: read 1–10 known artifacts from the same account in
  one call. Handle per-item errors; use scoped single reads for large artifacts.
- `sosein_find_in_artifact`: locate literal text or regex in a known artifact.
- `sosein_outline_document`: discover headings and `b:` section ids.
- `sosein_outline_artifact_objects`: discover object references and their
  surrounding section. Use `sosein_read_object` for their actual data.
- `sosein_read_object`: read one `o:` object and its `n:` node ids,
  `object_type`, `schema_version`, values, and edit preconditions.
- `sosein_list_object_types` then `sosein_get_object_schema`: discover the
  supported object contract; never infer it from projected text.
- `sosein_create_artifact`: create a document or note.
- `sosein_create_object`: create a schema-valid object and insert its reference
  into an existing artifact atomically.
- `sosein_edit_artifact`: edit prose with projection-versioned exact fragments.
- `sosein_edit_object`: edit structured object data with node-level operations.

## Read Workflow

1. Resolve the account with `sosein_profile` if necessary.
2. Search only when the artifact id or URI is unknown. Use filters instead of
   broad queries when the request supplies type, date, or workspace context.
3. Read selected results to confirm content and access. Search freshness reports
   index state, not whether the artifact is currently readable.
4. For a large known artifact, outline or find first, then use the returned `b:`
   id in a scoped read. For embedded object data, outline objects or use a known
   `o:` id, then call `sosein_read_object`.

## Artifact Writes

Create with `sosein_create_artifact`, an `account_id`, title, UUIDv7
`request_id`, optional initial content, and explicit `type` when a note is
intended. Events are readable/searchable but are not created or edited here.

For an existing artifact:

1. Read the latest projection and retain its `artifact_session_id` and
   `head.projection_version`.
2. If needed, find or outline the target, then read the exact section again.
   Find/outline output is not an edit anchor.
3. Build `sosein_edit_artifact.fragments` from the projection just read. Each
   `old` value must match exactly and uniquely; `new` is the replacement
   (`""` deletes). Add a `b:` or `o:` `scope` when uniqueness needs narrowing.
4. Use `dry_run: true` for multi-fragment, section-wide, or otherwise risky
   edits. Inspect the preview, then commit unchanged with the same request id;
   use a new request id if the payload changes.
5. Re-read after commit when confirmation or subsequent reasoning depends on
   the final state.

Never use unified diffs or whole-artifact replacement for an existing artifact.
Manage newlines explicitly. Do not create or copy projected object references
with text fragments; use `sosein_create_object`.

## Object Writes

To create an object:

1. Call `sosein_list_object_types`, then `sosein_get_object_schema` for the
   chosen type and version.
2. Read the destination artifact and choose a placement: a unique text anchor
   or a start/end boundary, optionally scoped by `b:` or `o:` id.
3. Call `sosein_create_object` with schema-valid fields, the read projection
   version/session, placement, title, and a fresh UUIDv7 request id.

To edit an object, call `sosein_read_object`, then `sosein_edit_object` with its
exact `object_type`, `schema_version`, and current `n:` ids, values, and hashes.
Use the structured `add_field`, `update_field`, `remove_field`, `insert`,
`delete`, or `move` operation described by the tool schema; never replace the
whole object. Preserve collections' object-only shape and let Sosein allocate
new node ids. Never assume a type, version, field, or value even if familiar;
derive them from the catalog, schema, fresh read, and user's stated intent, and
ask when required intent is missing.

## Recovery

- On stale projection, missing/multiple anchor, invalid scope, overlap, or stale
  object precondition: re-read, rebuild the write against current ids and
  values, and use a fresh request id because the payload changed.
- On `request_id_conflict`: retry with the old id only if the payload is
  identical; otherwise generate a fresh UUIDv7.
- On missing scope/tool/permission: inspect `sosein_profile`, then ask the user
  to re-authorize when the requested capability is not delegated.
