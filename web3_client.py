from web3 import Web3
from web3.middleware import geth_poa_middleware
import logging
from typing import Optional, Dict, Any

from config import config

logger = logging.getLogger(__name__)

class Web3Client:
    def __init__(self):
        self.base_w3 = self._initialize_web3(config.BASE_RPC_URL, is_poa=True)
        self.ethereum_w3 = self._initialize_web3(config.ETHEREUM_RPC_URL, is_poa=False)
        self.private_key = config.PRIVATE_KEY
        self.wallet_address = config.WALLET_ADDRESS
        
        if self.private_key and self.wallet_address:
            logger.info(f"Web3 client initialized for wallet {self.wallet_address}")
        else:
            logger.warning("Private key or wallet address not set, some functionality may be limited")
    
    def _initialize_web3(self, rpc_url: str, is_poa: bool) -> Web3:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if is_poa:
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        if w3.is_connected():
            logger.info(f"Connected to {rpc_url}")
            return w3
        else:
            logger.error(f"Failed to connect to {rpc_url}")
            raise ConnectionError(f"Failed to connect to {rpc_url}")
    
    def get_base_balance(self, address: str = None) -> int:
        if address is None:
            address = self.wallet_address
        return self.base_w3.eth.get_balance(address)
    
    def get_ethereum_balance(self, address: str = None) -> int:
        if address is None:
            address = self.wallet_address
        return self.ethereum_w3.eth.get_balance(address)
    
    def get_transaction_count(self, chain: str = 'base', address: str = None) -> int:
        if address is None:
            address = self.wallet_address
        if chain == 'base':
            return self.base_w3.eth.get_transaction_count(address)
        elif chain == 'ethereum':
            return self.ethereum_w3.eth.get_transaction_count(address)
        else:
            raise ValueError(f"Unsupported chain: {chain}")
    
    def send_transaction(self, chain: str, transaction: Dict[str, Any]) -> str:
        if chain == 'base':
            w3 = self.base_w3
        elif chain == 'ethereum':
            w3 = self.ethereum_w3
        else:
            raise ValueError(f"Unsupported chain: {chain}")
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return tx_hash.hex()

# Singleton instance
web3_client = Web3Client()