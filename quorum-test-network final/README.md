Hyperledger Besu Dynamic Node & Validator Automation
Overview
This document describes the automated process of adding new nodes and promoting them to validators in a Hyperledger Besu QBFT network using Python-based orchestration scripts. The system enables dynamic scaling of validators while maintaining proper configuration and consensus.
Minimum Requirements
    • Docker (latest stable version)
    • Docker Compose
    • Python 3.8 or higher
    • Node.js and npm
    • Hyperledger Besu
    • Python libraries: requests, pyyaml, toml
    • Linux-based system (recommended for compatibility)
End-to-End Workflow
    1. Reset the network to a clean state
    2. Add N new nodes (configuration only)
    3. Start the network using ./run.sh
    4. Promote nodes to validators via QBFT voting
Scripts Description
resetNodeEntries.py
Resets the network to a base state. It stops running containers using ./stop.sh, restores original base configuration files (docker-compose.yml, static-nodes.json, permissions_config.toml), and removes dynamically added node directories. This ensures the system behaves like a fresh setup, preventing duplicate entries, stale configurations, and network conflicts.
addNode.py
Generates node keys, creates a node directory under config/nodes/, and moves generated files. It constructs the enode address, updates static-nodes.json and permissions_config.toml (avoiding duplicates), and inserts a properly formatted service block into docker-compose.yml with unique IP and RPC port.
validatorPromotion.py
Promotes a node to a validator using QBFT consensus voting. It fetches the node address, retrieves current validators via RPC, submits validator votes from multiple existing validators, and waits until the validator set is updated.
orchestrator.py
Automates the entire lifecycle: resets the network, adds multiple nodes in a loop, starts the network using ./run.sh, and promotes nodes sequentially to validators. This ensures correct ordering and avoids voting conflicts.
Reset Mechanism (Important)
The reset process restores the system to a known clean baseline. It replaces modified configuration files with original base versions and removes dynamically created node data. This ensures the network behaves as if it was freshly initialized. It eliminates issues such as duplicate enodes, incorrect permissions, mismatched IPs, and corrupted docker-compose configurations.
Port and IP Management
Validator nodes use predefined RPC ports (21001–21004). New nodes are assigned dynamic ports starting from 21005 to avoid conflicts. Each node is also assigned a unique IP within the Docker network (e.g., 172.16.239.X). Proper management ensures no collisions and stable network behavior.
