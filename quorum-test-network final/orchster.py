#!/usr/bin/env python3

# ==========================================================
# ORCHESTRATOR SCRIPT
# ==========================================================
# Purpose:
# Automates full lifecycle of Besu network scaling:
#   1. Reset network
#   2. Add N nodes (configuration phase)
#   3. Start network
#   4. Promote nodes to validators sequentially
#
# Design Principles:
#   - Fail fast on any error
#   - Deterministic execution
#   - No partial state progression
# ==========================================================

import subprocess
import sys
import time
import requests

# =========================
# CONFIG
# =========================

# Validate CLI input (must provide number of nodes)
if len(sys.argv) < 2:
    raise Exception("Usage: python3 orchestrator.py <number_of_nodes>")

# Total number of nodes to add and promote
TOTAL_NODES = int(sys.argv[1])

# RPC endpoint (validator1)
# Used for:
#   - network health checks
#   - validator queries
RPC_URL = "http://127.0.0.1:21001"

# Standard JSON-RPC headers
HEADERS = {"Content-Type": "application/json"}


# =========================
# HELPERS
# =========================

def run(cmd):
    """
    Execute shell command.

    Behavior:
    - Prints command for traceability
    - Fails immediately if command fails

    Critical:
    - Ensures no step continues after failure
    """
    print(f">> Running: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True)

        if result.returncode != 0:
            raise Exception(f"Command failed: {cmd}")

    except Exception as e:
        print(f"❌ ERROR during command execution: {e}")
        exit(1)


def rpc_call(method, params=None):
    """
    Generic JSON-RPC call to Besu node.

    Returns:
    - result field if successful
    - None if any error occurs

    Note:
    - This function does NOT raise errors by design
    - Calling functions must validate response
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or [],
        "id": 1
    }

    try:
        r = requests.post(RPC_URL, json=payload, headers=HEADERS)

        # Raise HTTP error if response not 200
        r.raise_for_status()

        return r.json()["result"]

    except Exception as e:
        print(f"⚠️ RPC call failed ({method}): {e}")
        return None


# =========================
# WAIT FOR NETWORK READY
# =========================

def wait_for_network():
    """
    Wait until network becomes healthy.

    Conditions:
    - At least 1 peer connected
    - Block production has started

    Retry:
    - 30 attempts
    - 5 seconds interval

    Fails:
    - If network does not stabilize
    """
    print(">> Waiting for network to become healthy...")

    for _ in range(30):
        try:
            peers = rpc_call("net_peerCount")
            block = rpc_call("eth_blockNumber")

            # Validate both values exist
            if peers and block:
                if int(peers, 16) > 0:
                    print(f">> Network ready (peers={peers}, block={block})")
                    return

        except Exception as e:
            print(f"⚠️ Error while checking network health: {e}")

        time.sleep(5)

    # Fail if network never becomes ready
    raise Exception("Network did not become ready")


# =========================
# WAIT FOR VALIDATOR UPDATE
# =========================

def wait_for_validator_count(expected):
    """
    Wait until validator set reaches expected size.

    Used after each validator promotion.

    Retry:
    - 40 attempts
    - 5 seconds interval

    Fails:
    - If validator set does not update
    """
    print(f">> Waiting for validator count = {expected}")

    for _ in range(40):
        try:
            vals = rpc_call(
                "qbft_getValidatorsByBlockNumber",
                ["latest"]
            )

            if vals and len(vals) == expected:
                print(f">> Validator set updated: {len(vals)}")
                return

        except Exception as e:
            print(f"⚠️ Error while checking validator count: {e}")

        time.sleep(5)

    # Fail if validator set does not update
    raise Exception("Validator count update failed")


# =========================
# MAIN FLOW
# =========================

def main():
    """
    Main orchestration pipeline.

    Execution order:
    1. Reset network (clean baseline)
    2. Generate all node configs
    3. Start network
    4. Wait for health
    5. Promote nodes sequentially
    """

    print(f"\n=== Adding {TOTAL_NODES} nodes + validators ===\n")

    try:
        # --------------------------------------------------
        # STEP 1: RESET NETWORK
        # --------------------------------------------------
        # Ensures:
        #   - no stale configs
        #   - no duplicate entries
        #   - clean deterministic start
        run("python3 resetNodeEntries.py")

        # Small delay to ensure cleanup stability
        time.sleep(5)

        # --------------------------------------------------
        # STEP 2: CREATE ALL NODE CONFIGURATIONS
        # --------------------------------------------------
        # Only prepares:
        #   - keys
        #   - configs
        #   - docker entries
        # Does NOT start containers yet
        for i in range(1, TOTAL_NODES + 1):
            print(f"\n--- Creating node {i} ---")
            run(f"python3 nodeAdder.py {i}")

        # --------------------------------------------------
        # STEP 3: START NETWORK
        # --------------------------------------------------
        print("\n>> Starting network...")
        run("./run.sh")

        # --------------------------------------------------
        # STEP 4: WAIT FOR NETWORK HEALTH
        # --------------------------------------------------
        wait_for_network()

        # --------------------------------------------------
        # STEP 5: GET INITIAL VALIDATOR SET
        # --------------------------------------------------
        base_validators = rpc_call(
            "qbft_getValidatorsByBlockNumber",
            ["latest"]
        )

        if not base_validators:
            raise Exception("Could not fetch initial validators")

        current_count = len(base_validators)
        print(f">> Initial validator count: {current_count}")

        # --------------------------------------------------
        # STEP 6: PROMOTE NODES ONE BY ONE
        # --------------------------------------------------
        # Sequential promotion ensures:
        #   - stable voting
        #   - correct majority handling
        for i in range(1, TOTAL_NODES + 1):
            print(f"\n--- Promoting node {i} ---")

            run(f"python3 validatorPromotion.py {i}")

            current_count += 1

            # Wait until validator set reflects change
            wait_for_validator_count(current_count)

        print("\n🎉 All nodes added and promoted successfully!\n")

    except Exception as e:
        # Global fail-safe
        print(f"\n❌ FATAL ERROR: {e}")
        exit(1)


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()