const path = require("path");
const fs = require("fs-extra");
const ethers = require("ethers");

// RPC Node Details
const { tessera, besu } = require("../keys.js");
const host = besu.rpcnode.url;
const accountPrivateKey = besu.rpcnode.accountPrivateKey;

// Load Permission contract ABI
const contractJsonPath = path.resolve(__dirname, "../../", "contracts", "Permission.json");
const contractJson = JSON.parse(fs.readFileSync(contractJsonPath));
const contractAbi = contractJson.abi;

// Load stored contract addresses
const address = require("../address.js");

// Ensure contract address exists
if (!address.permission) {
    console.error("Error: No contract address found in address.js. Ensure the Permission contract is deployed.");
    process.exit(1);
}
const contractAddress = address.permission;
// Helper function to approve permission
async function approvePermission(provider, wallet, deployedContractAbi, deployedContractAddress, requesterKey, granterKey, newEncKey) {
    const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);
    const contractWithSigner = contract.connect(wallet);
    const tx = await contractWithSigner.approvePermission(requesterKey, granterKey, newEncKey);
    await tx.wait();
    console.log(`Permission approved. Data shared from ${granterKey} to ${requesterKey} with new encryption key.`);
    return tx;
}
async function main() {
    const provider = new ethers.JsonRpcProvider(host);
    const wallet = new ethers.Wallet(accountPrivateKey, provider);

    try {
        const requesterKey = ethers.encodeBytes32String("UserKey7");
        const granterKey = ethers.encodeBytes32String("UserKey8");
        const newEncKey = ethers.encodeBytes32String("NewEncKey789");
        console.log("Approving permission...");
        await approvePermission(provider, wallet, contractAbi, contractAddress, requesterKey, granterKey, newEncKey);
    } catch (error) {
        console.error("An error occurred! Ensure both users exist in the registry and try again.", error);
    }
}

if (require.main === module) {
    main();
}

module.exports = main;
