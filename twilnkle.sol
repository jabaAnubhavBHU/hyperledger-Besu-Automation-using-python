/ SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.8.2 <0.9.0;

contract WSMPSolver {

    struct Worker {
        address addr;
        uint256 deposit;
        bytes32 solHash;
        uint256[] solution; // binary vector: selected sets
        bool revealed;
        bool valid;
    }

    address public procurer;

    // Problem definition
    uint256 public numElements;
    uint256 public numSets;

    uint256[] public setCosts; // size m
    uint256[] public coverageRequirement; // size n

    // coverageMatrix[i][j] = coverage of element i by set j
    mapping(uint256 => mapping(uint256 => uint256)) public coverageMatrix;

    // Timing
    uint256 public t_s;
    uint256 public t_sf;
    uint256 public startTime;

    uint256 public rewardPool;

    bool public problemActive;

    Worker[] public workers;
    address[] public winners;

    uint256 public bestCost = type(uint256).max;
    uint256[] public bestSolution;

    bool public evaluationStatus;   //keeps tab on whther evaluation is done

    constructor() {
        procurer = msg.sender;
    }

    // 1. Define WSMC problem
    function NewProblem(
        uint256 _n,
        uint256 _m,
        uint256[] memory _setCosts,
        uint256[] memory _coverageReq,
        uint256[] memory flatMatrix,
        uint256 _t_s,
        uint256 _t_sf
    ) external payable {
      
        require(msg.sender == procurer, "Only procurer");
        require(!problemActive, "Problem already active");

        problemActive = true;
        numElements = _n;                   //number of items in the set
        numSets = _m;                       // number of bundles offered
        setCosts = _setCosts;               //cost of bundles/sets offered
        coverageRequirement = _coverageReq; //requirement of every item 

        // Load coverage matrix (flattened input)
        uint256 k = 0;
        for (uint256 i = 0; i < _n; i++) {
            for (uint256 j = 0; j < _m; j++) {
                coverageMatrix[i][j] = flatMatrix[k++];
            }
        }

        t_s = _t_s;
        t_sf = _t_sf;
        startTime = block.timestamp;

        rewardPool = msg.value;
        problemActive= true;
    }

    // 2. Accept problem
    function acceptProblem() external payable {
        require(problemActive, "No active problem");

        require(block.timestamp <= startTime + t_s, "Acceptance window closed");
        workers.push(Worker({
            addr: msg.sender,
            deposit: msg.value,
            solHash: 0,
            solution: new uint256[](0),
            revealed: false,
            valid: false
        }));
    }

    // 3. Submit hash
    function submitHash(uint256 workerId, bytes32 h) external {
        require(block.timestamp <= startTime + t_s, "Hash phase over");
        require(msg.sender == workers[workerId].addr);

        workers[workerId].solHash = h;
    }

    // 4. Reveal solution
    function revealSolution(
        uint256 workerId,
        uint256[] memory sol
    ) external {

        require(block.timestamp > startTime + t_s && block.timestamp <= startTime + t_s + t_sf,"Reveal phase invalid");

        Worker storage w = workers[workerId];
        require(msg.sender == w.addr);

        require(keccak256(abi.encode(sol)) == w.solHash,"Hash mismatch");

        w.solution = sol;
        w.revealed = true;
    }

    //  Check feasibility
    function isFeasible(uint256[] memory sol)
        internal view returns (bool)
    {
        uint256[] memory coverage = new uint256[](numElements);

        for (uint256 j = 0; j < numSets; j++) {
            if (sol[j] == 1) {
                for (uint256 i = 0; i < numElements; i++) {
                    coverage[i] += coverageMatrix[i][j];
                }
            }
        }

        for (uint256 i = 0; i < numElements; i++) {
            if (coverage[i] < coverageRequirement[i]) {
                return false;
            }
        }

        return true;
    }

    //  Compute cost
    function computeCost(uint256[] memory sol)
        internal view returns (uint256)
    {
        uint256 cost = 0;

        for (uint256 j = 0; j < numSets; j++) {
            if (sol[j] == 1) {
                cost += setCosts[j];
            }
        }

        return cost;
    }

    // 5. Evaluation
    function evaluate() external {

        //require(msg.sender == procurer);
        require(block.timestamp > startTime + t_s + t_sf);

        for (uint256 i = 0; i < workers.length; i++) {
            Worker storage w = workers[i];

            if (w.revealed && isFeasible(w.solution)) {
                uint256 cost = computeCost(w.solution);

                if (cost < bestCost) {
                    bestCost = cost;
                    bestSolution = w.solution;
                    winners = new address[](1);
                    winners[0] = w.addr;
                } else if (cost == bestCost) {
                    winners.push(w.addr);
                }

                w.valid = true;
                (bool success, ) = payable(w.addr).call{value: w.deposit}("");
                require(success, "Transfer failed");
            } else {
                (bool success, ) = payable(procurer).call{value: w.deposit}("");
                require(success, "Transfer failed");
            }
        }
        evaluationStatus=true;
    }

    // 6. Settlement
    function settle() external {
        //require(msg.sender == procurer);
        require(evaluationStatus== true, "Evaluation yet to be done!");

        uint256 share = rewardPool / winners.length;

        for (uint256 i = 0; i < winners.length; i++) {
            (bool success, ) = payable(winners[i]).call{value: share}("");
            require(success, "Transfer failed");
        }
    }
}
