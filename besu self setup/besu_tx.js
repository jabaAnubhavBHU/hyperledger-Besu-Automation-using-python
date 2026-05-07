// besu_tx.js
// A minimal script that:
//   - connects to an Ethereum‑style RPC node (e.g., Besu),
//   - sends 0.01 ETH from one account to another,
//   - and waits for the transaction to be included in a block.

const { ethers } = require("ethers");

// 1. Import ethers
// - `ethers` is a JavaScript library for Ethereum‑compatible blockchains (EVM).
// - It provides:
//   - `JsonRpcProvider` to talk to an RPC endpoint (curl‑like JSON‑RPC over HTTP),
//   - `Wallet` to sign transactions with a private key,
//   - utilities like `parseEther` to convert human‑readable ETH values to wei.

const provider = new ethers.JsonRpcProvider("http://localhost:8545");

// 2. Create a provider (readonly connection to a node)
// - `JsonRpcProvider(url)` creates a connection to a node’s JSON‑RPC endpoint.
// - `http://localhost:8545` is the default HTTP‑RPC address for your Besu Node‑1.
// - This provider can:
//   - read balances (`getBalance`),
//   - get network ID (`getNetwork`),
//   - get gas price / fee info (`getFeeData`),
//   - but it does NOT sign; for signing you need `Wallet`.

const senderAddress = "0xFE3b557E8Fb62b89F4916B721be55cEb828dBd73".toLowerCase();
const receiverAddress = "0x627306090abab3a6e1400e9345bc60c78a8bef57".toLowerCase();

// 3. Define sender and receiver addresses
// - These are two common test accounts:
//   - `0xFE3b...dBd73` has a large pre‑funded balance on dev networks,
//   - `0x6273...8bef57` is another known test address.
// - `.toLowerCase()`:
//   - Converts mixed‑case hex to all‑lowercase,
//   - so ethers does not enforce Ethereum’s EIP‑55 checksum validation.
//   - On dev this avoids "bad address checksum" errors; in production you can keep original case.

const privateKey = "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63";
const wallet = new ethers.Wallet(privateKey, provider);

// 4. Create a signing wallet
// - `privateKey`:
//   - This is the private key for the sender account `0xFE3b...dBd73`.
//   - On dev it is public and safe to use; NEVER use it on Mainnet.
// - `new ethers.Wallet(privateKey, provider)`:
//   - Binds this private key to the `provider` connection.
//   - `wallet` can sign and send raw transactions via `eth_sendRawTransaction` under the hood,
//     bypassing Besu’s restriction on `eth_sendTransaction`.

async function main() {
  try {
    // 5. Connect and read network info
    const network = await provider.getNetwork();
    console.log("Connected to chain:", network.chainId.toString());

    // - `provider.getNetwork()` calls `eth_chainId` and related RPCs.
    // - `network.chainId` tells you what chain you are on (e.g., 1337 for dev).
    // - Later, when you switch RPC URL to Quorum testnet, this will show the new chain ID.

    // 6. Read initial balances
    const balSenderBefore = await provider.getBalance(senderAddress);
    const balReceiverBefore = await provider.getBalance(receiverAddress);

    // - `provider.getBalance(address)` calls `eth_getBalance` and returns a `BigInt`.
    // - The value is in **wei**; 1 ETH = 10¹⁸ wei.

    console.log("Sender   balance (before):", balSenderBefore.toString());
    console.log("Receiver balance (before):", balReceiverBefore.toString());

    // - Print the balances in decimal form for logging.
    // - You will compare "before" and "after" to see how much value went through.

    // 7. Get current gas‑price / fee info (ethers v6 style)
    const feeData = await provider.getFeeData();
    const tx = {
      from: senderAddress,
      to: receiverAddress,
      value: ethers.parseEther("0.01"),
      gasLimit: 21000,
      gasPrice: feeData.gasPrice,
      chainId: 1337,
    };

    // - `provider.getFeeData()`:
    //     - Returns `gasPrice`, `maxFeePerGas`, `maxPriorityFeePerGas`.
    //     - On non‑EIP‑1559 chains (like `--network=dev`) you can just use `gasPrice`.
    // - `tx` fields:
    //   - `from`: sender address (for routing and gas‑payment).
    //   - `to`: receiver address.
    //   - `value`: amount to send.
    //     - `ethers.parseEther("0.01")` converts decimal `0.01` to wei (≈ 10¹⁶ wei).
    //   - `gasLimit: 21000`:
    //       - Standard gas for a simple ETH transfer.
    //   - `gasPrice: feeData.gasPrice`:
    //       - Current gas‑price suggested by the node, taken from `getFeeData()`.
    //   - `chainId: 1337`:
    //       - Must match `network.chainId`; protects against replay attacks across chains.

    // 8. Sign and send the transaction
    const txResponse = await wallet.sendTransaction(tx);
    console.log("Tx hash:", txResponse.hash);

    // - `wallet.sendTransaction(tx)`:
    //   - Builds a raw transaction from `tx`,
    //   - Signs it with the wallet’s `privateKey`,
    //   - Calls `eth_sendRawTransaction` on the node.
    // - `txResponse.hash` is the transaction hash (e.g., `0xe31e...`).
    // - You can later use this hash with `eth_getTransactionReceipt`.

    // 9. Wait for the transaction to be mined
    const receipt = await txResponse.wait();
    console.log("Block number:", receipt.blockNumber.toString());
    console.log("Status:", receipt.status === 1 ? "SUCCESS" : "FAILED");

    // - `txResponse.wait()` polls the node until the transaction is included in a block.
    // - `receipt.blockNumber`:
    //     - The block number where this transaction appears.
    //     - On your current Besu version this may never advance because PoW mining is effectively disabled.
    // - `receipt.status`:
    //     - `1` → transaction succeeded,
    //     - `0` → transaction reverted (failed).

    // 10. Read balances after the transaction
    const balSenderAfter = await provider.getBalance(senderAddress);
    const balReceiverAfter = await provider.getBalance(receiverAddress);

    console.log("Sender   balance (after):", balSenderAfter.toString());
    console.log("Receiver balance (after):", balReceiverAfter.toString());

    // - By comparing before and after balances you can:
    //   - Confirm receiver increased by ≈ 0.01 ETH,
    //   - Confirm sender decreased by 0.01 ETH + gas cost.

  } catch (err) {
    // 11. Error handling
    console.error("ERROR:", err.message);
    // - This catches:
    //   - network issues,
    //   - invalid RPC calls,
    //   - invalid addresses, gas, or chain‑ID mismatches.
  }
}

main();

// 12. Run the async function
// - `main()` is defined as async so we can `await` promises.
// - When you move to Quorum testnet, you only change:
//   - the provider URL,
//   - possibly the chain‑ID,
//   - and optionally the private key / addresses.
// - The rest of the logic (signing, sending, waiting, balance checks) stays the same.