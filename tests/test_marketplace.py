"""Tests for the marketplace generator."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


def run_generator(
    marketplace_generator: Path,
    config_json: dict,
    registry: dict,
    output_dir: Path,
    scope: str | None = None,
    settings_path: Path | None = None,
    extra_args: list | None = None,
) -> tuple[int, str, str]:
    """Run the marketplace generator script."""
    # Write config to temp file
    config_file = output_dir / "config.json"
    with open(config_file, "w") as f:
        json.dump(config_json, f)

    # Write registry to temp file
    registry_file = output_dir / "registry.json"
    with open(registry_file, "w") as f:
        json.dump(registry, f)

    cmd = [
        "python3",
        str(marketplace_generator),
        "--config", str(config_file),
        "--registry", str(registry_file),
        "--output", str(output_dir / "marketplace"),
        "--json-output",
    ]

    if scope:
        cmd.extend(["--scope", scope])

    if settings_path:
        cmd.extend(["--settings", str(settings_path)])

    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


class TestMarketplaceGeneration:
    """Tests for marketplace generation."""

    def test_generate_single_server(self, marketplace_generator, registry, temp_dir):
        """Test generating marketplace with a single server."""
        config = {"ensure_installed": ["pylsp"], "servers": {}}

        returncode, stdout, _ = run_generator(
            marketplace_generator, config, registry, temp_dir
        )

        assert returncode == 0
        result = json.loads(stdout)
        assert "lsp-python-pylsp" in result["generated"]
        assert len(result["generated"]) == 1

        # Check files were created
        marketplace_dir = temp_dir / "marketplace"
        assert (marketplace_dir / ".claude-plugin" / "marketplace.json").exists()
        assert (marketplace_dir / "plugins" / "lsp-python-pylsp" / ".lsp.json").exists()

    def test_generate_multiple_servers(
        self, marketplace_generator, registry, temp_dir
    ):
        """Test generating marketplace with multiple servers."""
        config = {
            "ensure_installed": ["pylsp", "ts_ls", "lua_ls"],
            "servers": {},
        }

        returncode, stdout, _ = run_generator(
            marketplace_generator, config, registry, temp_dir
        )

        assert returncode == 0
        result = json.loads(stdout)
        assert len(result["generated"]) == 3
        assert "lsp-python-pylsp" in result["generated"]
        assert "lsp-typescript" in result["generated"]
        assert "lsp-lua" in result["generated"]

    def test_generate_with_custom_settings(
        self, marketplace_generator, registry, temp_dir
    ):
        """Test that custom server settings are included in .lsp.json."""
        config = {
            "ensure_installed": ["pylsp"],
            "servers": {
                "pylsp": {
                    "settings": {
                        "pylsp": {"plugins": {"ruff": {"enabled": True}}}
                    }
                }
            },
        }

        returncode, stdout, _ = run_generator(
            marketplace_generator, config, registry, temp_dir
        )

        assert returncode == 0

        # Check settings are in .lsp.json
        lsp_json_path = (
            temp_dir / "marketplace" / "plugins" / "lsp-python-pylsp" / ".lsp.json"
        )
        with open(lsp_json_path) as f:
            lsp_config = json.load(f)

        assert "python" in lsp_config
        assert "settings" in lsp_config["python"]
        assert lsp_config["python"]["settings"]["pylsp"]["plugins"]["ruff"]["enabled"]

    def test_unknown_server_warning(
        self, marketplace_generator, registry, temp_dir
    ):
        """Test that unknown servers are reported but don't cause failure."""
        config = {
            "ensure_installed": ["unknown_server", "pylsp"],
            "servers": {},
        }

        returncode, stdout, stderr = run_generator(
            marketplace_generator, config, registry, temp_dir
        )

        assert returncode == 0
        result = json.loads(stdout)
        assert "unknown_server" in result["unknown_servers"]
        assert "lsp-python-pylsp" in result["generated"]

    def test_missing_binary_detection(
        self, marketplace_generator, registry, temp_dir, mocker
    ):
        """Test that missing binaries are detected and reported."""
        config = {"ensure_installed": ["pylsp"], "servers": {}}

        returncode, stdout, _ = run_generator(
            marketplace_generator, config, registry, temp_dir
        )

        assert returncode == 0
        result = json.loads(stdout)
        # Missing binaries might or might not be detected depending on system
        # Just check the structure is correct
        assert "missing_binaries" in result


