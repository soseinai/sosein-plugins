# Sosein Staging Plugin

This package connects your agent (Codex or Claude Code) to Sosein Staging.

```text
https://app.staging.sosein.ai/mcp
```

The agent discovers OAuth from the MCP server's protected-resource metadata,
dynamically registers as a public client, and completes authorization with PKCE.
The resulting MCP actor is an agent identity whose access is delegated from the
signed-in human user's current Sosein Staging permissions. If access is missing,
agents should ask the user to connect or re-authorize this plugin, not ask for
bearer tokens.

## Agent Surface

The server exposes tools for profile inspection, artifact discovery, precise
reads, object reads/structured edits, text finding, heading outlines, document
or note creation, and anchored edits:

| Need | Tool |
| --- | --- |
| Confirm delegated identity, account, workspace, or scopes | `sosein_profile` |
| Find an artifact by title, topic, phrase, recency, or type in a known account | `sosein_search_artifacts` |
| Read the latest committed artifact head | `sosein_read_artifact` |
| Read full data for a projected object marker | `sosein_read_object` |
| Mutate a referenced object with structured operations | `sosein_edit_object` |
| Locate exact text or regex matches inside a known artifact | `sosein_find_in_artifact` |
| Get heading paths and section ranges | `sosein_outline_document` |
| Create a new document or note | `sosein_create_artifact` |
| Change an existing artifact | `sosein_edit_artifact` |

Search requires an `account_id`; agents should get that from `sosein_profile`
when it is not already known. Pass `type: "document"` or `type: "note"` when the
request is type-specific. Successful artifact and search responses include
resource links for readable latest-artifact URIs when the MCP client can use
them.

## Editing Existing Artifacts

Existing-artifact writes use `sosein_edit_artifact`, not unified diffs and not
full-document replacement. The tool accepts projection-versioned anchored
fragments:

- `old`: exact projected content that must still match uniquely.
- `new`: replacement content; use an empty string to delete `old`.
- `scope`: optional `b:` heading id or `o:` object id that narrows matching.

Agents should read the latest committed projection first and pass
`head.projection_version` as `projection_version`. Use `sosein_find_in_artifact`
and `sosein_outline_document` only as discovery aids; before editing, re-read
the artifact and build fragments from the returned projection. Use `dry_run:
true` for complex edits to preview the resolved changes before committing.

When `sosein_edit_artifact` reports an ambiguous, missing, stale, or conflicting
fragment, re-read the artifact and regenerate fragments against the current
projection. Retrying stale fragments is intentionally rejected.

## Skill

The bundled `sosein-staging` skill is the operational guide loaded by agents. Keep
it focused on high-signal workflow rules: how to locate artifacts, when to use
find versus outline, how to choose edit operations, and how to recover from stale
or ambiguous edits.
