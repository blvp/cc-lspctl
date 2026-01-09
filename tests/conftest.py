"""Shared pytest fixtures for lspctl tests."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def fixtures_dir(project_root) -> Path:
    """Return the fixtures directory."""
    return project_root / "tests" / "fixtures"


@pytest.fixture
def registry(project_root) -> dict:
    """Load the server registry."""
    registry_path = project_root / "registry" / "servers.json"
    with open(registry_path) as f:
        return json.load(f)


@pytest.fixture
def lua_parser_script(project_root) -> Path:
    """Return path to the Lua parser script."""
    return project_root / "scripts" / "parse-lua-config.lua"


@pytest.fixture
def marketplace_generator(project_root) -> Path:
    """Return path to the marketplace generator script."""
    return project_root / "scripts" / "generate-marketplace.py"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp = tempfile.mkdtemp(prefix="lspctl-test-")
    yield Path(temp)
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def minimal_config(fixtures_dir) -> Path:
    """Return path to minimal config fixture."""
    return fixtures_dir / "minimal-config.lua"


@pytest.fixture
def full_config(fixtures_dir) -> Path:
    """Return path to full config fixture."""
    return fixtures_dir / "full-config.lua"


@pytest.fixture
def empty_config(fixtures_dir) -> Path:
    """Return path to empty config fixture."""
    return fixtures_dir / "empty-config.lua"


@pytest.fixture
def invalid_config(fixtures_dir) -> Path:
    """Return path to invalid config fixture."""
    return fixtures_dir / "invalid-config.lua"


@pytest.fixture
def unknown_servers_config(fixtures_dir) -> Path:
    """Return path to config with unknown servers."""
    return fixtures_dir / "unknown-servers-config.lua"


@pytest.fixture
def mock_claude_cli(mocker):
    """Mock Claude CLI commands."""
    mock = mocker.patch("subprocess.run")
    mock.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="", stderr=""
    )
    return mock


@pytest.fixture
def generated_marketplace(temp_dir, full_config, registry, marketplace_generator):
    """Pre-generate a marketplace for testing removal operations."""
    # First parse the config
    result = subprocess.run(
        ["lua", str(temp_dir.parent.parent / "scripts" / "parse-lua-config.lua"), str(full_config)],
        capture_output=True,
        text=True,
        cwd=temp_dir,
    )

    if result.returncode != 0:
        pytest.skip(f"Lua not available or parse failed: {result.stderr}")

    # Write parsed config to temp file
    config_json_path = temp_dir / "config.json"
    with open(config_json_path, "w") as f:
        f.write(result.stdout)

    # Generate marketplace
    registry_path = temp_dir.parent.parent / "registry" / "servers.json"
    output_dir = temp_dir / "generated-lsp-marketplace"

    gen_result = subprocess.run(
        [
            "python3",
            str(marketplace_generator),
            "--config", str(config_json_path),
            "--registry", str(registry_path),
            "--output", str(output_dir),
        ],
        capture_output=True,
        text=True,
    )

    if gen_result.returncode != 0:
        pytest.fail(f"Marketplace generation failed: {gen_result.stderr}")

    return output_dir
