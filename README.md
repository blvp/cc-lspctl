# cc-lspctl

Mason-like LSP server manager for Claude Code. Define your LSP servers in a Neovim-compatible Lua config and auto-generate Claude Code LSP plugins.

## Features

- **Declarative LSP Configuration**: Use `lsp-config.lua` to define which LSP servers you want
- **Neovim Compatible**: Config format works with Mason/lspconfig patterns
- **Marketplace Generation**: Automatically generates a Claude Code marketplace with individual LSP plugins
- **Binary Management**: Detects missing binaries and offers installation via brew/npm/pip/cargo/etc.
- **Multi-Scope Support**: User-level or project-level configurations

## Installation

```bash
# Clone the plugin
git clone https://github.com/blvp/cc-lspctl.git ~/.claude/plugins/lspctl

# Or add to Claude Code
/plugin marketplace add https://github.com/blvp/cc-lspctl
/plugin install lspctl
```

## Quick Start

### 1. Create Config File

Create `~/.claude/lsp-config.lua`:

```lua
return {
  ensure_installed = {
    "lua_ls",
    "pylsp",
    "rust_analyzer",
    "ts_ls"
  },
  servers = {
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

### 2. Generate Marketplace

```
/lspctl:sync
```

### 3. Install Plugins

```
/plugin install lsp-python-pylsp@generated-lsp
```

Or install all at once:
```
/lspctl:install-all
```

## Commands

| Command | Description |
|---------|-------------|
| `/lspctl:list` | Show available servers and their status |
| `/lspctl:sync` | Generate marketplace from config |
| `/lspctl:install <server>` | Install binary + plugin for a server |
| `/lspctl:install-all` | Install all configured servers |
| `/lspctl:uninstall <server>` | Uninstall server plugin and optionally binary |
| `/lspctl:uninstall --all` | Remove all plugins and deregister marketplace |

## Configuration

### Config File Locations

1. Project: `.claude/lsp-config.lua`
2. User: `~/.claude/lsp-config.lua`

### Config Format

```lua
return {
  -- List of servers to install (lspconfig names)
  ensure_installed = {
    "lua_ls",
    "pylsp",
    "pyright",
    "ts_ls",
    "rust_analyzer"
  },

  -- Per-server settings (optional)
  servers = {
    server_name = {
      settings = {
        -- Server-specific settings
      }
    }
  }
}
```

## Supported Servers

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

## Architecture

This plugin generates a Claude Code marketplace:

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

Each generated plugin contains a `.lsp.json` that Claude Code uses to configure the LSP server.

## Requirements

- Lua interpreter (lua or luajit) for config parsing
- Python 3.8+ for marketplace generation
- jq (optional, for binary checking scripts)

## Troubleshooting

### Check Server Status

```
/lspctl:list
```

### Enable LSP Debug Logging

```bash
claude --enable-lsp-logging
```

Logs are written to `~/.claude/debug/`.

### Validate Config Syntax

```bash
lua -c ~/.claude/lsp-config.lua
```

### Test Config Parsing

```bash
lua scripts/parse-lua-config.lua ~/.claude/lsp-config.lua
```

## License

MIT

## Credits

Inspired by [Mason.nvim](https://github.com/mason-org/mason.nvim) and [mason-lspconfig.nvim](https://github.com/mason-org/mason-lspconfig.nvim).