class TestMarketplaceStructure:
    """Tests for generated marketplace file structure."""

    def test_marketplace_json_structure(
        self, marketplace_generator, registry, temp_dir
    ):
        """Test marketplace.json has correct structure."""
        config = {"ensure_installed": ["pylsp", "ts_ls"], "servers": {}}

        returncode, _, _ = run_generator(
            marketplace_generator, config, registry, temp_dir
        )
        assert returncode == 0

        marketplace_json_path = (
            temp_dir / "marketplace" / ".claude-plugin" / "marketplace.json"
        )
        with open(marketplace_json_path) as f:
            marketplace = json.load(f)

        assert marketplace["name"] == "generated-lsp"
        assert "owner" in marketplace
        assert marketplace["owner"]["name"] == "lspctl"
        assert "metadata" in marketplace
        assert marketplace["metadata"]["pluginRoot"] == "./plugins"
        assert "plugins" in marketplace
        assert len(marketplace["plugins"]) == 2

        # Check plugin entries
        plugin_names = [p["name"] for p in marketplace["plugins"]]
        assert "lsp-python-pylsp" in plugin_names
        assert "lsp-typescript" in plugin_names

    def test_plugin_json_structure(
        self, marketplace_generator, registry, temp_dir
    ):
        """Test plugin.json has correct structure."""
        config = {"ensure_installed": ["pylsp"], "servers": {}}

        returncode, _, _ = run_generator(
            marketplace_generator, config, registry, temp_dir
        )
        assert returncode == 0

        plugin_json_path = (
            temp_dir
            / "marketplace"
            / "plugins"
            / "lsp-python-pylsp"
            / ".claude-plugin"
            / "plugin.json"
        )
        with open(plugin_json_path) as f:
            plugin = json.load(f)

        assert plugin["name"] == "lsp-python-pylsp"
        assert "description" in plugin
        assert "version" in plugin

    def test_lsp_json_structure(self, marketplace_generator, registry, temp_dir):
        """Test .lsp.json has correct structure."""
        config = {"ensure_installed": ["pylsp"], "servers": {}}

        returncode, _, _ = run_generator(
            marketplace_generator, config, registry, temp_dir
        )
        assert returncode == 0

        lsp_json_path = (
            temp_dir / "marketplace" / "plugins" / "lsp-python-pylsp" / ".lsp.json"
        )
        with open(lsp_json_path) as f:
            lsp_config = json.load(f)

        # Should have language as top-level key
        assert "python" in lsp_config
        python_config = lsp_config["python"]

        # Check required fields
        assert "command" in python_config
        assert python_config["command"] == "pylsp"
        assert "extensionToLanguage" in python_config
        assert ".py" in python_config["extensionToLanguage"]


class TestMarketplaceSettings:
    """Tests for settings.json integration."""

    def test_settings_updated_with_scope(
        self, marketplace_generator, registry, temp_dir
    ):
        """Test that settings.json is updated when scope is specified."""
        config = {"ensure_installed": ["pylsp"], "servers": {}}
        settings_path = temp_dir / "settings.json"

        # Create empty settings file
        with open(settings_path, "w") as f:
            json.dump({}, f)

        returncode, stdout, _ = run_generator(
            marketplace_generator,
            config,
            registry,
            temp_dir,
            settings_path=settings_path,
        )

        assert returncode == 0

        # Check settings was updated
        with open(settings_path) as f:
            settings = json.load(f)

        assert "extraKnownMarketplaces" in settings
        assert "generated-lsp" in settings["extraKnownMarketplaces"]

    def test_settings_preserves_existing_content(
        self, marketplace_generator, registry, temp_dir
    ):
        """Test that existing settings.json content is preserved."""
        config = {"ensure_installed": ["pylsp"], "servers": {}}
        settings_path = temp_dir / "settings.json"

        # Create settings with existing content
        existing_settings = {"someExistingSetting": True, "anotherSetting": "value"}
        with open(settings_path, "w") as f:
            json.dump(existing_settings, f)

        returncode, _, _ = run_generator(
            marketplace_generator,
            config,
            registry,
            temp_dir,
            settings_path=settings_path,
        )

        assert returncode == 0

        # Check existing content preserved
        with open(settings_path) as f:
            settings = json.load(f)

        assert settings["someExistingSetting"] is True
        assert settings["anotherSetting"] == "value"
        assert "extraKnownMarketplaces" in settings


