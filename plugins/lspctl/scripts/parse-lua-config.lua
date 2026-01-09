#!/usr/bin/env lua
-- parse-lua-config.lua
-- Parses LSP configuration from Lua file and outputs JSON
-- Usage: lua parse-lua-config.lua <config-path>

-- Minimal JSON encoder for Lua tables
local function encode_json(obj, indent)
    indent = indent or 0
    local spaces = string.rep("  ", indent)
    local t = type(obj)

    if t == "nil" then
        return "null"
    elseif t == "boolean" then
        return obj and "true" or "false"
    elseif t == "number" then
        if obj ~= obj then  -- NaN check
            return "null"
        elseif obj == math.huge or obj == -math.huge then
            return "null"
        end
        return tostring(obj)
    elseif t == "string" then
        -- Escape special characters
        local escaped = obj:gsub('\\', '\\\\')
                           :gsub('"', '\\"')
                           :gsub('\n', '\\n')
                           :gsub('\r', '\\r')
                           :gsub('\t', '\\t')
        return '"' .. escaped .. '"'
    elseif t == "table" then
        -- Check if array (sequential integer keys starting from 1)
        local is_array = true
        local max_index = 0
        for k, _ in pairs(obj) do
            if type(k) ~= "number" or k <= 0 or math.floor(k) ~= k then
                is_array = false
                break
            end
            if k > max_index then max_index = k end
        end
        if is_array and max_index > 0 then
            -- Verify no gaps
            for i = 1, max_index do
                if obj[i] == nil then
                    is_array = false
                    break
                end
            end
        end
        if max_index == 0 then is_array = false end

        local items = {}

        if is_array then
            for i = 1, max_index do
                local v = obj[i]
                if type(v) ~= "function" then
                    table.insert(items, encode_json(v, indent + 1))
                end
            end
            if #items == 0 then return "[]" end
            return "[\n" .. spaces .. "  " .. table.concat(items, ",\n" .. spaces .. "  ") .. "\n" .. spaces .. "]"
        else
            -- Object
            local keys = {}
            for k in pairs(obj) do
                if type(k) == "string" and type(obj[k]) ~= "function" then
                    table.insert(keys, k)
                end
            end
            table.sort(keys)

            for _, k in ipairs(keys) do
                local v = obj[k]
                local key = '"' .. k:gsub('\\', '\\\\'):gsub('"', '\\"') .. '"'
                local val = encode_json(v, indent + 1)
                table.insert(items, spaces .. "  " .. key .. ": " .. val)
            end
            if #items == 0 then return "{}" end
            return "{\n" .. table.concat(items, ",\n") .. "\n" .. spaces .. "}"
        end
    elseif t == "function" then
        return "null"
    end
    return "null"
end

-- Mock vim global for Neovim config compatibility
local function create_vim_mock()
    local vim_mock = {
        env = {
            VIMRUNTIME = "/usr/share/nvim/runtime"
        },
        fn = {
            stdpath = function(what)
                if what == "data" then return os.getenv("HOME") .. "/.local/share/nvim" end
                if what == "config" then return os.getenv("HOME") .. "/.config/nvim" end
                return ""
            end,
            expand = function(path) return path end,
            has = function() return 0 end,
        },
        opt = setmetatable({}, {
            __index = function() return { get = function() return {} end } end
        }),
        g = {},
        o = {},
        bo = {},
        wo = {},
        api = {
            nvim_get_runtime_file = function() return {} end,
            nvim_create_autocmd = function() end,
            nvim_create_augroup = function() return 0 end,
            nvim_buf_get_name = function() return "" end,
            nvim_get_current_buf = function() return 0 end,
        },
        lsp = {
            protocol = {
                make_client_capabilities = function() return {} end
            },
            config = function() end,
            enable = function() end,
        },
        diagnostic = {
            config = function() end,
        },
        keymap = {
            set = function() end,
        },
        cmd = setmetatable({}, {
            __call = function() end,
            __index = function() return function() end end
        }),
        notify = function() end,
        schedule = function(fn) fn() end,
        tbl_deep_extend = function(behavior, ...)
            local result = {}
            for _, tbl in ipairs({...}) do
                if type(tbl) == "table" then
                    for k, v in pairs(tbl) do
                        if type(v) == "table" and type(result[k]) == "table" then
                            result[k] = vim_mock.tbl_deep_extend(behavior, result[k], v)
                        else
                            result[k] = v
                        end
                    end
                end
            end
            return result
        end,
        tbl_extend = function(behavior, ...)
            local result = {}
            for _, tbl in ipairs({...}) do
                if type(tbl) == "table" then
                    for k, v in pairs(tbl) do
                        result[k] = v
                    end
                end
            end
            return result
        end,
        tbl_keys = function(t)
            local keys = {}
            for k in pairs(t) do table.insert(keys, k) end
            return keys
        end,
        tbl_contains = function(t, val)
            for _, v in pairs(t) do
                if v == val then return true end
            end
            return false
        end,
        inspect = function(t) return tostring(t) end,
        log = {
            levels = { DEBUG = 1, INFO = 2, WARN = 3, ERROR = 4 }
        },
    }
    return vim_mock
end

-- Mock require for common Neovim plugins
local original_require = require
local mock_modules = {
    ["mason"] = { setup = function() end },
    ["mason-lspconfig"] = { setup = function() end },
    ["lspconfig"] = setmetatable({}, {
        __index = function(_, server_name)
            return { setup = function() end }
        end
    }),
    ["cmp_nvim_lsp"] = {
        default_capabilities = function() return {} end
    },
    ["lazy"] = { setup = function() end },
}

local function mock_require(module_name)
    if mock_modules[module_name] then
        return mock_modules[module_name]
    end
    -- Try to load normally, but don't fail
    local ok, result = pcall(original_require, module_name)
    if ok then return result end
    -- Return empty table as fallback
    return {}
end

-- Main function
local function main()
    local config_path = arg[1]
    if not config_path then
        io.stderr:write("Usage: lua parse-lua-config.lua <config-path>\n")
        os.exit(1)
    end

    -- Check file exists
    local f = io.open(config_path, "r")
    if not f then
        io.stderr:write("Error: Cannot open file: " .. config_path .. "\n")
        os.exit(1)
    end
    f:close()

    -- Set up mocks
    _G.vim = create_vim_mock()
    _G.require = mock_require

    -- Load config
    local ok, config = pcall(dofile, config_path)
    if not ok then
        io.stderr:write("Error loading config: " .. tostring(config) .. "\n")
        os.exit(1)
    end

    -- Validate config structure
    if type(config) ~= "table" then
        io.stderr:write("Error: Config must return a table\n")
        os.exit(1)
    end

    -- Extract LSP-relevant configuration
    local result = {
        ensure_installed = {},
        servers = {}
    }

    -- Handle ensure_installed
    if type(config.ensure_installed) == "table" then
        for _, server in ipairs(config.ensure_installed) do
            if type(server) == "string" then
                table.insert(result.ensure_installed, server)
            end
        end
    end

    -- Handle servers configuration
    if type(config.servers) == "table" then
        for server_name, server_config in pairs(config.servers) do
            if type(server_name) == "string" and type(server_config) == "table" then
                result.servers[server_name] = server_config
            end
        end
    end

    -- Output JSON
    print(encode_json(result))
end

main()
