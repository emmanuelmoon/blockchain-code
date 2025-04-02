import os
import json
import google.generativeai as genai
from web3 import Web3
from dotenv import load_dotenv
from solcx import install_solc, compile_source
import time

load_dotenv()

class GeminiContractDeployer:
    SUPPORTED_MODELS = {
        # 'gemini-pro': "models/gemini-pro",
        # 'gemini-1.0-pro': "models/gemini-1.0-pro",
        'gemini-1.5-pro': "models/gemini-1.5-pro"
    }

    def __init__(self):
        self.validate_config()
        self.init_web3()
        self.init_gemini()
        install_solc('0.8.0')

    def validate_config(self):
        """Validate all required configuration"""
        required_vars = {
            "RPC_URL": os.getenv("RPC_URL"),
            "CHAIN_ID": os.getenv("CHAIN_ID"),
            "DEPLOYER_PRIVATE_KEY": os.getenv("DEPLOYER_PRIVATE_KEY"),
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
        }
        
        if None in required_vars.values():
            missing = [k for k, v in required_vars.items() if v is None]
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        self.rpc_url = required_vars["RPC_URL"]
        self.chain_id = int(required_vars["CHAIN_ID"])
        self.private_key = required_vars["DEPLOYER_PRIVATE_KEY"]
        self.gemini_key = required_vars["GEMINI_API_KEY"]

    def init_web3(self):
        """Initialize Web3 connection"""
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to blockchain RPC")
        self.account = self.w3.eth.account.from_key(self.private_key)

    def init_gemini(self):
        """Initialize Gemini AI with model fallback"""
        genai.configure(api_key=self.gemini_key)
        
        # Try available models in order
        for model_name, model_path in self.SUPPORTED_MODELS.items():
            try:
                self.gemini = genai.GenerativeModel(model_path)
                # Test with a simple prompt
                response = self.gemini.generate_content("Test connection")
                if response.text:
                    print(f"✓ Connected to Gemini model: {model_name}")
                    return
            except Exception as e:
                print(f"⚠️ Failed to initialize {model_name}: {str(e)}")
                continue
        
        raise ConnectionError("Could not connect to any supported Gemini model")

    def ai_analyze_demand(self, passenger_count, historical_data=None):
        """Use Gemini AI to analyze passenger demand and recommend fare parameters"""
        try:
            prompt = f"""
            As a transportation economics AI agent, analyze this scenario:
            - Current passenger count: {passenger_count}
            - Historical data: {historical_data or 'No historical data available'}
            
            Recommend optimal parameters for a dynamic fare system:
            1. Initial base fare (in wei, typically 100-500)
            2. Passenger threshold for fare adjustments
            3. Percentage decrease when below threshold
            
            Considerations:
            - Maintain profitability
            - Encourage ridership during low demand
            - Account for market conditions
            - Balance supply and demand
            
            Respond ONLY with valid JSON in this exact format:
            {{
                "initial_fare": integer,
                "threshold": integer,
                "decrease_pct": integer,
                "reason": "brief explanation of your recommendation"
            }}
            """
            
            response = self.gemini.generate_content(prompt)
            
            # Extract JSON from Gemini's response
            json_str = response.text.strip()
            if '```json' in json_str:
                json_str = json_str.split('```json')[1].split('```')[0].strip()
            elif '```' in json_str:
                json_str = json_str.split('```')[1].split('```')[0].strip()
            
            result = json.loads(json_str)
            
            return (
                int(result["initial_fare"]),
                int(result["threshold"]),
                int(result["decrease_pct"]),
                result.get("reason", "No reason provided")
            )
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {str(e)}")
            # Fallback to reasonable defaults
            return (100, 500, 10, "Using default values after AI failure")

    def compile_contract(self):
        """Compile the Solidity contract"""
        with open('DynamicFare.sol', 'r') as file:
            solidity_source = file.read()
        
        return compile_source(
            solidity_source,
            output_values=['abi', 'bin'],
            solc_version='0.8.0',
            optimize=True,
            optimize_runs=200
        )

    def deploy_contract(self, initial_fare, threshold, decrease_pct):
        """Deploy contract to blockchain"""
        compiled = self.compile_contract()
        contract_id, contract_interface = compiled.popitem()
        
        contract = self.w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        # Build transaction
        transaction = contract.constructor(
            initial_fare,
            threshold,
            decrease_pct
        ).build_transaction({
            'chainId': self.chain_id,
            'gas': 2000000,
            'maxFeePerGas': self.w3.to_wei('50', 'gwei'),
            'maxPriorityFeePerGas': self.w3.to_wei('2', 'gwei'),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        
        # Sign and send
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt.contractAddress

    def run(self):
        """Main execution flow"""
        print("\n🚀 Gemini-Powered Dynamic Fare Deployment")
        print("---------------------------------------")
        print(f"🔗 Connected to: {self.rpc_url}")
        print(f"🆔 Chain ID: {self.chain_id}")
        print(f"👛 Account: {self.account.address}")
        print(f"💰 Balance: {self.w3.from_wei(self.w3.eth.get_balance(self.account.address), 'ether'):.4f} ETH")
        
        try:
            # Get passenger data
            passenger_count = int(input("\nEnter today's passenger count: "))
            historical = input("Enter historical passenger counts (comma separated, optional): ")
            
            historical_data = [int(x.strip()) for x in historical.split(',')] if historical else None
            
            # Get AI recommendation
            print("\n🤖 Consulting Gemini AI for optimal fare parameters...")
            initial_fare, threshold, decrease_pct, reason = self.ai_analyze_demand(
                passenger_count,
                historical_data
            )
            
            print(f"\n📊 AI Recommendation:")
            print(f"   - Initial Fare: {initial_fare} wei")
            print(f"   - Threshold: {threshold} passengers")
            print(f"   - Decrease Percentage: {decrease_pct}%")
            print(f"   - Reasoning: {reason}")
            
            # Confirm deployment
            if input("\nProceed with deployment? (y/n): ").lower() == 'y':
                print("\n⏳ Deploying contract...")
                contract_address = self.deploy_contract(initial_fare, threshold, decrease_pct)
                print(f"\n✅ Contract successfully deployed!")
                print(f"📌 Address: {contract_address}")
                print(f"🔗 View on Etherscan: https://sepolia.etherscan.io/address/{contract_address}")
            else:
                print("🚫 Deployment cancelled")
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            self.handle_error(e)

    def handle_error(self, error):
        """Provide specific guidance for common errors"""
        error_msg = str(error).lower()
        
        if "insufficient funds" in error_msg:
            print("\n💡 Solution: Get Sepolia ETH from:")
            print("   - https://sepoliafaucet.com")
            print("   - https://faucet.quicknode.com/ethereum/sepolia")
        elif "nonce too low" in error_msg:
            print("\n💡 Solution: Wait for pending transactions to complete")
        elif "chain id" in error_msg:
            print("\n💡 Solution: Verify your .env has correct chain ID")
        elif "quota" in error_msg or "limit" in error_msg:
            print("\n💡 Gemini API Error: You may have exceeded your API quota")
        elif "model" in error_msg:
            print("\n💡 Gemini Model Error: Try updating the model name in SUPPORTED_MODELS")
            print("Available models:", list(self.SUPPORTED_MODELS.keys()))
        else:
            print("\n💡 Check your configuration and try again")

if __name__ == "__main__":
    try:
        GeminiContractDeployer().run()
    except Exception as e:
        print(f"\n🔥 Initialization error: {str(e)}")
        print("Please check your .env file configuration")