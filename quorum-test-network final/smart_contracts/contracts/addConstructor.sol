// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.10;

contract AddConstructor {
    /// @notice Stores the result of the last addition
    uint256 public result;

    /// @param init Initial value of `result`
    constructor(uint256 init) {
        result = init;
    }

    /// @notice Adds two values and stores the result
    /// @param a First operand
    /// @param b Second operand
    /// @return sum Result of a + b
    function add(uint256 a, uint256 b) external returns (uint256 sum) {
        sum = a + b;
        result = sum;
    }
        // Optional: separate read‑only getter
    function getResult() public view returns (uint) {
        return result;
    }
}
