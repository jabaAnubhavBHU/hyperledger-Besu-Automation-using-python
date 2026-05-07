// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.10;

contract Add {
    // Optional: store the result on‑chain
    uint public result;

    function add(uint a, uint b) public returns (uint) {
        // Simple addition
        result = a + b;
        return result;
    }

    // Optional: separate read‑only getter
    function getResult() public view returns (uint) {
        return result;
    }
}
