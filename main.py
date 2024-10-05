import time
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from web3 import Web3
from dotenv import load_dotenv
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins


load_dotenv()

# Set up your Web3 connection
# Replace this URL with your Infura/Alchemy API or your Ethereum node URL
infura_url = "https://rpc-testnet.bdagscan.com"
web3 = Web3(Web3.HTTPProvider(infura_url))

# Check if connected to the Ethereum network
if not web3.is_connected():
    print("Failed to connect to Ethereum network")
    exit()

# Set up the contract details (ERC20 token)
token_address = Web3.to_checksum_address(os.getenv("CONTRACT_ADDRESS"))
wallet_private_key = os.getenv("PRIVATE_KEY")  # Keep your private key secure
your_wallet_address = Web3.to_checksum_address(os.getenv("YOUR_WALLET_ADDRESS"))


# Set up your token contract ABI (truncated for simplicity)
# Replace this with the correct ABI for your token
token_abi = """[
    {
        "constant": false,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]"""

# Instantiate the token contract
token_contract = web3.eth.contract(address=token_address, abi=token_abi)


@app.route("/faucet", methods=["POST"])
def faucet():
    try:
        # Get the wallet address from the request
        wallet_address = request.json.get("walletAddress")
        if not wallet_address or not web3.is_address(wallet_address):
            return jsonify({"error": "Invalid wallet address"}), 400

        wallet_address = Web3.to_checksum_address(wallet_address)

        # Set the token amount to send (in Wei)
        token_amount = Web3.to_wei(1, "ether")  # For example, sending 1tokens

        # Create the transaction
        nonce = web3.eth.get_transaction_count(your_wallet_address)
        txn = token_contract.functions.transfer(
            wallet_address, token_amount
        ).build_transaction(
            {
                "chainId": 24171,  # Mainnet
                "gas": 200000,  # Adjust based on contract requirements
                "gasPrice": web3.to_wei("100", "gwei"),
                "nonce": nonce,
            }
        )

        # Sign the transaction with your private key
        signed_txn = web3.eth.account.sign_transaction(
            txn, private_key=wallet_private_key
        )

        # Send the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # Wait for the transaction to be mined
        web3.eth.wait_for_transaction_receipt(tx_hash)

        time.sleep(5)

        return (
            jsonify(
                {
                    "message": f"Tokens sent successfully to {wallet_address}",
                    "txHash": web3.to_hex(tx_hash),
                }
            ),
            200,
        )

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to send tokens"}), 500


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
