// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DynamicFare {
    address public owner;
    uint256 public currentFare;
    uint256 public passengerThreshold;
    uint256 public dailyPassengerCount;
    uint256 public lastUpdateTimestamp;
    uint256 public fareDecreasePercentage;
    
    event FareAdjusted(
        uint256 newFare, 
        uint256 passengerCount, 
        string reason,
        uint256 timestamp
    );
    
    constructor(
        uint256 _initialFare,
        uint256 _threshold,
        uint256 _decreasePercentage
    ) {
        owner = msg.sender;
        currentFare = _initialFare;
        passengerThreshold = _threshold;
        fareDecreasePercentage = _decreasePercentage;
        lastUpdateTimestamp = block.timestamp;
    }
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    function updatePassengerCount(
        uint256 _newCount, 
        string memory _reason
    ) external onlyOwner {
        // Reset counter if it's a new day
        if (block.timestamp > lastUpdateTimestamp + 1 days) {
            dailyPassengerCount = 0;
        }
        
        dailyPassengerCount = _newCount;
        lastUpdateTimestamp = block.timestamp;
        
        // Adjust fare if below threshold
        if (dailyPassengerCount < passengerThreshold) {
            uint256 decreaseAmount = (currentFare * fareDecreasePercentage) / 100;
            currentFare -= decreaseAmount;
            emit FareAdjusted(
                currentFare, 
                dailyPassengerCount, 
                _reason,
                block.timestamp
            );
        }
    }
    
    function setParameters(
        uint256 _newThreshold,
        uint256 _newDecreasePercentage
    ) external onlyOwner {
        require(_newDecreasePercentage <= 50, "Decrease percentage too high");
        passengerThreshold = _newThreshold;
        fareDecreasePercentage = _newDecreasePercentage;
    }
    
    function getCurrentFare() external view returns (uint256) {
        return currentFare;
    }
    
    function getParameters() external view returns (
        uint256, uint256, uint256, uint256
    ) {
        return (
            currentFare,
            passengerThreshold,
            fareDecreasePercentage,
            dailyPassengerCount
        );
    }
}