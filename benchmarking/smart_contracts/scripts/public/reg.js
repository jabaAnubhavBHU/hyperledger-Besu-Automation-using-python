const path = require('path');
const fs = require('fs-extra');
const ethers = require('ethers');

// RPCNODE details of the node that runs the transaction, (not the user to be registered!)
const { tessera, besu } = require("../keys.js");
const host = besu.member1.url;
const accountPrivateKey = besu.member1.accountPrivateKey;

// Load contract ABI
const contractJsonPath = path.resolve(__dirname, '../../', 'contracts', 'Registry.json');
const contractJson = JSON.parse(fs.readFileSync(contractJsonPath));
const contractAbi = contractJson.abi;

// Load stored contract address
const address = require("../address.js"); 

// Ensure contract address exists
if (!address.registry) {
    console.error("Error: No contract address found in address.js. Ensure the contract is deployed.");
    process.exit(1);
}

const contractAddress = address.registry;
// console.log("Using existing contract at address:", contractAddress);

// Helper to check user role
async function getUserRole(provider, deployedContractAbi, deployedContractAddress, userKey) {
    const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);
    const rolenum = await contract.getUserRole(userKey);
    const roleMapping = ["Patient", "CareProvider", "Researcher", "Regulator"];
    const role = roleMapping[rolenum];
    console.log("The user is a : " + role);
    return role;
}

// Helper to register a user
async function registerUser(provider, wallet, deployedContractAbi, deployedContractAddress, userKey, role) {
    const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);
    const contractWithSigner = contract.connect(wallet);
    const tx = await contractWithSigner.registerUser(userKey, role);
    await tx.wait();
    console.log("User registered with role: " + role);
    return tx;
}

async function main() {
    const provider = new ethers.JsonRpcProvider(host);
    const wallet = new ethers.Wallet(accountPrivateKey, provider);

    try {
        
        const userKey = ethers.encodeBytes32String("UserKeyc1");
        const role = "CareProvider"; // Change this to test different roles
        console.log("Registering a user...");
        await registerUser(provider, wallet, contractAbi, contractAddress, userKey, role);

        console.log("Checking the user's role...");
        await getUserRole(provider, contractAbi, contractAddress, userKey);
    } catch (error) {
        console.error("An error occurred!");
    }
}

if (require.main === module) {
    main();
}

module.exports = main;


// register user with public key and role
// check user with his public key