const path = require('path');
const fs = require('fs-extra');
const ethers = require('ethers');

// Load user data
const users = require("../users.js"); // Change to users.json if using JSON

// RPC node details
const { tessera, besu } = require("../keys.js");
const host = besu.member1.url;
const accountPrivateKey = besu.member1.accountPrivateKey;

// Load contract ABI
const contractJsonPath = path.resolve(__dirname, '../../', 'contracts', 'Registry.json');
const contractJson = JSON.parse(fs.readFileSync(contractJsonPath));
const contractAbi = contractJson.abi;

// Load stored contract address
const address = require("../address.js");

if (!address.registry) {
    console.error("Error: No contract address found in address.js. Ensure the contract is deployed.");
    process.exit(1);
}

const contractAddress = address.registry;

// Function to get a user's role
async function getUserRole(provider, contractAbi, contractAddress, userKey) {
    const contract = new ethers.Contract(contractAddress, contractAbi, provider);
    const roleNum = await contract.getUserRole(userKey);
    const roleMapping = ["Patient", "CareProvider", "Researcher", "Regulator"];
    return roleMapping[roleNum] || "Unknown";
}

// Function to register a user
async function registerUser(provider, wallet, contractAbi, contractAddress, userKey, role) {
    const contract = new ethers.Contract(contractAddress, contractAbi, provider);
    const contractWithSigner = contract.connect(wallet);

    try {
        const tx = await contractWithSigner.registerUser(userKey, role);
        await tx.wait();
        console.log(`User ${userKey} registered with role: ${role}`);
    } catch (error) {
        console.error(`Error registering user ${userKey}:`, error.message);
    }
}

async function main() {
    const provider = new ethers.JsonRpcProvider(host);
    const wallet = new ethers.Wallet(accountPrivateKey, provider);

    for (const user of users) {
        try {
            const userKey = ethers.encodeBytes32String(user.key);
            console.log("user key",userKey);
            const role = user.role;
            
            console.log(`Registering user ${user.key}...`);
            await registerUser(provider, wallet, contractAbi, contractAddress, userKey, role);

            console.log(`Checking role for user ${user.key}...`);
            const assignedRole = await getUserRole(provider, contractAbi, contractAddress, userKey);
            console.log(`User ${user.key} has role: ${assignedRole}`);
        } catch (error) {
            console.error(`Error processing user ${user.key}:`, error.message);
        }
    }
}

if (require.main === module) {
    main();
}

module.exports = main;
