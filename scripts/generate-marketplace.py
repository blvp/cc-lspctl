#!/usr/bin/env python3
"""
Generate Claude Code marketplace structure from LSP configuration.

This script takes a parsed LSP config (JSON) and server registry,
then generates a complete marketplace with individual LSP plugins.

Usage:
    python3 generate-marketplace.py \
        --config <config.json> \
        --registry <registry.json> \
        --output <output-dir>
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict:
    """Load JSON file."""
    with open(path) as f:
        return json.load(f)


def save_json(path: Path, data: dict, indent: int = 2) -> None:
    """Save JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)
        f.write("\n")


def check_binary(command: str) -> bool:
    """Check if a binary exists in PATH."""
    result = subprocess.run(
        ["which", command],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def generate_plugin_json(server_name: str, registry_entry: dict) -> dict:
    """Generate plugin.json for an LSP server."""
    return {
        "name": registry_entry["pluginName"],
        "description": f"{registry_entry['description']} for Claude Code",
        "version": "1.0.0"
    }


def generate_lsp_json(server_name: str, registry_entry: dict, user_settings: dict) -> dict:
    """Generate .lsp.json for an LSP server."""
    language = registry_entry["language"]

    lsp_config = {
        "command": registry_entry["command"],
        "extensionToLanguage": registry_entry["extensionToLanguage"]
    }

    # Add args if present
    if registry_entry.get("args"):
        lsp_config["args"] = registry_entry["args"]

    # Merge user settings
    if user_settings.get("settings"):
        lsp_config["settings"] = user_settings["settings"]

    return {language: lsp_config}


def generate_marketplace_json(plugins: list[dict]) -> dict:
    """Generate marketplace.json."""
    return {
        "name": "generated-lsp",
        "owner": {
            "name": "lsp-install"
        },
        "metadata": {
            "description": "Auto-generated LSP plugins from lsp-config.lua",
            "version": "1.0.0",
            "pluginRoot": "./plugins"
        },
        "plugins": plugins
    }


def generate_marketplace(
    config: dict,
    registry: dict,
    output_dir: Path
) -> dict:
    """
    Generate complete marketplace structure.

    Returns dict with:
        - generated: list of generated plugin names
        - missing_binaries: dict of server -> install commands
        - unknown_servers: list of servers not in registry
    """
    result = {
        "generated": [],
        "missing_binaries": {},
        "unknown_servers": []
    }

    ensure_installed = config.get("ensure_installed", [])
    servers_config = config.get("servers", {})

    # Clean output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Create directory structure
    plugins_dir = output_dir / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / ".claude-plugin").mkdir(parents=True, exist_ok=True)

    marketplace_plugins = []

    for server_name in ensure_installed:
        if server_name not in registry:
            result["unknown_servers"].append(server_name)
            print(f"Warning: Unknown server '{server_name}' - skipping", file=sys.stderr)
            continue

        registry_entry = registry[server_name]
        plugin_name = registry_entry["pluginName"]
        user_settings = servers_config.get(server_name, {})

        # Check binary availability
        command = registry_entry["command"]
        if not check_binary(command):
            result["missing_binaries"][server_name] = registry_entry.get("installCommands", {})

        # Create plugin directory
        plugin_dir = plugins_dir / plugin_name
        (plugin_dir / ".claude-plugin").mkdir(parents=True, exist_ok=True)

        # Generate plugin.json
        plugin_json = generate_plugin_json(server_name, registry_entry)
        save_json(plugin_dir / ".claude-plugin" / "plugin.json", plugin_json)

        # Generate .lsp.json
        lsp_json = generate_lsp_json(server_name, registry_entry, user_settings)
        save_json(plugin_dir / ".lsp.json", lsp_json)

        # Add to marketplace plugins list
        marketplace_plugins.append({
            "name": plugin_name,
            "source": f"./plugins/{plugin_name}",
            "description": registry_entry["description"],
            "keywords": ["lsp", registry_entry["language"]]
        })

        result["generated"].append(plugin_name)

    # Generate marketplace.json
    marketplace_json = generate_marketplace_json(marketplace_plugins)
    save_json(output_dir / ".claude-plugin" / "marketplace.json", marketplace_json)

    return result


