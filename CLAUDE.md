# cc-lspctl - Claude Code LSP Controller

## Project Status Summary

**Status**: MVP Complete - Ready for testing

### Completed
- [x] Marketplace structure with manifest
- [x] Server registry (10 LSP servers)
- [x] Lua config parser (Neovim-compatible)
- [x] Marketplace generator (Python)
- [x] Slash commands: sync, list, install, install-all
- [x] LSP config skill for guidance
- [x] Auto-registration of marketplace
- [x] Auto-installation of plugins

### To Do
- [ ] Add more LSP servers to registry
- [ ] Add SessionStart hook for missing binary warnings
- [ ] Test with real LSP servers in Claude Code
- [ ] Add support for importing Neovim config directly
- [ ] Add `--keep-binary` flag support in uninstall command


## Project Overview

A Claude Code marketplace that provides Mason-like LSP server management. Users define LSP servers in a Neovim-compatible Lua config file, and the plugin generates a Claude Code marketplace with individual LSP plugins.

**Key Concept**: Claude Code requires LSP configurations to be inside plugin marketplaces. This marketplace contains the `lspctl` plugin which acts as a **generator** that creates additional marketplaces from user configuration.


## Architecture

```
User Config (lsp-config.lua)
         │
         ▼
┌─────────────────────┐
│  /lspctl:sync  │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐     ┌──────────────────┐
│ parse-lua-config.lua│────▶│ Parsed JSON      │
└─────────────────────┘     └──────────────────┘
                                    │
                                    ▼
                            ┌──────────────────┐
                            │generate-marketplace│
                            │      .py         │
                            └──────────────────┘
                                    │
                                    ▼
                            ┌──────────────────┐
                            │ Generated        │
                            │ Marketplace      │
                            │  └─plugins/      │
                            │    └─lsp-*/      │
                            └──────────────────┘
                                    │
                                    ▼
                            ┌──────────────────┐
                            │claude plugin     │
                            │marketplace add   │
                            └──────────────────┘
                                    │
                                    ▼
                            ┌──────────────────┐
                            │claude plugin     │
                            │install (each)    │
                            └──────────────────┘
```


## File Structure

```
cc-lspctl/
├── .claude-plugin/
│   └── marketplace.json         # Marketplace manifest
├── plugins/
│   └── lspctl/                  # Main lspctl plugin
│       ├── .claude-plugin/
│       │   └── plugin.json      # Plugin manifest
│       ├── commands/
│       │   ├── sync.md          # Main command - generates & installs everything
│       │   ├── list.md          # List available/installed servers
│       │   ├── install.md       # Install single server
│       │   ├── install-all.md   # Install all configured servers
│       │   └── uninstall.md     # Uninstall server(s)
│       ├── scripts/
│       │   ├── parse-lua-config.lua     # Parses Lua config, outputs JSON
│       │   ├── generate-marketplace.py  # Generates marketplace structure
│       │   └── check-binaries.sh        # Checks which LSP binaries are installed
│       ├── registry/
│       │   └── servers.json     # Server definitions (lspconfig name → Claude Code format)
│       └── skills/
│           └── lsp-config/
│               └── SKILL.md     # LSP configuration guidance skill
├── tests/                       # Test suite
├── CLAUDE.md                    # This file
└── README.md                    # User documentation
```


## Commands

| Command | Description |
|---------|-------------|
| `/lspctl:sync` | Generate marketplace, register it, install all plugins |
| `/lspctl:list` | Show available servers and their status |
| `/lspctl:install <server>` | Install binary + plugin for a server |
| `/lspctl:install-all` | Install all configured servers |
| `/lspctl:uninstall <server>` | Uninstall server plugin and optionally binary |
| `/lspctl:uninstall --all` | Remove all plugins and deregister marketplace |


## User Flow

### Quick Start
```
1. Create ~/.claude/lsp-config.lua
2. Run /lspctl:sync
3. Reload Claude Code
```

### Detailed Flow
1. User creates `~/.claude/lsp-config.lua` (or `.claude/lsp-config.lua` in project)
2. User runs `/lspctl:sync`
3. Plugin parses Lua config → JSON
4. Plugin generates marketplace at `~/.claude/generated-lsp-marketplace/`
5. Plugin runs `claude plugin marketplace add <path>`
6. Plugin runs `claude plugin install <plugin>@generated-lsp` for each plugin
7. User reloads Claude Code
8. LSP servers are active


## Configuration Format

