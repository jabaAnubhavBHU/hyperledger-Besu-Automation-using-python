const path = require('path');
const fs = require('fs-extra');
const ethers = require('ethers');

// RPCNODE details
const { tessera, besu } = require("../keys.js");

const host = besu.rpcnode.url;
const accountPrivateKey = besu.rpcnode.accountPrivateKey;

// ==========================================================
// VALIDATE INPUT
// ==========================================================

if (process.argv.length < 3) {

    console.error(
        "Usage: node deployContract.js <ContractName>"
    );

    process.exit(1);
}

// Contract name passed dynamically
const CONTRACT_NAME = process.argv[2];

// ==========================================================
// HELPER: READ ABI + BYTECODE
// ==========================================================

const getContractData = (contractName) => {

    const contractJsonPath = path.resolve(
        __dirname,
        '../../',
        'contracts',
        `${contractName}.json`
    );

    if (!fs.existsSync(contractJsonPath)) {

        throw new Error(
            `Contract JSON not found: ${contractJsonPath}`
        );
    }

    const contractJson = JSON.parse(
        fs.readFileSync(contractJsonPath)
    );

    return {
        abi: contractJson.abi,
        bytecode: contractJson.evm.bytecode.object
    };
};

// ==========================================================
// HELPER: DEPLOY CONTRACT
// ==========================================================

async function createContract(
    wallet,
    contractAbi,
    contractBytecode
) {

    const factory = new ethers.ContractFactory(
        contractAbi,
        contractBytecode,
        wallet
    );

    // Generic deployment
    // NOTE:
    // Assumes either:
    //   - no constructor
    //   - constructor(uint initVal)
    //
    // Adjust if contracts differ.
    let contract;

    try {

        contract = await factory.deploy(100);

    } catch (err) {

        // fallback for empty constructor
        contract = await factory.deploy();
    }

    const deployed = await contract.waitForDeployment();

    return deployed;
}

// ==========================================================
// HELPER: UPDATE address.js
// ==========================================================

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

    console.log(
        `Updated ${key} address in address.js`
    );
}

// ==========================================================
// MAIN
// ==========================================================

async function main() {

    const provider = new ethers.JsonRpcProvider(host);

    const wallet = new ethers.Wallet(
        accountPrivateKey,
        provider
    );

    try {

        console.log(
            `\n=== Deploying ${CONTRACT_NAME} ===\n`
        );

        // --------------------------------------------------
        // READ CONTRACT DATA
        // --------------------------------------------------

        const {
            abi,
            bytecode
        } = getContractData(CONTRACT_NAME);

        // --------------------------------------------------
        // DEPLOY CONTRACT
        // --------------------------------------------------

        const deployedContract = await createContract(
            wallet,
            abi,
            bytecode
        );

        const contractAddress =
            await deployedContract.getAddress();

        console.log(
            `${CONTRACT_NAME} deployed at address:`,
            contractAddress
        );

        // --------------------------------------------------
        // UPDATE ADDRESS FILE
        // --------------------------------------------------

        updateContractAddresses(
            CONTRACT_NAME,
            contractAddress
        );

        // --------------------------------------------------
        // OPTIONAL TEST INTERACTION
        // --------------------------------------------------

        const contract = new ethers.Contract(
            contractAddress,
            abi,
            provider
        );

        const contractWithSigner =
            contract.connect(wallet);

        // Try generic "set"
        try {

            const tx =
                await contractWithSigner.set(500);

            await tx.wait();

            console.log("Value updated to 500");

        } catch (err) {

            console.log(
                "No set() method found, skipping..."
            );
        }

        // Try generic "get"
        try {

            const value = await contract.get();

            console.log(
                "Stored value:",
                value.toString()
            );

        } catch (err) {

            console.log(
                "No get() method found, skipping..."
            );
        }

    } catch (error) {

        console.error(
            "An error occurred:",
            error
        );
    }
}

// ==========================================================
// ENTRY
// ==========================================================

if (require.main === module) {
    main();
}

module.exports = main;