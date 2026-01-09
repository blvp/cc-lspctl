---
name: lsp-config
description: This skill should be used when the user asks about "LSP configuration", "language server setup", "adding LSP to Claude Code", "mason config import", "lspconfig migration", "lsp-install plugin", or discusses Claude Code LSP integration and troubleshooting.
version: 1.0.0
---

# LSP Configuration Skill

Provides guidance for configuring Language Server Protocol (LSP) servers in Claude Code using the lsp-install plugin.

## Overview

The lsp-install plugin enables Mason-like LSP management for Claude Code:
1. Define servers in a Lua config file (compatible with Neovim)
2. Generate a marketplace with individual LSP plugins
3. Install binaries and plugins as needed

## Quick Start

### 1. Create Config File

Create `~/.claude/lsp-config.lua` (user-level) or `.claude/lsp-config.lua` (project-level):

```lua
return {
  ensure_installed = {
    "lua_ls",      -- Lua
    "pylsp",       -- Python (with ruff/isort)
    "pyright",     -- Python (type checking)
    "ts_ls",       -- TypeScript/JavaScript
    "rust_analyzer", -- Rust
    "gopls",       -- Go
  },
  servers = {
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

### 2. Generate Marketplace

```
/lsp-install:sync
```

This creates a marketplace at `~/.claude/generated-lsp-marketplace/` (or project-level).

### 3. Install Plugins

```
/plugin install lsp-python-pylsp@generated-lsp
/plugin install lsp-rust@generated-lsp
```

Or install all:
```
/lsp-install:install-all
```

## Available Commands

| Command | Description |
|---------|-------------|
| `/lsp-install:list` | Show available servers and status |
| `/lsp-install:sync` | Generate marketplace from config |
| `/lsp-install:install <server>` | Install specific server |
| `/lsp-install:install-all` | Install all configured servers |

## Supported LSP Servers

| Server | Language | Binary |
|--------|----------|--------|
| lua_ls | Lua | lua-language-server |
| pylsp | Python | pylsp |
| pyright | Python | pyright-langserver |
| ts_ls | TypeScript/JS | typescript-language-server |
| rust_analyzer | Rust | rust-analyzer |
| gopls | Go | gopls |
| clangd | C/C++ | clangd |
| jsonls | JSON | vscode-json-language-server |
| yamlls | YAML | yaml-language-server |
| bashls | Bash | bash-language-server |

## Server Settings Reference

### Python (pylsp with ruff)

```lua
pylsp = {
  settings = {
    pylsp = {
      plugins = {
        ruff = { enabled = true, lineLength = 80 },
        isort = { enabled = true, profile = "black" },
        pycodestyle = { enabled = false },
        pyflakes = { enabled = false },
        mccabe = { enabled = false }
      }
    }
  }
}
```

### Python (pyright)

```lua
pyright = {
  settings = {
    python = {
      analysis = {
        typeCheckingMode = "basic",  -- "off", "basic", "standard", "strict"
        autoSearchPaths = true,
        useLibraryCodeForTypes = true
      }
    }
  }
}
```

### Lua

```lua
lua_ls = {
  settings = {
    Lua = {
      diagnostics = { globals = { "vim" } },
      runtime = { version = "LuaJIT" },
      workspace = { checkThirdParty = false }
    }
  }
}
```

### Rust

```lua
rust_analyzer = {
  settings = {
    ["rust-analyzer"] = {
      checkOnSave = { command = "clippy" },
      files = { excludeDirs = { ".git", "target" } }
    }
  }
}
```

### TypeScript

```lua
ts_ls = {
  settings = {
    typescript = {
      preferences = {
        quoteStyle = "single"
      }
    }
  }
}
```

## Troubleshooting

### LSP not starting

1. Check if binary is installed:
   ```bash
   which <command>
   ```

2. Run with debug logging:
   ```bash
   claude --enable-lsp-logging
   ```

3. Check logs in `~/.claude/debug/`

### Config not parsing

1. Validate Lua syntax:
   ```bash
   lua -c ~/.claude/lsp-config.lua
   ```

2. Test parser:
   ```bash
   lua ${CLAUDE_PLUGIN_ROOT}/scripts/parse-lua-config.lua ~/.claude/lsp-config.lua
   ```

### Plugin not found

1. Ensure marketplace was generated:
   ```
   /lsp-install:sync
   ```

2. Check marketplace was added to settings:
   ```bash
   cat ~/.claude/settings.json | grep generated-lsp
   ```

## Migrating from Neovim

Your Neovim LSP config uses lspconfig server names (e.g., `lua_ls`, `pylsp`). The lsp-install plugin uses the same naming convention.

To migrate:
1. Copy `ensure_installed` array from your mason-lspconfig setup
2. Copy server settings from your `vim.lsp.config()` calls
3. Run `/lsp-install:sync`
