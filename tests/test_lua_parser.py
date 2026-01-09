"""Tests for the Lua config parser."""

import json
import subprocess
from pathlib import Path

import pytest


def parse_lua_config(lua_parser_script: Path, config_path: Path) -> dict:
    """Run the Lua parser and return parsed JSON."""
    result = subprocess.run(
        ["lua", str(lua_parser_script), str(config_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Parser failed: {result.stderr}")
    return json.loads(result.stdout)


class TestLuaParserBasics:
    """Basic parser functionality tests."""

    def test_parse_minimal_config(self, lua_parser_script, minimal_config):
        """Test parsing a minimal config with one server."""
        result = parse_lua_config(lua_parser_script, minimal_config)

        assert "ensure_installed" in result
        assert "servers" in result
        assert result["ensure_installed"] == ["pylsp"]
        assert result["servers"] == {}

    def test_parse_full_config_with_settings(self, lua_parser_script, full_config):
        """Test parsing a full config with multiple servers and settings."""
        result = parse_lua_config(lua_parser_script, full_config)

        assert "ensure_installed" in result
        assert len(result["ensure_installed"]) == 5
        assert "lua_ls" in result["ensure_installed"]
        assert "pylsp" in result["ensure_installed"]
        assert "rust_analyzer" in result["ensure_installed"]

        # Check server settings
        assert "servers" in result
        assert "lua_ls" in result["servers"]
        assert "pylsp" in result["servers"]
        assert "rust_analyzer" in result["servers"]

        # Check nested settings
        lua_settings = result["servers"]["lua_ls"]["settings"]
        assert lua_settings["Lua"]["diagnostics"]["globals"] == ["vim"]
        assert lua_settings["Lua"]["runtime"]["version"] == "LuaJIT"

        pylsp_settings = result["servers"]["pylsp"]["settings"]
        assert pylsp_settings["pylsp"]["plugins"]["ruff"]["enabled"] is True
        assert pylsp_settings["pylsp"]["plugins"]["ruff"]["lineLength"] == 80

    def test_parse_empty_ensure_installed(self, lua_parser_script, empty_config):
        """Test parsing a config with empty ensure_installed list."""
        result = parse_lua_config(lua_parser_script, empty_config)

        # Empty Lua tables serialize as {} not [] - this is expected
        assert result["ensure_installed"] == {} or result["ensure_installed"] == []
        assert result["servers"] == {}


class TestLuaParserErrors:
    """Error handling tests for the Lua parser."""

    def test_parse_invalid_syntax(self, lua_parser_script, invalid_config):
        """Test that invalid Lua syntax returns non-zero exit code."""
        result = subprocess.run(
            ["lua", str(lua_parser_script), str(invalid_config)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Error" in result.stderr

    def test_parse_missing_file(self, lua_parser_script, temp_dir):
        """Test handling of missing config file."""
        nonexistent = temp_dir / "nonexistent.lua"
        result = subprocess.run(
            ["lua", str(lua_parser_script), str(nonexistent)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Cannot open file" in result.stderr

    def test_parse_no_arguments(self, lua_parser_script):
        """Test that parser requires config path argument."""
        result = subprocess.run(
            ["lua", str(lua_parser_script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "Usage:" in result.stderr


class TestLuaParserVimMock:
    """Tests for vim global mock compatibility."""

    def test_vim_global_mock(self, lua_parser_script, temp_dir):
        """Test that vim.xxx references don't crash the parser."""
        # Create a config that uses vim globals
        config_with_vim = temp_dir / "vim-config.lua"
        config_with_vim.write_text("""
-- Config that references vim
local _ = vim.fn.stdpath("data")
local _ = vim.g
local _ = vim.tbl_deep_extend("force", {}, {})

return {
    ensure_installed = {
        "pylsp"
    }
}
""")
        result = parse_lua_config(lua_parser_script, config_with_vim)
        assert result["ensure_installed"] == ["pylsp"]

    def test_require_lspconfig_mock(self, lua_parser_script, temp_dir):
        """Test that require('lspconfig') doesn't crash."""
        config_with_require = temp_dir / "require-config.lua"
        config_with_require.write_text("""
-- Config that requires lspconfig
local lspconfig = require('lspconfig')

return {
    ensure_installed = {
        "ts_ls"
    }
}
""")
        result = parse_lua_config(lua_parser_script, config_with_require)
        assert result["ensure_installed"] == ["ts_ls"]


class TestLuaParserEdgeCases:
    """Edge case tests for the Lua parser."""

    def test_unknown_servers_passed_through(
        self, lua_parser_script, unknown_servers_config
    ):
        """Test that unknown server names are still included in output."""
        result = parse_lua_config(lua_parser_script, unknown_servers_config)

        assert "unknown_server_1" in result["ensure_installed"]
        assert "unknown_server_2" in result["ensure_installed"]
        assert "pylsp" in result["ensure_installed"]

    def test_config_with_only_servers_no_ensure_installed(
        self, lua_parser_script, temp_dir
    ):
        """Test config that has servers but no ensure_installed."""
        config = temp_dir / "servers-only.lua"
        config.write_text("""
return {
    servers = {
        pylsp = {
            settings = {}
        }
    }
}
""")
        result = parse_lua_config(lua_parser_script, config)
        # Empty Lua tables serialize as {} not [] - this is expected
        assert result["ensure_installed"] == {} or result["ensure_installed"] == []
        assert "pylsp" in result["servers"]

    def test_special_characters_in_settings(self, lua_parser_script, temp_dir):
        """Test that special characters in settings are escaped properly in JSON."""
        config = temp_dir / "special-chars.lua"
        config.write_text('''
return {
    ensure_installed = {"pylsp"},
    servers = {
        pylsp = {
            settings = {
                pylsp = {
                    configurationSources = {"pycodestyle"},
                    format = {
                        quote = "'"
                    }
                }
            }
        }
    }
}
''')
        result = parse_lua_config(lua_parser_script, config)
        # Should not raise JSON decode error
        assert result["servers"]["pylsp"]["settings"]["pylsp"]["format"]["quote"] == "'"