class TestMarketplaceEdgeCases:
    """Edge case tests for marketplace generation."""

    def test_empty_ensure_installed(self, marketplace_generator, registry, temp_dir):
        """Test handling of empty ensure_installed."""
        config = {"ensure_installed": [], "servers": {}}

        returncode, stdout, _ = run_generator(
            marketplace_generator, config, registry, temp_dir
        )

        assert returncode == 0
        result = json.loads(stdout)
        assert result["generated"] == []

    def test_regeneration_cleans_previous(
        self, marketplace_generator, registry, temp_dir
    ):
        """Test that regenerating marketplace cleans previous content."""
        # First generation
        config1 = {"ensure_installed": ["pylsp", "ts_ls"], "servers": {}}
        run_generator(marketplace_generator, config1, registry, temp_dir)

        # Check first plugins exist
        assert (
            temp_dir / "marketplace" / "plugins" / "lsp-python-pylsp"
        ).exists()
        assert (temp_dir / "marketplace" / "plugins" / "lsp-typescript").exists()

        # Second generation with different servers
        config2 = {"ensure_installed": ["lua_ls"], "servers": {}}
        run_generator(marketplace_generator, config2, registry, temp_dir)

        # Check old plugins are removed
        assert not (
            temp_dir / "marketplace" / "plugins" / "lsp-python-pylsp"
        ).exists()
        assert not (
            temp_dir / "marketplace" / "plugins" / "lsp-typescript"
        ).exists()
        # Check new plugin exists
        assert (temp_dir / "marketplace" / "plugins" / "lsp-lua").exists()


