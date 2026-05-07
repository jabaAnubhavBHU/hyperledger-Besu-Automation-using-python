const path = require("path");
const fs = require("fs-extra");
const ethers = require("ethers");

// RPC Node Details
const { tessera, besu } = require("../keys.js");
const host = besu.rpcnode.url;
const accountPrivateKey = besu.rpcnode.accountPrivateKey;

// Load Metadata contract ABI
const contractJsonPath = path.resolve(__dirname, "../../", "contracts", "Metadata.json");
const contractJson = JSON.parse(fs.readFileSync(contractJsonPath));
const contractAbi = contractJson.abi;

// Load stored contract addresses
const address = require("../address.js");

// Ensure contract address exists
if (!address.metadata) {
    console.error("Error: No contract address found in address.js. Ensure the Metadata contract is deployed.");
    process.exit(1);
}

const contractAddress = address.metadata;
console.log("Using existing Metadata contract at address:", contractAddress);

// Helper function to add EHR data
async function addEHRdata(provider, wallet, deployedContractAbi, deployedContractAddress, ownerKey, dataType, HI, encKey) {
    const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);
    const contractWithSigner = contract.connect(wallet);
    
    const tx = await contractWithSigner.addEHRdata(ownerKey, dataType, HI, encKey);
    await tx.wait();
    
    console.log("EHR Data added successfully!");
    return tx;
}

// Helper function to search EHR data for a user
async function searchData(provider, deployedContractAbi, deployedContractAddress, userKey) {
    const contract = new ethers.Contract(deployedContractAddress, deployedContractAbi, provider);
    
    const ehrData = await contract.searchData(userKey);
    console.log(`EHR Data for user ${userKey}:`);
    ehrData.forEach((data, index) => {
        console.log(`[${index + 1}] DataType: ${data.dataType}, HI: ${data.HI}, EncKey: ${data.encKey}`);
    });
    return ehrData;
}

async function main() {
    const provider = new ethers.JsonRpcProvider(host);
    const wallet = new ethers.Wallet(accountPrivateKey, provider);

    try {
        const userKey = ethers.encodeBytes32String("UserKey8");
        const dataType = 1;  // Blood Test (Assuming enum mapping: COVID = 0, Blood = 1, etc.)
        const HI = ethers.encodeBytes32String("HealthInfo124");
        const encKey = ethers.encodeBytes32String("symmetric124");

        console.log("Adding EHR data...");
        await addEHRdata(provider, wallet, contractAbi, contractAddress, userKey, dataType, HI, encKey);

        console.log("Fetching EHR data...");
        await searchData(provider, contractAbi, contractAddress, userKey);
    } catch (error) {
        console.error("An error occurred! Ensure that the user exists in the registry and try again.", error);
    }
}

if (require.main === module) {
    main();
}

module.exports = main;
