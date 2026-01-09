---
description: Generate LSP marketplace from your lsp-config.lua file
argument-hint: [--scope user|project|local] [--config <path>]
allowed-tools: [Bash, Read, Write, Glob, AskUserQuestion, Skill]
---

# lspctl: Sync Configuration

Generate a Claude Code marketplace with LSP plugins from your configuration file.

## Arguments

$ARGUMENTS

- `--scope`: Where to create the marketplace (user/project/local). If not specified, will prompt.
- `--config`: Path to custom config file. Default: `.claude/lsp-config.lua` or `~/.claude/lsp-config.lua`

## Process

1. **Locate config file** (in order of priority):
   - Custom path from `--config` argument
   - `.claude/lsp-config.lua` in current project
   - `~/.claude/lsp-config.lua` for user-level config

2. **Parse configuration** using:
   ```bash
   lua ${CLAUDE_PLUGIN_ROOT}/scripts/parse-lua-config.lua <config-path>
   ```

3. **Prompt for scope** if not specified:
   - **user**: `~/.claude/generated-lsp-marketplace/` - personal, applies everywhere
   - **project**: `.claude/generated-lsp-marketplace/` - shareable via git
   - **local**: `.claude/generated-lsp-marketplace/` with local settings

4. **Run marketplace generator**:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-marketplace.py \
     --config <parsed-config.json> \
     --registry ${CLAUDE_PLUGIN_ROOT}/registry/servers.json \
     --scope <scope>
   ```

5. **Register/Update marketplace** - Run this command:
   ```bash
   claude plugin marketplace add <marketplace-path>
   ```

6. **Auto-install all generated plugins** - For each plugin in the generated marketplace:
   ```bash
   claude plugin install <plugin-name>@generated-lsp
   ```
   Run this for every plugin that was generated (e.g., lsp-python-pylsp, lsp-typescript, etc.)

7. **Report results**:
   - List installed plugins
   - Show missing binaries with install suggestions (user needs to install these separately)

8. **Final instruction to user**:
   - Tell user: "All LSP plugins have been installed. **RELOAD Claude Code** (restart the session) for LSP servers to activate."
   - If there are missing binaries, tell user which commands to run to install them

## Expected Config Format

Your `lsp-config.lua` should look like:

```lua
return {
  ensure_installed = {
    "lua_ls",
    "pylsp",
    "ts_ls",
    "rust_analyzer"
  },
  servers = {
    lua_ls = {
      settings = {
        Lua = {
          diagnostics = { globals = { "vim" } }
        }
      }
    },
    pylsp = {
      settings = {
        pylsp = {
          plugins = {
            ruff = { enabled = true }
          }
        }
      }
    }
  }
}
```

## Generated Output

Creates marketplace structure:
```
generated-lsp-marketplace/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    ├── lsp-lua/
    │   ├── .claude-plugin/plugin.json
    │   └── .lsp.json
    ├── lsp-python-pylsp/
    │   ├── .claude-plugin/plugin.json
    │   └── .lsp.json
    └── ...
```

## After Sync

The sync command automatically:
1. Generates the marketplace with all configured LSP plugins
2. Registers the marketplace with Claude Code
3. Installs all generated plugins

**You just need to RELOAD Claude Code** (restart the session) for the LSP servers to activate.

If any LSP binaries are missing, install them using the suggested commands (e.g., `npm install -g pyright`).
