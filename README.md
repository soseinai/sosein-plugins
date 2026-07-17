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

- inspect the delegated Sosein profile and account context;
- search and read Sosein's artifacts;
- find text and inspect document outlines;
- create documents and notes; and
- edit existing artifacts with sequence-checked structured operations.

Each MCP identity is delegated from the signed-in human user in its respective
environment. Installing either plugin does not grant access to artifacts the
user cannot already access in that Sosein environment.

See [`plugins/sosein/README.md`](plugins/sosein/README.md) for the complete agent
surface and editing contract.

## Repository contents

This public repository contains the production and staging Sosein plugins. The
staging plugin is intended only for explicit testing and non-production work.
Internal engineering plugins are not distributed here.

Sosein is proprietary software. The plugin package is published here for use
with Codex and Claude Code; no additional license is granted beyond that use.