def update_settings(settings_path: Path, marketplace_path: Path) -> None:
    """Add marketplace to Claude Code settings."""
    settings = {}

    if settings_path.exists():
        try:
            settings = load_json(settings_path)
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {settings_path}, creating new", file=sys.stderr)

    # Ensure extraKnownMarketplaces exists
    if "extraKnownMarketplaces" not in settings:
        settings["extraKnownMarketplaces"] = {}

    # Add or update the generated-lsp marketplace
    # Local paths use "directory" source type
    settings["extraKnownMarketplaces"]["generated-lsp"] = {
        "source": {
            "source": "directory",
            "path": str(marketplace_path.absolute())
        }
    }

    save_json(settings_path, settings)


def get_scope_paths(scope: str) -> tuple[Path, Path]:
    """Get output and settings paths based on scope."""
    home = Path.home()
    cwd = Path.cwd()

    if scope == "user":
        output = home / ".claude" / "generated-lsp-marketplace"
        settings = home / ".claude" / "settings.json"
    elif scope == "project":
        output = cwd / ".claude" / "generated-lsp-marketplace"
        settings = cwd / ".claude" / "settings.json"
    elif scope == "local":
        output = cwd / ".claude" / "generated-lsp-marketplace"
        settings = cwd / ".claude" / "settings.local.json"
    else:
        raise ValueError(f"Unknown scope: {scope}")

    return output, settings


def main():
    parser = argparse.ArgumentParser(
        description="Generate Claude Code LSP marketplace from configuration"
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to parsed config JSON file"
    )
    parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="Path to server registry JSON"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for marketplace (overrides --scope)"
    )
    parser.add_argument(
        "--settings",
        type=Path,
        help="Path to settings.json to update (overrides --scope)"
    )
    parser.add_argument(
        "--scope",
        choices=["user", "project", "local"],
        help="Scope for output and settings (user/project/local)"
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output result as JSON"
    )

    args = parser.parse_args()

    # Determine output and settings paths
    if args.scope:
        scope_output, scope_settings = get_scope_paths(args.scope)
        output_dir = args.output or scope_output
        settings_path = args.settings or scope_settings
    else:
        if not args.output:
            parser.error("--output is required when --scope is not specified")
        output_dir = args.output
        settings_path = args.settings

    # Load inputs
    config = load_json(args.config)
    registry = load_json(args.registry)

    # Generate marketplace
    result = generate_marketplace(config, registry, output_dir)
    result["marketplace_path"] = str(output_dir)

    # Update settings if specified
    if settings_path:
        update_settings(settings_path, output_dir)
        result["settings_updated"] = str(settings_path)

    # Output results
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"\nGenerated {len(result['generated'])} LSP plugins:")
        for plugin in result["generated"]:
            print(f"  - {plugin}")

        if result["missing_binaries"]:
            print(f"\nMissing binaries ({len(result['missing_binaries'])}):")
            for server, commands in result["missing_binaries"].items():
                print(f"\n  {server}:")
                for method, cmd in commands.items():
                    print(f"    {method}: {cmd}")

        if result["unknown_servers"]:
            print(f"\nUnknown servers (not in registry):")
            for server in result["unknown_servers"]:
                print(f"  - {server}")

        print(f"\nMarketplace generated at: {output_dir}")

        # Always show the marketplace add command
        print(f"\n** IMPORTANT: Register the marketplace by running:")
        print(f"   /plugin marketplace add {output_dir}")

        print("\nThen install plugins:")
        for plugin in result["generated"]:
            print(f"   /plugin install {plugin}@generated-lsp")

        print("\n** After installing plugins, RELOAD Claude Code for LSP servers to activate **")


if __name__ == "__main__":
    main()
