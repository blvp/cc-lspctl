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
