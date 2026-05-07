#!/usr/bin/env python3

# ==========================================================
# NODE ADDER SCRIPT
# ==========================================================
# Purpose:
#   Adds a new Besu node to the network by:
#     1. Generating keys
#     2. Creating node directory
#     3. Updating static-nodes.json
#     4. Updating permissions_config.toml
#     5. Updating docker-compose.yml
#
# Key Guarantees:
#   - No duplicate entries (pubkey-based deduplication)
#   - No IP conflicts (dynamic allocation)
#   - Fail-fast on any error
# ==========================================================

import os
import shutil
import subprocess
import json
import toml
import re
import sys
import textwrap


# =========================
# CONFIG (EDIT THESE)
# =========================

# Base working directory
BASE_DIR = os.getcwd()

# Validate input
if len(sys.argv) < 2:
    raise Exception("Usage: python3 addNode.py <node_number>")

# Node number (used for naming + port calculation)
NODE_NUMBER = int(sys.argv[1])

# Password used during key generation
PASSWORD = "Password"

# Base subnet
BASE_IP = "172.16.239."

# Directory paths
EXTRA_DIR = os.path.join(BASE_DIR, "extra")
CONFIG_DIR = os.path.join(BASE_DIR, "config")
BESU_CONFIG_DIR = os.path.join(CONFIG_DIR, "besu")
NODES_DIR = os.path.join(CONFIG_DIR, "nodes")

# Docker compose file
COMPOSE_FILE = os.path.join(BASE_DIR, "docker-compose.yml")


# =========================
# DERIVED VALUES
# =========================

# Node name (e.g., newnode5)
NODE_NAME = f"newnode{NODE_NUMBER}"

# Node directory path
NODE_DIR = os.path.join(NODES_DIR, NODE_NAME)

# Config files
STATIC_NODES_FILE = os.path.join(BESU_CONFIG_DIR, "static-nodes.json")
PERM_FILE = os.path.join(BESU_CONFIG_DIR, "permissions_config.toml")


# =========================
# HELPER: Extract pubkey
# =========================
def extract_pubkey(enode):
    """
    Extract public key from enode:
    enode://PUBKEY@ip:port → PUBKEY
    """
    return enode.split("://")[1].split("@")[0]


# =========================
# STEP 0: Get used IPs
# =========================
def get_used_ips():
    """
    Reads docker-compose and extracts all assigned IPs.
    Prevents IP duplication across containers.
    """
    try:
        used_ips = set()

        with open(COMPOSE_FILE, "r") as f:
            content = f.read()

        matches = re.findall(r'ipv4_address:\s*(\d+\.\d+\.\d+\.\d+)', content)

        for ip in matches:
            used_ips.add(ip)

        return used_ips

    except Exception as e:
        print(f"❌ ERROR reading docker-compose: {e}")
        exit(1)


# =========================
# STEP 0.1: Get free IP
# =========================
def get_free_ip():
    """
    Finds a free IP in subnet by checking existing assignments.
    """
    used_ips = get_used_ips()

    print(f">> Used IPs: {used_ips}")

    for i in range(10, 250):
        candidate = BASE_IP + str(i)

        if candidate not in used_ips:
            print(f">> Assigned free IP: {candidate}")
            return candidate

    raise Exception("No free IPs available in subnet")


# =========================
# STEP 1: Generate keys
# =========================
def generate_keys():
    """
    Generates:
    - nodekey
    - nodekey.pub
    - account keys
    """
    print(">> Generating node keys...")

    try:
        subprocess.run(
            ["npm", "install", "--legacy-peer-deps"],
            cwd=EXTRA_DIR,
            check=True
        )

        subprocess.run(
            ["node", "generate_node_details.js", "--password", PASSWORD],
            cwd=EXTRA_DIR,
            check=True
        )

    except Exception as e:
        print(f"❌ ERROR during key generation: {e}")
        exit(1)


# =========================
# STEP 2: Setup node directory
# =========================
def setup_node_directory():
    """
    Creates node directory and moves generated files into it.
    """
    print(">> Setting up node directory...")

    try:
        os.makedirs(NODE_DIR, exist_ok=True)

        files = ["nodekey", "nodekey.pub", "address", "accountPrivateKey", "accountKeystore"]

        for f in files:
            src = os.path.join(EXTRA_DIR, f)
            dst = os.path.join(NODE_DIR, f)

            if not os.path.exists(src):
                raise FileNotFoundError(f"{src} not found")

            shutil.move(src, dst)

    except Exception as e:
        print(f"❌ ERROR setting up node directory: {e}")
        exit(1)


