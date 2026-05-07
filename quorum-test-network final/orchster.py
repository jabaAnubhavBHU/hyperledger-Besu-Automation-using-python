#!/usr/bin/env python3

# ==========================================================
# ORCHESTRATOR SCRIPT
# ==========================================================
# Purpose:
# Automates full lifecycle of Besu network scaling:
#   1. Reset network
#   2. Add N nodes (configuration phase)
<<<<<<< HEAD
#   3. Update consensus mechanism in .env
#   4. Start network
#   5. Promote nodes to validators sequentially
#
# Supports:
#   - QBFT
#   - IBFT
#
# Usage:
#   python3 orchestrator.py <number_of_nodes> <QBFT/IBFT>
#
# Example:
#   python3 orchestrator.py 4 QBFT
#   python3 orchestrator.py 4 IBFT
=======
#   3. Start network
#   4. Promote nodes to validators sequentially
#
# Design Principles:
#   - Fail fast on any error
#   - Deterministic execution
#   - No partial state progression
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
# ==========================================================

import subprocess
import sys
import time
import requests
<<<<<<< HEAD
import os
=======
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc

# =========================
# CONFIG
# =========================

<<<<<<< HEAD
BASE_DIR = os.getcwd()

# Validate CLI input
if len(sys.argv) < 3:
    raise Exception(
        "Usage: python3 orchestrator.py <number_of_nodes> <QBFT/IBFT>"
    )

# Number of nodes to add/promote
TOTAL_NODES = int(sys.argv[1])

# Consensus mechanism
CONSENSUS_MECH = sys.argv[2].upper()

# Validate consensus
if CONSENSUS_MECH not in ["QBFT", "IBFT"]:
    raise Exception("Consensus must be QBFT or IBFT")

# Select correct RPC method dynamically
if CONSENSUS_MECH == "QBFT":
    VALIDATOR_RPC_METHOD = "qbft_getValidatorsByBlockNumber"
else:
    VALIDATOR_RPC_METHOD = "ibft_getValidatorsByBlockNumber"

# RPC endpoint (validator1)
=======
# Validate CLI input (must provide number of nodes)
if len(sys.argv) < 2:
    raise Exception("Usage: python3 orchestrator.py <number_of_nodes>")

# Total number of nodes to add and promote
TOTAL_NODES = int(sys.argv[1])

# RPC endpoint (validator1)
# Used for:
#   - network health checks
#   - validator queries
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
RPC_URL = "http://127.0.0.1:21001"

# Standard JSON-RPC headers
HEADERS = {"Content-Type": "application/json"}

<<<<<<< HEAD
=======

>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
# =========================
# HELPERS
# =========================

def run(cmd):
    """
    Execute shell command.
<<<<<<< HEAD
    Fails immediately if command fails.
    """

=======

    Behavior:
    - Prints command for traceability
    - Fails immediately if command fails

    Critical:
    - Ensures no step continues after failure
    """
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
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
<<<<<<< HEAD
    """

=======

    Returns:
    - result field if successful
    - None if any error occurs

    Note:
    - This function does NOT raise errors by design
    - Calling functions must validate response
    """
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or [],
        "id": 1
    }

    try:
<<<<<<< HEAD
        r = requests.post(
            RPC_URL,
            json=payload,
            headers=HEADERS
        )

        r.raise_for_status()

        response = r.json()

        if "error" in response:
            raise Exception(response["error"])

        return response["result"]
=======
        r = requests.post(RPC_URL, json=payload, headers=HEADERS)

        # Raise HTTP error if response not 200
        r.raise_for_status()

        return r.json()["result"]
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc

    except Exception as e:
        print(f"⚠️ RPC call failed ({method}): {e}")
        return None


<<<<<<< HEAD
def update_consensus_env():
    """
    Updates .env with selected consensus mechanism.
    """

    env_path = os.path.join(BASE_DIR, ".env")

    if not os.path.exists(env_path):
        raise Exception(f".env file not found: {env_path}")

    try:

        with open(env_path, "r") as f:
            lines = f.readlines()

        updated = False

        for i in range(len(lines)):

            if lines[i].startswith("BESU_CONS_ALGO="):

                lines[i] = (
                    f"BESU_CONS_ALGO={CONSENSUS_MECH}\n"
                )

                updated = True

        # Add variable if missing
        if not updated:

            lines.append(
                f"\nBESU_CONS_ALGO={CONSENSUS_MECH}\n"
            )

        with open(env_path, "w") as f:
            f.writelines(lines)

        print(
            f">> Updated .env consensus to "
            f"{CONSENSUS_MECH}"
        )

    except Exception as e:
        raise Exception(
            f"Failed updating .env: {e}"
        )


=======
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
# =========================
# WAIT FOR NETWORK READY
# =========================

def wait_for_network():
    """
    Wait until network becomes healthy.
