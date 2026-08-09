#!/usr/bin/env bash
set -euo pipefail

# Single entry point: builds the app (if not already built) and installs it
# for the current Linux user. See scripts/install_linux.sh for details.

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$SCRIPT_DIR/scripts/install_linux.sh" "$@"
