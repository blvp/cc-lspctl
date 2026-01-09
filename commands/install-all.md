---
description: Install all configured LSP servers (binaries and plugins)
argument-hint: [--skip-installed] [--dry-run]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# lspctl: Install All Servers

Install all LSP servers defined in your `lsp-config.lua`.

## Arguments

$ARGUMENTS

- `--skip-installed`: Skip servers that already have binaries installed
- `--dry-run`: Show what would be installed without actually installing

## Process

1. **Find and parse config** from `.claude/lsp-config.lua` or `~/.claude/lsp-config.lua`

2. **Load server registry** from `${CLAUDE_PLUGIN_ROOT}/registry/servers.json`

3. **Check each server status**:
   - Binary installed?
   - Claude Code plugin installed?
   - In generated marketplace?

4. **Generate installation plan**:
   | Server | Binary Status | Action |
   |--------|---------------|--------|
   | lua_ls | Missing | Install via brew |
   | pylsp | Installed | Install plugin only |
   | pyright | Installed | Already complete |

5. **Ask for confirmation** before proceeding

6. **Execute installations**:
   - Install missing binaries
   - Install Claude Code plugins for each server

7. **Report results**:
   - Successfully installed
   - Failed installations
   - Skipped (already installed)

## Prerequisites

Before running this command:
1. Create `~/.claude/lsp-config.lua` with your desired servers
2. Run `/lspctl:sync` to generate the marketplace

## Example

```
/lspctl:install-all
/lspctl:install-all --skip-installed
/lspctl:install-all --dry-run
```

## Installation Order

Servers are installed in the order they appear in `ensure_installed`.

For each server:
1. Check if binary is available
2. Install binary if needed (with user confirmation)
3. Install Claude Code plugin from generated marketplace