<<<<<<< HEAD
    """

    print(">> Waiting for network to become healthy...if this fails check validator log if the validator is workign increase the timeout in orchester file in waitnetworkfor health function")
    time.sleep(60)

    for _ in range(10):

=======

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
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
        try:
            peers = rpc_call("net_peerCount")
            block = rpc_call("eth_blockNumber")

<<<<<<< HEAD
            if peers and block:

                if int(peers, 16) > 0:
                    print(
                        f">> Network ready "
                        f"(peers={peers}, block={block})"
                    )
=======
            # Validate both values exist
            if peers and block:
                if int(peers, 16) > 0:
                    print(f">> Network ready (peers={peers}, block={block})")
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
                    return

        except Exception as e:
            print(f"⚠️ Error while checking network health: {e}")

<<<<<<< HEAD
        time.sleep(2)

=======
        time.sleep(5)

    # Fail if network never becomes ready
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
    raise Exception("Network did not become ready")


# =========================
# WAIT FOR VALIDATOR UPDATE
# =========================

def wait_for_validator_count(expected):
    """
    Wait until validator set reaches expected size.
<<<<<<< HEAD
    """

    print(f">> Waiting for validator count = {expected}")

    for _ in range(40):

        try:
            vals = rpc_call(
                VALIDATOR_RPC_METHOD,
=======

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
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
                ["latest"]
            )

            if vals and len(vals) == expected:
                print(f">> Validator set updated: {len(vals)}")
                return

        except Exception as e:
            print(f"⚠️ Error while checking validator count: {e}")

        time.sleep(5)

<<<<<<< HEAD
=======
    # Fail if validator set does not update
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
    raise Exception("Validator count update failed")


# =========================
# MAIN FLOW
# =========================

def main():
<<<<<<< HEAD

    print(
        f"\n=== Adding {TOTAL_NODES} nodes "
        f"+ validators using {CONSENSUS_MECH} ===\n"
    )

    try:

        # --------------------------------------------------
        # STEP 1: RESET NETWORK
        # --------------------------------------------------

        run("python3 resetNodeEntries.py")

        time.sleep(5)

        # --------------------------------------------------
        # STEP 2: CREATE NODE CONFIGURATIONS
        # --------------------------------------------------

        for i in range(1, TOTAL_NODES + 1):

            print(f"\n--- Creating node {i} ---")

            run(f"python3 nodeAdder.py {i}")

        # --------------------------------------------------
        # STEP 3: UPDATE CONSENSUS ENV
        # --------------------------------------------------

        update_consensus_env()

        # --------------------------------------------------
        # STEP 4: START NETWORK
        # --------------------------------------------------

        print("\n>> Starting network...")

        run("./run.sh")

        # --------------------------------------------------
        # STEP 5: WAIT FOR NETWORK HEALTH
        # --------------------------------------------------

        wait_for_network()

        # --------------------------------------------------
        # STEP 6: FETCH INITIAL VALIDATORS
        # --------------------------------------------------

        base_validators = rpc_call(
            VALIDATOR_RPC_METHOD,
=======
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
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
            ["latest"]
        )

        if not base_validators:
<<<<<<< HEAD
            raise Exception(
                "Could not fetch initial validators"
            )

        current_count = len(base_validators)

        print(
            f">> Initial validator count: {current_count}"
        )

        # --------------------------------------------------
        # STEP 7: PROMOTE NODES SEQUENTIALLY
        # --------------------------------------------------

        for i in range(1, TOTAL_NODES + 1):

            print(f"\n--- Promoting node {i} ---")

            run(
                f"python3 validatorPromotion.py "
                f"{i} {CONSENSUS_MECH}"
            )

            current_count += 1

            wait_for_validator_count(current_count)

        print(
            f"\n🎉 All nodes added and promoted "
            f"successfully using {CONSENSUS_MECH}!\n"
        )

    except Exception as e:

        print(f"\n❌ FATAL ERROR: {e}")

=======
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
>>>>>>> f9702028a80b10bf1678546c3a99fe9b31077abc
        exit(1)


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()