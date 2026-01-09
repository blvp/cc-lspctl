---
description: Uninstall LSP server(s) or remove entire marketplace
argument-hint: <server-name> | --all [--keep-binary] [--scope user|project|local]
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# lspctl: Uninstall Server

Uninstall an LSP server plugin from Claude Code and optionally remove its binary.

## Arguments

$ARGUMENTS

- `<server-name>`: The lspconfig name of the server to uninstall (e.g., pylsp, ts_ls)
- `--all`: Remove all LSP plugins and deregister the marketplace entirely
- `--keep-binary`: Skip binary uninstall prompt (default: ask)
- `--scope`: Specify marketplace scope (user/project/local). Auto-detected if not specified.

## Mode 1: Uninstall Single Server

Usage: `/lspctl:uninstall <server-name>`

### Process

1. **Load server registry** from `${CLAUDE_PLUGIN_ROOT}/registry/servers.json`

2. **Validate server name** - check if it exists in the registry

3. **Find marketplace location** (check in order):
   - `.claude/generated-lsp-marketplace` (project)
   - `~/.claude/generated-lsp-marketplace` (user)

   Or use `--scope` to specify directly.

4. **Uninstall Claude Code plugin**:
   ```bash
   claude plugin uninstall <plugin-name>@generated-lsp
   ```

5. **Remove from marketplace** using:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-marketplace.py \
     --remove <server-name> \
     --registry ${CLAUDE_PLUGIN_ROOT}/registry/servers.json \
     --output <marketplace-path>
   ```

6. **Ask about binary** (unless `--keep-binary`):
   - Show available uninstall commands from registry
   - If user wants to uninstall, show the commands to run

7. **Check if marketplace is empty**:
   - If yes, suggest running `/lspctl:uninstall --all` to clean up

8. **Report results**:
   - Plugin uninstalled
   - Remaining plugins in marketplace
   - Binary uninstall commands (if applicable)

## Mode 2: Uninstall All (Full Cleanup)

Usage: `/lspctl:uninstall --all`

### Process

1. **Find marketplace location** (or use `--scope`)

2. **List all plugins** in the marketplace

3. **Uninstall each Claude Code plugin**:
   ```bash
   claude plugin uninstall <plugin-name>@generated-lsp
   ```
   Run for each plugin in the marketplace.

4. **Deregister marketplace**:
   ```bash
   claude plugin marketplace remove generated-lsp
   ```

5. **Remove marketplace files** using:
   ```bash
   python3 ${CLAUDE_PLUGIN_ROOT}/scripts/generate-marketplace.py \
     --deregister \
     --output <marketplace-path> \
     --settings <settings-path>
   ```

6. **Ask about binaries** (unless `--keep-binary`):
   - Show uninstall commands for each server
   - User must run these manually

7. **Final instruction**:
   - Tell user: "All LSP plugins removed. **RELOAD Claude Code** for changes to take effect."

## Available Servers

From the registry, these servers can be uninstalled:

| Server | Plugin Name | Binary |
|--------|-------------|--------|
| lua_ls | lsp-lua | lua-language-server |
| pylsp | lsp-python-pylsp | pylsp |
| pyright | lsp-python-pyright | pyright-langserver |
| ts_ls | lsp-typescript | typescript-language-server |
| rust_analyzer | lsp-rust | rust-analyzer |
| gopls | lsp-go | gopls |
| clangd | lsp-cpp | clangd |
| jsonls | lsp-json | vscode-json-language-server |
| yamlls | lsp-yaml | yaml-language-server |
| bashls | lsp-bash | bash-language-server |

## Example Usage

```
# Uninstall single server
/lspctl:uninstall pylsp
/lspctl:uninstall ts_ls --keep-binary

# Remove everything
/lspctl:uninstall --all
/lspctl:uninstall --all --scope user
```

## Notes

- Uninstalling a plugin does NOT automatically remove the binary
- Binaries are managed by your system's package manager
- After uninstall, reload Claude Code for changes to take effect
- You can re-add servers later by editing lsp-config.lua and running `/lspctl:sync`
