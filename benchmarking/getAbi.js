const fs = require('fs');

const data = JSON.parse(
  fs.readFileSync('./smart_contracts/contracts/SimpleStorage.json')
);

fs.writeFileSync(
  './smart_contracts/contracts/SimpleStorage.abi',
  JSON.stringify(data.abi, null, 2)
);  


console.log("ABI extracted");