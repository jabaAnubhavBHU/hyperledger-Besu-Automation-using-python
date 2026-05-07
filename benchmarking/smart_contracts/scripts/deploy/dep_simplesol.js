const path = require('path');
const fs = require('fs-extra');
const ethers = require('ethers');

// RPCNODE details
const { tessera, besu } = require("../keys.js");

const host = besu.rpcnode.url;
const accountPrivateKey = besu.rpcnode.accountPrivateKey;

// Helper function to read contract ABI and bytecode
const getContractData = (contractName) => {

    const contractJsonPath = path.resolve(
        __dirname,
        '../../',
        'contracts',
        `${contractName}.json`
    );

    const contractJson = JSON.parse(
        fs.readFileSync(contractJsonPath)
    );

    return {
        abi: contractJson.abi,
        bytecode: contractJson.evm.bytecode.object
    };
};

// Helper function to deploy contract
async function createContract(
    provider,
    wallet,
    contractAbi,
    contractBytecode
) {

    const factory = new ethers.ContractFactory(
        contractAbi,
        contractBytecode,
        wallet
    );

    // constructor(uint initVal)
    const contract = await factory.deploy(100);

    const deployed = await contract.waitForDeployment();

    return deployed;
}

// Function to update address.js
function updateContractAddresses(key, address) {

    const filePath = path.resolve(
        __dirname,
        "..",
        "address.js"
    );

    let existingData = {};

    if (fs.existsSync(filePath)) {
        existingData = require(filePath);
    }

    existingData[key] = address;

    const formattedData = Object.entries(existingData)
        .map(([k, v]) => `    ${k}: "${v}"`)
        .join(",\n");

    const fileContent =
`module.exports = {
${formattedData}
};
`;

    fs.writeFileSync(filePath, fileContent);

    console.log(`Updated ${key} address in address.js`);
}

// Main function
async function main() {

    const provider = new ethers.JsonRpcProvider(host);

    const wallet = new ethers.Wallet(
        accountPrivateKey,
        provider
    );

    try {

        // Deploy SimpleStorage contract
        const {
            abi: simpleStorageAbi,
            bytecode: simpleStorageBytecode
        } = getContractData('SimpleStorage');

        const simpleStorageContract = await createContract(
            provider,
            wallet,
            simpleStorageAbi,
            simpleStorageBytecode
        );

        const simpleStorageAddress =
            await simpleStorageContract.getAddress();

        console.log(
            "SimpleStorage contract deployed at address:",
            simpleStorageAddress
        );

        updateContractAddresses(
            "simpleStorage",
            simpleStorageAddress
        );

        // Interact with contract
        const contract = new ethers.Contract(
            simpleStorageAddress,
            simpleStorageAbi,
            provider
        );

        const contractWithSigner =
            contract.connect(wallet);

        // set value
        const tx = await contractWithSigner.set(500);

        await tx.wait();

        console.log("Value updated to 500");

        // get value
        const value = await contract.get();

        console.log(
            "Stored value:",
            value.toString()
        );

    } catch (error) {

        console.error(
            "An error occurred:",
            error
        );
    }
}

if (require.main === module) {
    main();
}

module.exports = main;