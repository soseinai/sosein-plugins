# Sosein Plugins

Official plugins for connecting Codex and Claude Code to Sosein production and
staging environments.

The `sosein` plugin connects agents to the production Sosein MCP server. It
supports OAuth sign-in and lets an agent search, read, create, and edit Sosein's
artifacts using the signed-in user's existing Sosein permissions.

## Install in Codex

```sh
codex plugin marketplace add soseinai/sosein-plugins
codex plugin add sosein@sosein
```

Install the staging plugin when you explicitly want to work with non-production
Sosein data:

```sh
codex plugin add sosein-staging@sosein
```

Start a new Codex task after installation. Sosein will ask you to sign in when
the MCP connection is first used.

To fetch an updated marketplace snapshot and reinstall the latest plugin:

```sh
codex plugin marketplace upgrade sosein
codex plugin add sosein@sosein
```

## Install in Claude Code

```sh
claude plugin marketplace add soseinai/sosein-plugins
claude plugin install sosein@sosein
```

Install the staging plugin when you explicitly want to work with non-production
Sosein data:

```sh
claude plugin install sosein-staging@sosein
```

Run `/reload-plugins` or restart Claude Code after installation. Sosein will ask
you to sign in when the MCP connection is first used.

To update later:

```sh
claude plugin marketplace update sosein
claude plugin update sosein@sosein
```

## Capabilities and access

The plugin can:

- inspect the delegated profile, account context, and workspace destinations;
- search documents, notes, records, and events;
- read artifacts, selected blocks, and structured objects;
- create documents, notes, or records privately or in a workspace, from native
  agent Markdown or source Markdown;
- edit text, block structure, and object fields with current-content checks; and
- read and create reviews, comments, and suggestions.

Each MCP identity is delegated from the signed-in human user in its respective
environment. Installing either plugin does not grant access to artifacts the
user cannot already access in that Sosein environment.

See [`plugins/sosein/README.md`](plugins/sosein/README.md) for the complete agent
surface and editing contract.

## Maintaining MCP Alignment

The plugin guidance is aligned with the 26-tool catalog in Sosein Cloud commit
`82fb2e66c` (2026-09-02), including the format-v5 block surface. This is a
source-contract baseline, not a claim that both hosted environments have
deployed that revision. The connected server's tool schemas and delegated
scopes determine what is available.

When the server changes, compare its `src/mcp/mod.rs` tool definitions and
`src/mcp/tools/reviews/mod.rs` definitions in the Cloud server crate with both
plugins' skills and README tables. Keep the two workflows identical except for
environment routing. Update both Codex and Claude package versions together.

## Repository contents

This public repository contains the production and staging Sosein plugins. The
staging plugin is intended only for explicit testing and non-production work.
Internal engineering plugins are not distributed here.

Sosein is proprietary software. The plugin package is published here for use
with Codex and Claude Code; no additional license is granted beyond that use.
