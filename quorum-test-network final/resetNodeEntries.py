#!/usr/bin/env python3

# ==========================================================
# RESET SCRIPT
# ==========================================================
# Purpose:
#   Restores the Besu network to a clean baseline state by:
#     1. Stopping running containers
#     2. Restoring base configuration files
#     3. Removing dynamically added nodes
#
# Important Behavior:
#   - Base files act as "source of truth"
#   - Any dynamically added nodes (newnodeX) are deleted
#   - Ensures system behaves like fresh setup
#
# Failure Strategy:
#   - Critical steps (restore) will STOP execution on failure
#   - Non-critical step (docker stop) prints warning only
# ==========================================================

import os
import shutil
import subprocess
import re

# =========================
# CONFIG
# =========================

# Root project directory
BASE_DIR = os.getcwd()

# Config directories
CONFIG_DIR = os.path.join(BASE_DIR, "config")
BESU_CONFIG_DIR = os.path.join(CONFIG_DIR, "besu")
NODES_DIR = os.path.join(CONFIG_DIR, "nodes")

# Docker compose file
COMPOSE_FILE = os.path.join(BASE_DIR, "docker-compose.yml")

# Backup (baseline) files → MUST exist
COMPOSE_BASE = os.path.join(BASE_DIR, "docker-compose.base.yml")
STATIC_BASE = os.path.join(BESU_CONFIG_DIR, "static-nodes.base.json")
PERM_BASE = os.path.join(BESU_CONFIG_DIR, "permissions_config.base.toml")

# Active files (will be overwritten)
STATIC_FILE = os.path.join(BESU_CONFIG_DIR, "static-nodes.json")
PERM_FILE = os.path.join(BESU_CONFIG_DIR, "permissions_config.toml")


# =========================
# STEP 1: Stop containers
# =========================
def stop_network():
    """
    Stops running docker network using custom script.
    Non-critical:
    - Failure does NOT stop execution
    - Allows recovery even if containers already stopped
    """
    print(">> Stopping docker network...")

    try:
        subprocess.run(["./remove.sh"], check=True)
    except Exception as e:
        print(">> Warning: container removal failed failed:", e)


# =========================
# STEP 2: Restore docker-compose
# =========================
def restore_compose():
    """
    Restores docker-compose.yml from baseline file.
    Critical step:
    - If base file missing → STOP execution
    """
    print(">> Restoring docker-compose.yml...")

    if not os.path.exists(COMPOSE_BASE):
        raise Exception("Missing docker-compose.base.yml")

    try:
        shutil.copy(COMPOSE_BASE, COMPOSE_FILE)
    except Exception as e:
        print(f"❌ ERROR restoring docker-compose: {e}")
        exit(1)


# =========================
# STEP 3: Restore static-nodes.json
# =========================
def restore_static_nodes():
    """
    Restores static-nodes.json to original state.
    Removes all dynamically added nodes.
    """
    print(">> Restoring static-nodes.json...")

    if not os.path.exists(STATIC_BASE):
        raise Exception("Missing static-nodes.base.json")

    try:
        shutil.copy(STATIC_BASE, STATIC_FILE)
    except Exception as e:
        print(f"❌ ERROR restoring static-nodes: {e}")
        exit(1)


# =========================
# STEP 4: Restore permissions_config.toml
# =========================
def restore_permissions():
    """
    Restores permissioning configuration.
    Ensures allowlist returns to original validators only.
    """
    print(">> Restoring permissions_config.toml...")

    if not os.path.exists(PERM_BASE):
        raise Exception("Missing permissions_config.base.toml")

    try:
        shutil.copy(PERM_BASE, PERM_FILE)
    except Exception as e:
        print(f"❌ ERROR restoring permissions: {e}")
        exit(1)


# =========================
# STEP 5: Delete newnode directories
# =========================
def cleanup_nodes():
    """
    Removes all dynamically created node directories:
    - Matches pattern: newnodeX
    - Keeps validator directories intact
    """
    print(">> Removing dynamically added nodes...")

    if not os.path.exists(NODES_DIR):
        return

    try:
        for name in os.listdir(NODES_DIR):
            path = os.path.join(NODES_DIR, name)

            # Only remove dynamically added nodes
            if re.match(r"newnode\d+", name):
                print(f">> Removing {name}")
                shutil.rmtree(path)

    except Exception as e:
        print(f"❌ ERROR during node cleanup: {e}")
        exit(1)


# =========================
# MAIN
# =========================
def main():
    """
    Full reset pipeline:
    - Stops network
    - Restores all base configs
    - Cleans dynamically added nodes
    """
    print("\n=== RESETTING BESU NETWORK TO CLEAN STATE ===\n")

    try:
        stop_network()
        restore_compose()
        restore_static_nodes()
        restore_permissions()
        cleanup_nodes()

        print("\n✅ Reset complete!")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        exit(1)


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()