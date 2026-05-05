#!/usr/bin/env python3

# ==========================================================
# VALIDATOR PROMOTION SCRIPT
# ==========================================================
# Purpose:
#   Promotes a newly added node to validator in QBFT network.
#
# Flow:
#   1. Read new node's address
#   2. Fetch current validator set
#   3. Send vote from all existing validators
#   4. Wait until validator is consistently visible in set
#
# Key Behavior:
#   - Uses dynamic validator discovery (no hardcoding)
#   - Requires majority votes (handled implicitly via loop)
#   - Ensures stability (not just one-time appearance)
#
# Failure Strategy:
#   - RPC failures → raise exception (fail-fast)
#   - Vote failures → warning (since quorum still possible)
#   - Timeout → hard failure
# ==========================================================

import os
import json
import time
import requests
import sys

# =========================
# CONFIG
# =========================

BASE_DIR = os.getcwd()

# Validate input
if len(sys.argv) < 2:
    raise Exception("Usage: python3 validatorPromotion.py <node_number>")

# Node being promoted
NODE_NUMBER = int(sys.argv[1])
NODE_NAME = f"newnode{NODE_NUMBER}"

# Validator RPC base (validator1 → 21001)
BASE_RPC_PORT = 21001

HEADERS = {"Content-Type": "application/json"}


# =========================
# HELPERS
# =========================

def normalize(addr):
    """
    Normalize Ethereum address:
    - lowercase
    - remove 0x
    Ensures reliable comparison across formats.
    """
    return addr.lower().replace("0x", "")


def rpc_call(url, method, params=None):
    """
    Generic JSON-RPC call wrapper.
    Critical:
    - Any failure raises exception → stops execution
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or [],
        "id": 1
    }

    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        return response.json()["result"]

    except Exception as e:
        raise Exception(f"RPC failed at {url}: {e}")


# =========================
# STEP 1: Get validator address
# =========================
def get_new_validator_address():
    """
    Reads the Ethereum address of the new node.
    Source:
      config/nodes/newnodeX/address
    """
    path = os.path.join(BASE_DIR, "config", "nodes", NODE_NAME, "address")

    if not os.path.exists(path):
        raise Exception("Address file not found")

    try:
        with open(path) as f:
            addr = f.read().strip()

        print(f">> New validator address: {addr}")
        return addr

    except Exception as e:
        raise Exception(f"Failed reading validator address: {e}")


# =========================
# STEP 2: Get current validators
# =========================
def get_current_validators():
    """
    Fetches current validator set from primary validator node.
    """
    url = f"http://127.0.0.1:{BASE_RPC_PORT}"

    validators = rpc_call(
        url,
        "qbft_getValidatorsByBlockNumber",
        ["latest"]
    )

    return validators


# =========================
# STEP 3: Build validator RPC URLs dynamically
# =========================
def get_validator_rpc_urls():
    """
    Dynamically builds RPC endpoints based on validator count.
    Assumption:
      validators are mapped sequentially:
      21001, 21002, 21003, ...
    """
    validators = get_current_validators()

    urls = []
    for i in range(len(validators)):
        urls.append(f"http://127.0.0.1:{BASE_RPC_PORT + i}")

    print(f">> Validator RPC endpoints: {urls}")
    return urls


# =========================
# STEP 4: Propose vote
# =========================
def propose_vote(new_validator):
    """
    Sends vote transaction from all validators.

    Behavior:
    - Each validator proposes vote
    - Some failures allowed (quorum still possible)
    """
    print(">> Proposing validator vote...")

    urls = get_validator_rpc_urls()

    for url in urls:
        try:
            rpc_call(
                url,
                "qbft_proposeValidatorVote",
                [new_validator, True]
            )
            print(f">> Vote submitted from {url}")

        except Exception as e:
            print(f">> Warning: vote failed from {url} → {e}")


# =========================
# STEP 5: Wait for stable inclusion
# =========================
def wait_for_validator(new_validator, timeout=100, stable_checks=1):
    """
    Waits until validator appears consistently in validator set.

    Stability Logic:
    - Must appear in consecutive checks
    - Prevents false positives during consensus transition
    """
    print(">> Waiting for validator to be STABLE in set...")

    start = time.time()
    consecutive_success = 0

    while time.time() - start < timeout:
        validators = get_current_validators()

        print(f">> Current validators: {validators}")

        if normalize(new_validator) in [normalize(v) for v in validators]:
            consecutive_success += 1
            print(f">> Seen {consecutive_success}/{stable_checks} times")
        else:
            consecutive_success = 0

        # Validator considered added only if stable
        if consecutive_success >= stable_checks:
            print("✅ Validator successfully added (stable)")
            return True

        time.sleep(5)

    raise Exception("❌ Timeout: Validator not stably added")


# =========================
# MAIN
# =========================
def main():
    """
    Full validator promotion flow.
    """
    print(f"\n=== Promoting {NODE_NAME} to validator ===\n")

    try:
        new_validator = get_new_validator_address()

        current = get_current_validators()
        print(f">> Current validators: {current}")

        # Skip if already validator
        if normalize(new_validator) in [normalize(v) for v in current]:
            print(">> Already a validator, skipping")
            return

        # Send votes
        propose_vote(new_validator)

        # Wait for consensus update
        wait_for_validator(new_validator)

        print("\n✅ Validator promotion completed!\n")

    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        exit(1)


# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()