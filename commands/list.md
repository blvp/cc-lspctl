---
description: List available and configured LSP servers with installation status
allowed-tools: [Bash, Read]
---

# LSP Install: List Servers

Display available LSP servers from the registry and check their installation status.

## Process

1. **Load server registry** from `${CLAUDE_PLUGIN_ROOT}/registry/servers.json`

2. **Find user config** (check in order):
   - `.claude/lsp-config.lua` (project-level)
   - `~/.claude/lsp-config.lua` (user-level)

3. **Parse config** if found using `${CLAUDE_PLUGIN_ROOT}/scripts/parse-lua-config.lua`

4. **Check binary availability** for each server using `which <command>`

5. **Display results** in a table format:

| Server | Binary | Status | Configured |
|--------|--------|--------|------------|
| lua_ls | lua-language-server | Installed | Yes |
| pylsp | pylsp | Missing | Yes |
| pyright | pyright-langserver | Installed | No |

## Output

After displaying the table, show:
- Config file location (if found)
- Commands to run:
  - `/lsp-install:sync` to generate marketplace
  - `/lsp-install:install <server>` to install a specific server

## Available Servers in Registry

The following servers are available in the registry:

- **lua_ls** - Lua Language Server
- **pylsp** - Python LSP Server (with ruff/isort support)
- **pyright** - Pyright Python static type checker
- **ts_ls** - TypeScript Language Server
- **rust_analyzer** - Rust Analyzer
- **gopls** - Go Language Server
- **clangd** - C/C++ Language Server
- **jsonls** - JSON Language Server
- **yamlls** - YAML Language Server
- **bashls** - Bash Language Server
