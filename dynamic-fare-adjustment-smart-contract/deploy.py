import os
import json
import google.generativeai as genai
from web3 import Web3
from dotenv import load_dotenv
from solcx import install_solc, compile_source
import time
import joblib
import pandas as pd
import numpy as np

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
        self.load_ml_model()
        install_solc('0.8.0')

    def load_ml_model(self, model_path='fare_model.joblib'):
        """Load the pre-trained ML model"""
        try:
            self.ml_model = joblib.load(model_path)
            print("✓ Custom ML model loaded successfully")
            self.model_loaded = True
        except Exception as e:
            print(f"⚠️ Failed to load ML model: {str(e)}")
            self.model_loaded = False

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

    def predict_discount(self, features):
        if not self.model_loaded:
            return None
            
        try:
            # Convert features to correct format, assuming features is a dict
            # with keys matching your training data columns
            df = pd.DataFrame({
                'x1_hour': [features['x1_hour']],
                'x2_passenger_count': [features['x2_passenger_count']],
                'x3_vehicle_count': [features['x3_vehicle_count']],
                'x4_weather_condition': [features['x4_weather_condition']],
                'x5_day_type': [features['x5_day_type']],
                'occupancy_rate': [features['occupancy_rate']]
            })
            
            # Make prediction and keep as float
            discount = float(self.ml_model.predict(df)[0]) * 100
            
            # Return the raw discount value without converting to int
            return discount
        except Exception as e:
            print(f"⚠️ ML prediction failed: {str(e)}")
            return None

    def ai_analyze_demand(self, passenger_count, features=None, historical_data=None):
        """Use Gemini AI to analyze demand but preserve the ML discount prediction"""
        # Default values
        initial_fare = 100  # Wei
        threshold = 500     # Passengers
        decrease_pct = 10.0 # Percentage (as float)
        
        # First get ML prediction if features are provided
        ml_discount = None
        if features and self.model_loaded:
            ml_discount = self.predict_discount(features)
            if ml_discount is not None:
                decrease_pct = ml_discount
        
        # Now use Gemini only for initial_fare and threshold, not for discount
        try:
            # Build features string for Gemini
            features_str = ""
            if features:
                features_str = "\n".join([
                    f"- Time of day: {features['x1_hour']}:00",
                    f"- Passenger count: {features['x2_passenger_count']}",
                    f"- Vehicle count: {features['x3_vehicle_count']}",
                    f"- Weather condition: {features['x4_weather_condition']}",
                    f"- Day type: {features['x5_day_type']}",
                    f"- Current occupancy rate: {features['occupancy_rate']}",
                ])
            
            prompt = f"""
            As a transportation economics AI agent, analyze this scenario:
            
            CURRENT CONDITIONS:
            {features_str or f'- Current passenger count: {passenger_count}'}
            {f'- Historical data: {historical_data}' if historical_data else ''}
            
            ML MODEL PREDICTION:
            - Recommended discount: {ml_discount if ml_discount is not None else 'Not available'}
            
            Recommend only these parameters for a dynamic fare system:
            1. Initial base fare (in wei, typically 100-500)
            2. Passenger threshold for fare adjustments
            
            IMPORTANT: Do NOT recommend a discount percentage. The ML model has already determined 
            the optimal discount of {ml_discount if ml_discount is not None else 'Not available'}, 
            which will be used directly.
            
            Considerations:
            - Maintain profitability
            - Encourage ridership during low demand
            - Account for market conditions
            - Balance supply and demand
            
            Respond ONLY with valid JSON in this exact format:
            {{
                "initial_fare": integer,
                "threshold": integer,
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
            
            # Use ML discount directly, don't let Gemini override it
            return (
                int(result["initial_fare"]),
                int(result["threshold"]),
                decrease_pct,  # Keep as float from ML model
                result.get("reason", "No reason provided")
            )
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {str(e)}")
            # Fallback to ML prediction for discount and reasonable defaults for others
            reason = "Using ML discount with default parameters after AI failure"
            return (initial_fare, threshold, decrease_pct, reason)

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
    
    def load_csv_data(self, filepath='synthetic_fare_ai_dataset.csv', row_index=None):
        """Load transportation parameters from CSV file"""
        try:
            # Load the CSV file
            df = pd.read_csv(filepath)
            print(f"✓ Loaded CSV data: {len(df)} records")
            
            # If row_index is None, use the most recent data (last row)
            if row_index is None:
                row_index = len(df) - 1
                print(f"Using most recent data (row {row_index})")
            elif row_index >= len(df):
                print(f"⚠️ Row index {row_index} exceeds data length. Using last row.")
                row_index = len(df) - 1
            
            # Extract the row data
            row = df.iloc[row_index]
            
            # Convert to features dictionary
            features = {
                'x1_hour': int(row['x1_hour']),
                'x2_passenger_count': int(row['x2_passenger_count']),
                'x3_vehicle_count': int(row['x3_vehicle_count']),
                'x4_weather_condition': float(row['x4_weather_condition']),
                'x5_day_type': float(row['x5_day_type']),
                'occupancy_rate': float(row['occupancy_rate'])
            }
            
            # Optional: If you want historical data, get the last N passenger counts
            historical_data = df['x2_passenger_count'].tail(10).tolist()
            
            print(f"✓ Loaded features from CSV:")
            for key, value in features.items():
                print(f"  - {key}: {value}")
            
            return features, historical_data
        except Exception as e:
            print(f"⚠️ Failed to load CSV data: {str(e)}")
            return None, None

    def run(self):
      
        print("\n🚀 ML + Gemini-Powered Dynamic Fare Deployment")
        print("---------------------------------------")
        print(f"🔗 Connected to: {self.rpc_url}")
        print(f"🆔 Chain ID: {self.chain_id}")
        print(f"👛 Account: {self.account.address}")
        print(f"💰 Balance: {self.w3.from_wei(self.w3.eth.get_balance(self.account.address), 'ether'):.4f} ETH")
        print(f"🤖 ML Model: {'Loaded' if self.model_loaded else 'Not loaded'}")
        
        try:
            # Ask user if they want to use CSV data
            use_csv = input("\nDo you want to load parameters from CSV? (y/n): ").lower() == 'y'
            
            features = None
            historical_data = None
            passenger_count = None
            
            if use_csv:
                # Get CSV path and optional row
                csv_path = input("Enter CSV path (press Enter for default 'transportation_data.csv'): ")
                csv_path = csv_path if csv_path else 'synthetic_fare_ai_dataset.csv'
                
                row_input = input("Enter row number to use (press Enter for most recent): ")
                row_index = int(row_input) if row_input else None
                
                # Load data from CSV
                features, historical_data = self.load_csv_data(csv_path, row_index)
                if features:
                    passenger_count = features['x2_passenger_count']
                else:
                    print("⚠️ Failed to load CSV data. Switching to manual input.")
                    use_csv = False
            
            # Fall back to manual input if CSV not used or failed
            if not use_csv:
                # Collect feature data if ML model is available
                if self.model_loaded:
                    print("\n📊 Enter current transportation conditions:")
                    try:
                        features = {
                            'x1_hour': int(input("Hour of day (0-23): ")),
                            'x2_passenger_count': int(input("Current passenger count: ")),
                            'x3_vehicle_count': int(input("Vehicle count: ")),
                            'x4_weather_condition': float(input("Weather condition (numeric code): ")),
                            'x5_day_type': float(input("Day type (numeric code): ")),
                            'occupancy_rate': float(input("Current occupancy rate (0-1): "))
                        }
                        passenger_count = features['x2_passenger_count']
                    except ValueError:
                        print("⚠️ Invalid input values. Using simplified analysis.")
                        passenger_count = int(input("\nEnter today's passenger count: "))
                        features = None
                else:
                    # Traditional input if ML model isn't available
                    passenger_count = int(input("\nEnter today's passenger count: "))
                
                if not historical_data:
                    historical = input("Enter historical passenger counts (comma separated, optional): ")
                    historical_data = [int(x.strip()) for x in historical.split(',')] if historical else None
            
            # Get AI recommendation with ML enhancement
            print("\n🤖 Analyzing data with ML + Gemini AI for optimal fare parameters...")
            initial_fare, threshold, decrease_pct, reason = self.ai_analyze_demand(
                passenger_count,
                features,
                historical_data
            )
            
            # Continue with existing code...
            print(f"\n📊 AI+ML Recommendation:")
            print(f"   - Initial Fare: {initial_fare} wei")
            print(f"   - Threshold: {threshold} passengers")
            print(f"   - Decrease Percentage: {decrease_pct:.2f}%")  # Show float with 2 decimal places
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