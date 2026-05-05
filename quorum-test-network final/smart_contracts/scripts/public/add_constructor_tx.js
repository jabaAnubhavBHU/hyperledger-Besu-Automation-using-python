// you can find meaning of each line with comments at the end of code


const path = require('path');
const fs = require('fs-extra');
const ethers = require('ethers');

// 1. RPC node and account
const { tessera, besu } = require("../keys.js");
const host = besu.rpcnode.url;                    // e.g., http://localhost:21001
const accountPrivateKey = besu.rpcnode.accountPrivateKey;

// 2. Load AddTwoValues ABI + bytecode
const contractJsonPath = path.resolve(__dirname, '../../', 'contracts', 'AddConstructor.json');
const contractJson = JSON.parse(fs.readFileSync(contractJsonPath));
const contractAbi = contractJson.abi;
const contractBytecode = contractJson.evm.bytecode.object;   // hex string


// 3. Read the stored result
async function getResultAtAddress(provider, deployedContractAbi, deployedContractAddress) {
  // ✅ Correct: contract(target, abi, provider)
  const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);
  const res = await contract.getResult();
  console.log("On-chain result:", res.toString());
  return res;
}

// 4. Call add(a, b) (write)
async function addTwoValuesAtAddress(provider, wallet, deployedContractAbi, deployedContractAddress, a, b) {
  // ✅ Use provider + wallet correctly
  const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);
  const contractWithSigner = contract.connect(wallet);
  const tx = await contractWithSigner.add(a, b);
  await tx.wait();
  console.log("add(%d, %d) confirmed.", a, b);
  return tx;
}

// 5. Deploy function (no constructor arg)
async function createContract(provider, wallet, contractAbi, contractBytecode) {
  const factory = new ethers.ContractFactory(contractAbi, contractBytecode, wallet);
  const contract = await factory.deploy(0);   // passing args as the contructor needs to be initalized

  const deployed = await contract.waitForDeployment();
  return contract;
}

// 6. Main flow
async function main() {
  const provider = new ethers.JsonRpcProvider(host);
  const wallet = new ethers.Wallet(accountPrivateKey, provider);

  console.log("Deploying AddTwoValues...");
  createContract(provider, wallet, contractAbi, contractBytecode)
    .then(async (contract) => {
      const contractAddress = await contract.getAddress();
      console.log("AddTwoValues deployed at address:", contractAddress);

      // ✅ Pass address string, not ABI
      await addTwoValuesAtAddress(provider, wallet, contractAbi, contractAddress, 10, 20);
      await getResultAtAddress(provider, contractAbi, contractAddress);

      await addTwoValuesAtAddress(provider, wallet, contractAbi, contractAddress, 5, 7);
      await getResultAtAddress(provider, contractAbi, contractAddress);
    })
    .catch((err) => {
      console.error("Deployment or interaction failed:", err);
      console.error("Stack trace:", err.stack);
    });
}

if (require.main === module) {
  main();
}

module.exports = main;



// // Load Node.js path module to build absolute file paths
// const path = require('path');

// // Load fs-extra (enhanced fs) to read JSON safely
// const fs = require('fs-extra');

// // Load ethers v6 for Ethereum / Quorum interactions
// const ethers = require('ethers');


// // 1. RPC node and account setup (Quorum Dev‑Quickstart style)

// // Import keys.js that exports { tessera, besu }
// const { tessera, besu } = require("../keys.js");

// // Use the RPC URL of one Quorum validator, e.g., http://localhost:21001
// const host = besu.rpcnode.url;

// // Use the private key of an account that is funded on your Quorum network
// const accountPrivateKey = besu.rpcnode.accountPrivateKey;


// // 2. Load AddTwoValues ABI + bytecode

// // Build path to contracts/AddTwoValues.json (relative to this script)
// const contractJsonPath = path.resolve(__dirname, '../../', 'contracts', 'AddTwoValues.json');

// // Read the JSON file synchronously and parse it
// const contractJson = JSON.parse(fs.readFileSync(contractJsonPath));

// // Extract the ABI (array of function/event descriptions)
// const contractAbi = contractJson.abi;

// // Extract the bytecode hex string from the EVM section of the JSON
// const contractBytecode = contractJson.evm.bytecode.object;   // bytecode hex string


// // 3. Helper: read the stored result on the deployed contract

// /**
//  * Reads the current `result` value from the deployed contract using `getResult()`.
//  *
//  * @param provider - ethers.JsonRpcProvider connected to your Quorum node
//  * @param deployedContractAbi - ABI of the contract (array)
//  * @param deployedContractAddress - string address of the deployed contract (e.g., 0x...)
//  * @returns - the numeric result as a BigNumber (toString() gives decimal string)
//  */
// async function getResultAtAddress(provider, deployedContractAbi, deployedContractAddress) {
//   // Create a contract instance at the given address + ABI + provider
//   const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);

