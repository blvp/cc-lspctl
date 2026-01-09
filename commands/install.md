---
description: Install LSP server binary and Claude Code plugin
argument-hint: <server-name> [--method npm|pip|brew|cargo|rustup|uv]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# LSP Install: Install Server

Install an LSP server binary and its Claude Code plugin.

## Arguments

$ARGUMENTS

- `<server-name>`: The lspconfig name of the server (e.g., lua_ls, pylsp, rust_analyzer)
- `--method`: Preferred package manager (optional, auto-detected if not specified)

## Process

1. **Load server registry** from `${CLAUDE_PLUGIN_ROOT}/registry/servers.json`

2. **Validate server name** - check if it exists in the registry

3. **Check if binary already installed** using `which <command>`

4. **If binary missing**:
   - Show available installation methods from registry
   - Detect available package managers on system
   - Recommend the best method
   - Ask user for confirmation before running install command

5. **Install binary** with the selected method:
   ```bash
   # Example for pyright
   npm install -g pyright
   ```

6. **Verify installation** - run `which <command>` again

7. **Check if marketplace exists**:
   - If not, suggest running `/lsp-install:sync` first
   - If yes, install the plugin: `/plugin install <plugin-name>@generated-lsp`

## Available Servers

From the registry, these servers can be installed:

| Server | Command | Package Managers |
|--------|---------|------------------|
| lua_ls | lua-language-server | brew, npm |
| pylsp | pylsp | uv, pipx, pip |
| pyright | pyright-langserver | npm, pip |
| ts_ls | typescript-language-server | npm |
| rust_analyzer | rust-analyzer | rustup, brew |
| gopls | gopls | go |
| clangd | clangd | brew, apt |
| jsonls | vscode-json-language-server | npm |
| yamlls | yaml-language-server | npm |
| bashls | bash-language-server | npm |

## Example Usage

```
/lsp-install:install pyright
/lsp-install:install pylsp --method uv
/lsp-install:install rust_analyzer --method rustup
```

## Notes

- Always verify the install command before executing
- Some package managers may require sudo (apt)
- For uv/pipx, the binary is added to a tools directory that should be in PATH