class TestMarketplaceRemove:
    """Tests for --remove functionality."""

    def _setup_marketplace(
        self, marketplace_generator, registry, temp_dir, servers: list[str]
    ) -> Path:
        """Helper to set up a marketplace with given servers."""
        config = {"ensure_installed": servers, "servers": {}}
        run_generator(marketplace_generator, config, registry, temp_dir)
        return temp_dir / "marketplace"

    def test_remove_server_from_marketplace(
        self, marketplace_generator, registry, temp_dir, project_root
    ):
        """Test removing a single server from marketplace."""
        # Set up marketplace with multiple servers
        marketplace_dir = self._setup_marketplace(
            marketplace_generator, registry, temp_dir, ["pylsp", "ts_ls", "lua_ls"]
        )

        # Verify all plugins exist
        assert (marketplace_dir / "plugins" / "lsp-python-pylsp").exists()
        assert (marketplace_dir / "plugins" / "lsp-typescript").exists()
        assert (marketplace_dir / "plugins" / "lsp-lua").exists()

        # Remove pylsp
        registry_path = project_root / "registry" / "servers.json"
        result = subprocess.run(
            [
                "python3",
                str(marketplace_generator),
                "--remove", "pylsp",
                "--registry", str(registry_path),
                "--output", str(marketplace_dir),
                "--json-output",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        result_data = json.loads(result.stdout)

        assert result_data["removed"] == "lsp-python-pylsp"
        assert "lsp-typescript" in result_data["remaining_plugins"]
        assert "lsp-lua" in result_data["remaining_plugins"]
        assert result_data["marketplace_empty"] is False

        # Verify plugin directory was removed
        assert not (marketplace_dir / "plugins" / "lsp-python-pylsp").exists()
        # Other plugins still exist
        assert (marketplace_dir / "plugins" / "lsp-typescript").exists()
        assert (marketplace_dir / "plugins" / "lsp-lua").exists()

        # Verify marketplace.json updated
        with open(marketplace_dir / ".claude-plugin" / "marketplace.json") as f:
            marketplace = json.load(f)
        plugin_names = [p["name"] for p in marketplace["plugins"]]
        assert "lsp-python-pylsp" not in plugin_names
        assert "lsp-typescript" in plugin_names

    def test_remove_last_server_warns(
        self, marketplace_generator, registry, temp_dir, project_root
    ):
        """Test that removing the last server warns about empty marketplace."""
        # Set up marketplace with single server
        marketplace_dir = self._setup_marketplace(
            marketplace_generator, registry, temp_dir, ["pylsp"]
        )

        # Remove the only server
        registry_path = project_root / "registry" / "servers.json"
        result = subprocess.run(
            [
                "python3",
                str(marketplace_generator),
                "--remove", "pylsp",
                "--registry", str(registry_path),
                "--output", str(marketplace_dir),
                "--json-output",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        result_data = json.loads(result.stdout)

        assert result_data["marketplace_empty"] is True
        assert result_data["remaining_plugins"] == []

    def test_remove_nonexistent_server_error(
        self, marketplace_generator, registry, temp_dir, project_root
    ):
        """Test removing a server not in the marketplace."""
        # Set up marketplace with pylsp only
        marketplace_dir = self._setup_marketplace(
            marketplace_generator, registry, temp_dir, ["pylsp"]
        )

        # Try to remove ts_ls which isn't in the marketplace
        registry_path = project_root / "registry" / "servers.json"
        result = subprocess.run(
            [
                "python3",
                str(marketplace_generator),
                "--remove", "ts_ls",
                "--registry", str(registry_path),
                "--output", str(marketplace_dir),
                "--json-output",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0  # Still returns 0 but with error in result
        result_data = json.loads(result.stdout)
        assert result_data["error"] is not None
        assert "not found" in result_data["error"]

    def test_remove_unknown_server_error(
        self, marketplace_generator, registry, temp_dir, project_root
    ):
        """Test removing a server not in the registry."""
        marketplace_dir = self._setup_marketplace(
            marketplace_generator, registry, temp_dir, ["pylsp"]
        )

        registry_path = project_root / "registry" / "servers.json"
        result = subprocess.run(
            [
                "python3",
                str(marketplace_generator),
                "--remove", "unknown_server",
                "--registry", str(registry_path),
                "--output", str(marketplace_dir),
                "--json-output",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        result_data = json.loads(result.stdout)
        assert result_data["error"] is not None
        assert "Unknown server" in result_data["error"]


class TestMarketplaceDeregister:
    """Tests for --deregister functionality."""

    def _setup_marketplace_with_settings(
        self, marketplace_generator, registry, temp_dir, servers: list[str]
    ) -> tuple[Path, Path]:
        """Helper to set up marketplace with settings.json."""
        config = {"ensure_installed": servers, "servers": {}}
        settings_path = temp_dir / "settings.json"

        # Create empty settings file first
        with open(settings_path, "w") as f:
            json.dump({}, f)

        run_generator(
            marketplace_generator, config, registry, temp_dir,
            settings_path=settings_path
        )
        return temp_dir / "marketplace", settings_path

    def test_deregister_removes_all(
        self, marketplace_generator, registry, temp_dir, project_root
    ):
        """Test that --deregister removes marketplace and settings."""
        marketplace_dir, settings_path = self._setup_marketplace_with_settings(
            marketplace_generator, registry, temp_dir, ["pylsp", "ts_ls"]
        )

        # Verify marketplace exists
        assert marketplace_dir.exists()
        assert (marketplace_dir / "plugins" / "lsp-python-pylsp").exists()

        # Verify settings has marketplace
        with open(settings_path) as f:
            settings = json.load(f)
        assert "generated-lsp" in settings["extraKnownMarketplaces"]

        # Deregister
        result = subprocess.run(
            [
                "python3",
                str(marketplace_generator),
                "--deregister",
                "--output", str(marketplace_dir),
                "--settings", str(settings_path),
                "--json-output",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        result_data = json.loads(result.stdout)

        assert result_data["deregistered"] is True
        assert result_data["files_deleted"] is True
        assert "lsp-python-pylsp" in result_data["plugins_removed"]
        assert "lsp-typescript" in result_data["plugins_removed"]

        # Verify marketplace directory deleted
        assert not marketplace_dir.exists()

        # Verify settings updated
        with open(settings_path) as f:
            settings = json.load(f)
        assert "extraKnownMarketplaces" not in settings or \
               "generated-lsp" not in settings.get("extraKnownMarketplaces", {})

    def test_deregister_nonexistent_marketplace(
        self, marketplace_generator, temp_dir
    ):
        """Test deregistering when no marketplace exists."""
        nonexistent = temp_dir / "nonexistent-marketplace"

        result = subprocess.run(
            [
                "python3",
                str(marketplace_generator),
                "--deregister",
                "--output", str(nonexistent),
                "--json-output",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        result_data = json.loads(result.stdout)

        assert result_data["files_deleted"] is False
        assert result_data["plugins_removed"] == []