# =========================
# STEP 3: Generate enode
# =========================
def generate_enode(node_ip):
    """
    Builds enode string using pubkey + assigned IP.
    """
    print(">> Generating enode...")

    try:
        pubkey_path = os.path.join(NODE_DIR, "nodekey.pub")

        with open(pubkey_path) as f:
            pubkey = f.read().strip()

        return f"enode://{pubkey}@{node_ip}:30303"

    except Exception as e:
        print(f"❌ ERROR generating enode: {e}")
        exit(1)


# =========================
# STEP 4: Update static-nodes.json
# =========================
def update_static_nodes(enode):
    """
    Updates static-nodes.json with deduplication (pubkey-based).
    """
    print(">> Updating static-nodes.json...")

    try:
        with open(STATIC_NODES_FILE) as f:
            nodes = json.load(f)

        new_pub = extract_pubkey(enode)

        filtered = []
        seen = set()

        # Remove duplicates
        for n in nodes:
            pub = extract_pubkey(n)
            if pub not in seen:
                filtered.append(n)
                seen.add(pub)

        # Add new node if not present
        if new_pub in seen:
            print(">> Node already exists in static-nodes, skipping")
        else:
            filtered.append(enode)

        with open(STATIC_NODES_FILE, "w") as f:
            json.dump(filtered, f, indent=2)

    except Exception as e:
        print(f"❌ ERROR updating static-nodes: {e}")
        exit(1)


# =========================
# STEP 5: Update permissioning
# =========================
def update_permissioning(enode):
    """
    Updates permissions_config.toml with deduplication.
    """
    print(">> Updating permissioning_config.toml...")

    try:
        data = toml.load(PERM_FILE)
        allowlist = data.get("nodes-allowlist", [])

        new_pub = extract_pubkey(enode)

        filtered = []
        seen = set()

        for n in allowlist:
            pub = extract_pubkey(n)
            if pub not in seen:
                filtered.append(n)
                seen.add(pub)

        if new_pub in seen:
            print(">> Node already exists in allowlist, skipping")
        else:
            filtered.append(enode)

        data["nodes-allowlist"] = filtered

        with open(PERM_FILE, "w") as f:
            toml.dump(data, f)

    except Exception as e:
        print(f"❌ ERROR updating permissioning: {e}")
        exit(1)


# =========================
# STEP 6: Update docker-compose
# =========================
def update_docker_compose(node_ip):
    """
    Inserts new node block into docker-compose:
    - preserves anchor usage
    - ensures correct indentation
    - avoids duplicate insertion
    """
    RPC_PORT = 21005 + (NODE_NUMBER - 1)

    print(">> Updating docker-compose.yml...")

    try:
        with open(COMPOSE_FILE, "r") as f:
            content = f.read()

        if NODE_NAME in content:
            print(f">> {NODE_NAME} already exists, skipping")
            return

        node_block = (
f"  {NODE_NAME}:\n"
f"    <<: *besu-def\n"
f"    container_name: {NODE_NAME}\n"
f"    ports:\n"
f"      - {RPC_PORT}:8545\n"
f"    volumes:\n"
f"      - public-keys:/opt/besu/public-keys/\n"
f"      - ./config/besu/:/config\n"
f"      - ./config/nodes/{NODE_NAME}:/opt/besu/keys\n"
f"      - ./logs/besu:/tmp/besu\n"
f"    depends_on:\n"
f"      - validator1\n"
f"    networks:\n"
f"      quorum-dev-quickstart:\n"
f"        ipv4_address: {node_ip}\n"
        )

        if "  rpcnode:" not in content:
            raise Exception("rpcnode block not found")

        updated = content.replace("  rpcnode:", node_block + "  rpcnode:")

        with open(COMPOSE_FILE, "w") as f:
            f.write(updated)

        print(f">> {NODE_NAME} added to docker-compose")

    except Exception as e:
        print(f"❌ ERROR updating docker-compose: {e}")
        exit(1)


# =========================
# MAIN
# =========================
def main():
    """
    Main execution pipeline for node addition.
    """
    print(f"\n=== Adding Node: {NODE_NAME} ===\n")

    try:
        node_ip = get_free_ip()

        generate_keys()
        setup_node_directory()

        enode = generate_enode(node_ip)
        print(f">> Enode: {enode}")

        update_static_nodes(enode)
        update_permissioning(enode)

        update_docker_compose(node_ip)

        print("\n✅ Node addition completed successfully!")
        print(f">> Assigned IP: {node_ip}")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        exit(1)


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()