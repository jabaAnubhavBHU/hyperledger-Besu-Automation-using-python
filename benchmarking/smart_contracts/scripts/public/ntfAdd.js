const path = require("path");
const fs = require("fs-extra");
const ethers = require("ethers");

// RPC Node Details
const { tessera, besu } = require("../keys.js");
const host = besu.rpcnode.url;
const accountPrivateKey = besu.rpcnode.accountPrivateKey;

// Load NotificationManager contract ABI
const contractJsonPath = path.resolve(__dirname, "../../", "contracts", "NotificationManager.json");
const contractJson = JSON.parse(fs.readFileSync(contractJsonPath));
const contractAbi = contractJson.abi;

// Load stored contract addresses
const address = require("../address.js");

// Ensure contract address exists
if (!address.notification) {
    console.error("Error: No contract address found in address.js. Ensure the NotificationManager contract is deployed.");
    process.exit(1);
}

const contractAddress = address.notification;
console.log("Using existing NotificationManager contract at address:", contractAddress);

// Helper to add a notification
async function addNotification(provider, wallet, deployedContractAbi, deployedContractAddress, userKey, message) {
    const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);
    const contractWithSigner = contract.connect(wallet);
    
    const tx = await contractWithSigner.addNotification(userKey, message);
    await tx.wait();
    
    console.log("Notification added successfully!");
    return tx;
}

async function main() {
    const provider = new ethers.JsonRpcProvider(host);
    const wallet = new ethers.Wallet(accountPrivateKey, provider);

    try {
        const userKey = ethers.encodeBytes32String("UserKey8");

        console.log("Adding notification...");
        await addNotification(provider, wallet, contractAbi, contractAddress, userKey, "you have new requests!");
    } catch (error) {
        console.error("An error occurred!\nCheck if the user exists or if notifications are being added properly.", error);
    }
}

if (require.main === module) {
    main();
}

module.exports = main;