//   // Call the view function `getResult()` (read‑only, no gas, uses `eth_call`)
//   const res = await contract.getResult();

//   // Print the obtained value (cast to decimal string)
//   console.log("On-chain result:", res.toString());

//   // Return the value for further use (if needed)
//   return res;
// }


// // 4. Helper: call add(a, b) to write the result on‑chain

// /**
//  * Calls `add(a, b)` on the deployed contract and waits for the transaction to be mined.
//  *
//  * @param provider - ethers.JsonRpcProvider connected to your Quorum node
//  * @param wallet - ethers.Wallet with the signing private key
//  * @param deployedContractAbi - ABI of the contract (array)
//  * @param deployedContractAddress - string address of the deployed contract
//  * @param a - first uint to add
//  * @param b - second uint to add
//  * @returns - the transaction receipt (after waiting)
//  */
// async function addTwoValuesAtAddress(provider, wallet, deployedContractAbi, deployedContractAddress, a, b) {
//   // Create a contract instance bound to the address + ABI + provider
//   const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);

//   // Attach the wallet (signer) to the contract so it can send transactions
//   const contractWithSigner = contract.connect(wallet);

//   // Send a transaction to call `add(a, b)`, which:
//   // - Runs the logic,
//   // - Stores the result in `result`,
//   // - Returns the sum.
//   const tx = await contractWithSigner.add(a, b);

//   // Wait until the transaction is included in a block (Quorum IBFT 2.0)
//   await tx.wait();

//   // Print that the add call was confirmed
//   console.log("add(%d, %d) confirmed.", a, b);

//   // Return the transaction object (for inspection, if needed)
//   return tx;
// }


// // 5. Helper: deploy the AddTwoValues contract

// /**
//  * Deploys the AddTwoValues contract to the Quorum network using a wallet.
//  *
//  * @param provider - ethers.JsonRpcProvider connected to your Quorum node
//  * @param wallet - ethers.Wallet with the signing private key
//  * @param contractAbi - ABI of the contract (array)
//  * @param contractBytecode - hex string bytecode of the contract
//  * @returns - the deployed Contract instance
//  */
// async function createContract(provider, wallet, contractAbi, contractBytecode) {
//   // Construct a ContractFactory that knows how to deploy the contract
//   const factory = new ethers.ContractFactory(contractAbi, contractBytecode, wallet);

//   // Send a contract‑creation transaction (no constructor args in this case)
//   const contract = await factory.deploy();   // no args

//   // Wait until the deployment transaction is mined and the contract is live
//   const deployed = await contract.waitForDeployment();

//   // Return the contract instance so you can call its methods
//   return contract;
// }


// // 6. Main deployment and interaction flow

// /**
//  * Main async function that:
//  * - Connects to the Quorum node,
//  * - Deploys AddTwoValues,
//  * - Calls add(10,20) and add(5,7),
//  * - Reads the result after each call.
//  */
// async function main() {
//   // Create a JSON‑RPC provider pointing to your Quorum validator (e.g., http://localhost:21001)
//   const provider = new ethers.JsonRpcProvider(host);

//   // Create a wallet (signer) from your private key, connected to that provider
//   const wallet = new ethers.Wallet(accountPrivateKey, provider);

//   console.log("Deploying AddTwoValues...");
//   // Deploy AddTwoValues using the contract ABI + bytecode + wallet
//   createContract(provider, wallet, contractAbi, contractBytecode)
//     .then(async (contract) => {
//       // Get the on‑chain deployed contract address (e.g., 0x49f8...)
//       const contractAddress = await contract.getAddress();
//       console.log("AddTwoValues deployed at address:", contractAddress);

//       // --- First test: add(10, 20) ---

//       // Call add(10, 20) → result = 30, stored in `result`
//       await addTwoValuesAtAddress(provider, wallet, contractAbi, contractAddress, 10, 20);

//       // Read the stored result and print it
//       await getResultAtAddress(provider, contractAbi, contractAddress);

//       // --- Second test: add(5, 7) ---

//       // Call add(5, 7) → result = 12, overwrites previous value
//       await addTwoValuesAtAddress(provider, wallet, contractAbi, contractAddress, 5, 7);

//       // Read the updated result
//       await getResultAtAddress(provider, contractAbi, contractAddress);
//     })
//     .catch((err) => {
//       // Catch any errors during deployment or interaction
//       console.error("Deployment or interaction failed:", err);
//       console.error("Stack trace:", err.stack);
//     });
// }

// // If this script is run directly (node add_tx.js), call main()
// if (require.main === module) {
//   main();
// }

// // Export main so this module can be reused in other scripts if needed
// module.exports = main;
