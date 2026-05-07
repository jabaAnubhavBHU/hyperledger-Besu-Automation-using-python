'use strict';

const { WorkloadModuleBase } =
    require('@hyperledger/caliper-core');

class SetWorkload extends WorkloadModuleBase {

    async submitTransaction() {

        const value =
            Math.floor(Math.random() * 1000);

        const request = {
            contract: 'SimpleStorage',
            verb: 'set',
            args: [value]
        };

        await this.sutAdapter.sendRequests(request);
    }
}

function createWorkloadModule() {
    return new SetWorkload();
}

module.exports.createWorkloadModule =
    createWorkloadModule;