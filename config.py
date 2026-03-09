import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    FIRESTORE_COLLECTION: str = os.getenv("FIRESTORE_COLLECTION", "trading_context")
    
    # Web3
    BASE_RPC_URL: str = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
    ETHEREUM_RPC_URL: str = os.getenv("ETHEREUM_RPC_URL", "https://eth.llamarpc.com")
    PRIVATE_KEY: str = os.getenv("PRIVATE_KEY", "")
    WALLET_ADDRESS: str = os.getenv("WALLET_ADDRESS", "")
    
    # Twitter
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")
    
    # Telegram (for alerts)
    TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    # Trading Parameters
    MAX_POSITION_SIZE_PERCENT: float = float(os.getenv("MAX_POSITION_SIZE_PERCENT", 5.0))
    BASE_POSITION_SIZE_PERCENT: float = float(os.getenv("BASE_POSITION_SIZE_PERCENT", 2.0))
    TARGET_TRADES: int = int(os.getenv("TARGET_TRADES", 50))
    TOTAL_CAPITAL: float = float(os.getenv("TOTAL_CAPITAL", 20.0))  # In USD
    
    # Risk Management
    MAX_STOP_LOSS_PERCENT: float = float(os.getenv("MAX_STOP_LOSS_PERCENT", 8.0))
    MIN_TAKE_PROFIT_PERCENT: float = float(os.getenv("MIN_TAKE_PROFIT_PERCENT", 12.0))
    ATR_MULTIPLIER_STOP: float = float(os.getenv("ATR_MULTIPLIER_STOP", 2.0))
    ATR_MULTIPLIER_TAKE_PROFIT: float = float(os.getenv("ATR_MULTIPLIER_TAKE_PROFIT", 3.5))
    
    # API Keys (Etherscan, etc.)
    ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

config = Config()