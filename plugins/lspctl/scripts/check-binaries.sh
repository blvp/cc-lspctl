#!/bin/bash
# Check LSP binary availability
# Usage: check-binaries.sh [server1] [server2] ...
# If no arguments, checks all servers from registry

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REGISTRY="$SCRIPT_DIR/../registry/servers.json"

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed" >&2
    exit 1
fi

# Function to check a single binary
check_binary() {
    local server="$1"
    local command=$(jq -r ".\"$server\".command // empty" "$REGISTRY")

    if [ -z "$command" ]; then
        echo "UNKNOWN:$server"
        return 1
    fi

    if command -v "$command" &> /dev/null; then
        local path=$(which "$command")
        echo "INSTALLED:$server:$command:$path"
        return 0
    else
        echo "MISSING:$server:$command"
        return 1
    fi
}

# If arguments provided, check only those
if [ $# -gt 0 ]; then
    for server in "$@"; do
        check_binary "$server"
    done
else
    # Check all servers from registry
    servers=$(jq -r 'keys[]' "$REGISTRY")
    for server in $servers; do
        check_binary "$server"
    done
fi