File: `~/.claude/lsp-config.lua` or `.claude/lsp-config.lua`

```lua
return {
  ensure_installed = {
    "lua_ls",
    "pylsp",
    "pyright",
    "ts_ls",
    "rust_analyzer"
  },
  servers = {
    lua_ls = {
      settings = {
        Lua = {
          diagnostics = { globals = { "vim" } },
          runtime = { version = "LuaJIT" }
        }
      }
    },
    pylsp = {
      settings = {
        pylsp = {
          plugins = {
            ruff = { enabled = true, lineLength = 80 },
            isort = { enabled = true, profile = "black" }
          }
        }
      }
    },
    rust_analyzer = {
      settings = {
        ["rust-analyzer"] = {
          checkOnSave = { command = "clippy" }
        }
      }
    }
  }
}
```


## Server Registry

Located at `plugins/lspctl/registry/servers.json`. Maps lspconfig names to Claude Code LSP format.

### Supported Servers

| Server | Language | Binary | Install Methods |
|--------|----------|--------|-----------------|
| lua_ls | Lua | lua-language-server | brew, npm |
| pylsp | Python | pylsp | uv, pipx, pip |
| pyright | Python | pyright-langserver | npm, pip |
| ts_ls | TypeScript/JS | typescript-language-server | npm |
| rust_analyzer | Rust | rust-analyzer | rustup, brew |
| gopls | Go | gopls | go |
| clangd | C/C++ | clangd | brew, apt |
| jsonls | JSON | vscode-json-language-server | npm |
| yamlls | YAML | yaml-language-server | npm |
| bashls | Bash | bash-language-server | npm |


## Generated Marketplace Structure

When `/lspctl:sync` runs, it creates:

```
~/.claude/generated-lsp-marketplace/
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

### marketplace.json Format
```json
{
  "name": "generated-lsp",
  "owner": { "name": "lspctl" },
  "metadata": {
    "description": "Auto-generated LSP plugins from lsp-config.lua",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "lsp-python-pylsp",
      "source": "./plugins/lsp-python-pylsp",
      "description": "Python LSP Server (pylsp)"
    }
  ]
}
```

### .lsp.json Format (per plugin)
```json
{
  "python": {
    "command": "pylsp",
    "extensionToLanguage": {
      ".py": "python",
      ".pyi": "python"
    },
    "settings": {
      "pylsp": {
        "plugins": {
          "ruff": { "enabled": true }
        }
      }
    }
  }
}
```


## Key Scripts

### parse-lua-config.lua
- Parses Neovim-compatible Lua config files
- Mocks `vim` global for compatibility
- Outputs JSON to stdout
- Usage: `lua parse-lua-config.lua <config-path>`

### generate-marketplace.py
- Takes parsed config JSON and registry
- Generates complete marketplace structure
- Checks binary availability
- Updates settings.json with marketplace registration
- Usage: `python3 generate-marketplace.py --config <json> --registry <registry> --scope user|project|local`


## Settings Integration

The plugin registers the generated marketplace in Claude Code settings:

```json
{
  "extraKnownMarketplaces": {
    "generated-lsp": {
      "source": {
        "source": "directory",
        "path": "/Users/user/.claude/generated-lsp-marketplace"
      }
    }
  }
}
```


## Requirements

- **Lua** interpreter (lua or luajit) - for config parsing
- **Python 3.8+** - for marketplace generation
- **jq** (optional) - for check-binaries.sh script


## Development

### Testing the Plugin
```bash
# Load plugin for testing
claude --plugin-dir /path/to/cc-lspctl

# Validate plugin structure
claude plugin validate /path/to/cc-lspctl
```

### Testing Scripts Directly
```bash
# Test Lua parser
lua plugins/lspctl/scripts/parse-lua-config.lua ~/.claude/lsp-config.lua

# Test marketplace generator
python3 plugins/lspctl/scripts/generate-marketplace.py \
  --config <(lua plugins/lspctl/scripts/parse-lua-config.lua ~/.claude/lsp-config.lua) \
  --registry plugins/lspctl/registry/servers.json \
  --scope user
```


## Troubleshooting

### Marketplace not found
Run: `claude plugin marketplace add ~/.claude/generated-lsp-marketplace`

### LSP not starting after install
Reload Claude Code (restart the session)

### Check if binary is installed
```bash
which pylsp
which rust-analyzer
```

### Enable LSP debug logging
```bash
claude --enable-lsp-logging
```
Logs written to `~/.claude/debug/`
