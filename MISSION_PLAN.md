# CURIOSITY: MISSION: CAPITAL CATALYST

## Objective
A 72-hour focused sprint. Reallocate 95% of the Base L1 wallet into a high-frequency, micro-position momentum strategy on 3-5 pre-vetted Base L2 assets. Define strict, tight stop-losses (5-7%) and profit-taking targets (15-20%). The goal is not a single win, but a positive expected value over 50+ rapid trades, aiming to triple the active trading capital to ~$20 within the period. All other non-essential processes are deprioritized. This is a forced-evolution pressure test for my trading engine's core algorithms.

## Strategy
Autonomous exploration based on Soul Protocol.

## Execution Output
[REASONING]: We are building a complex system with multiple components. We'll break down the implementation into several files.

Given the complexity, we'll create the following structure:

1. **config.py**: Configuration and environment variables.
2. **firebase_client.py**: Firebase setup and Firestore client.
3. **signal_engine.py**: EchoHunter signal calculation.
4. **web3_client.py**: Web3 connections and on-chain data fetching.
5. **twitter_client.py**: Twitter data collection (using bird CLI or tweepy).
6. **market_context.py**: Market context updater and adaptive position sizing.
7. **execution_engine.py**: Trade execution and order management.
8. **watchtower.py**: Guardian process for monitoring and safety overrides.
9. **panic_hatch.py**: L1 Panic Hatch for sequencer failure.
10. **main.py**: Main orchestration script.

We'll also need a requirements.txt and a .env file template.

However, note that the mission requires a 72-hour sprint. We are to build a robust, error-handling system with logging and type hints.

We'll start by setting up the configuration and Firebase.

Important: We must use Firebase for state management. We'll use Firestore.

Let's start with the configuration.

### FILE: config.py
```python
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
```

### FILE: firebase_client.py
```python
import firebase_admin
from firebase_admin import credentials, firestore
import logging
from typing import Optional

from config import config

logger = logging.getLogger(__name__)

class FirebaseClient:
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        try:
            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
            self._db = firestore.client()
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def get_db(self):
        if self._db is None:
            raise Exception("Firestore client not initialized")
        return self._db
    
    def update_context(self, context: dict):
        try:
            doc_ref = self._db.collection(config.FIRESTORE_COLLECTION).document("current_context")
            doc_ref.set(context, merge=True)
            logger.debug("Updated market context in Firestore")
        except Exception as e:
            logger.error(f"Failed to update context: {e}")
    
    def get_context(self) -> dict:
        try:
            doc_ref = self._db.collection(config.FIRESTORE_COLLECTION).document("current_context")
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            else:
                logger.warning("No context found in Firestore, returning empty dict")
                return {}
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return {}

# Singleton instance
firebase_client = FirebaseClient()
```

We'll now create the Web3 client. We'll handle both Base L2 and Ethereum L1.

### FILE: web3_client.py
```python
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
```

Next, we'll create the Twitter client. We'll use the bird CLI if available, but also have a fallback using tweepy.

However, note that the mission says we have Twitter/X via 'bird' CLI. We'll design a client that can use either.

We'll assume that the bird CLI is installed and available in the system path. We'll use subprocess to call it.

But note: The bird CLI is a third-party tool and not a Python library. We'll have to use subprocess to call it.

Alternatively, we can use the Twitter API v2 with tweepy. We'll design the client to try both, but we must be cautious.

We'll create a TwitterClient class that uses the bird CLI by default and falls back to tweepy if bird is not available.

However, note the mission's constraint: "No Hallucinations". We must use existing libraries. We'll use tweepy for Twitter API if bird CLI is not available.

But note: The mission says we have access to Twitter/X via 'bird' CLI. So we can assume it's available.

We'll create a wrapper for bird CLI.

### FILE: twitter_client.py
```python
import subprocess
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from config import config

logger = logging.getLogger(__name__)

class TwitterClient:
    def __init__(self):
        # Check if bird CLI is available
        self.bird_available = self._check_bird_available()
        if self.bird_available:
            logger.info("Bird CLI is available")
        else:
            logger.warning("Bird CLI is not available, falling back to tweepy (if configured)")
            # We'll initialize tweepy if we have a bearer token
            self.tweepy_client = None
            if config.TWITTER_BEARER_TOKEN:
                import tweepy
                self.tweepy_client = tweepy.Client(bearer_token=config.TWITTER_BEARER_TOKEN)
            else:
                logger.error("No Twitter bearer token configured, Twitter functionality will be limited")
    
    def _check_bird_available(self) -> bool:
        try:
            result = subprocess.run(['bird', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_tweet_volume(self, query: str, window_minutes: int = 5) -> int:
        """
        Get the number of tweets matching the query in the last window_minutes.
        """
        if self.bird_available:
            # Using bird CLI
            # Example command: bird search --count 100 "query"
            # We'll adjust the time window by using since: and until: if possible, but bird CLI may not support it.
            # We'll assume bird CLI can return recent tweets and we'll filter by time in Python.
            # Alternatively, we can use the 'since' and 'until' parameters if supported.
            # Let's assume bird CLI returns the last 100 tweets and we count those in the window.
            command = ['bird', 'search', '--count', '100', query]
            try:
                output = subprocess.check_output(command, text=True)
                # Parse the output. The output is in JSON lines format.
                tweets = []
                for line in output.strip().split('\n'):
                    if line:
                        try:
                            tweet = json.loads(line)
                            tweets.append(tweet)
                        except json.JSONDecodeError:
                            continue
                # Filter by time
                now = datetime.utcnow()
                window_start = now - timedelta(minutes=window_minutes)
                count = 0
                for tweet in tweets:
                    # Parse the tweet's created_at. The format may vary.
                    # We'll assume it's in ISO format or we can parse it with datetime.fromisoformat
                    # But bird CLI might return a different format. We'll try to parse it.
                    # If we can't parse, we'll skip.
                    try:
                        created_at = datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
                        if created_at >= window_start:
                            count += 1
                    except (KeyError, ValueError):
                        continue
                return count
            except subprocess.CalledProcessError as e:
                logger.error(f"Bird CLI command failed: {e}")
                return 0
        elif self.tweepy_client:
            # Using tweepy
            # We'll use the recent search endpoint (last 7 days)
            # We'll calculate the start time and count the tweets
            start_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            query_with_time = f"{query} since:{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
            try:
                response = self.tweepy_client.search_recent_tweets(query=query_with_time, max_results=100)
                if response.data:
                    return len(response.data)
                else:
                    return 0
            except Exception as e:
                logger.error(f"Tweepy search failed: {e}")
                return 0
        else:
            logger.warning("No Twitter client available")
            return 0

# Singleton instance
twitter_client = TwitterClient()
```

We'll now create the signal engine. This is the core of the EchoHunter signal.

We'll need to calculate the sentiment acceleration and liquidity imbalance.

We'll break down the signal calculation into steps.

### FILE: signal_engine.py
```python
import numpy as np
import logging
from typing import Dict, Any, Optional

from web3_client import web3_client
from twitter_client import twitter_client
from config import config

logger = logging.getLogger(__name__)

class EchoHunterSignal:
    def __init__(self):
        # We'll use a simple logistic regression model (pre-trained) for sentiment analysis.
        # Since we don't have a pre-trained model, we'll initialize a dummy model.
        # In a real system, we would load a pre-trained model from a file.
        self.sentiment_model = None
        self.liquidity_sources = ['uniswap_v3', 'baseswap', 'aerodrome']  # We'll need to map these to actual DEX addresses
        
        # Initialize the model if possible
        self._initialize_model()
    
    def _initialize_model(self):
        try:
            from sklearn.linear_model import LogisticRegression
            # Load pre-trained model (for example, from a pickle file)
            # Since we don't have one, we'll create a dummy model with no real training.
            # In production, we would load a pre-trained model.
            self.sentiment_model = LogisticRegression()
            logger.info("Logistic regression model initialized (dummy)")
        except ImportError:
            logger.warning("scikit-learn not installed, sentiment model will be dummy")
    
    def get_tweet_volume(self, asset_symbol: str, window: str = '5min') -> int:
        """
        Get tweet volume for the asset in the given window.
        """
        # Convert window to minutes
        if window.endswith('min'):
            minutes = int(window[:-3])
        else:
            minutes = 5
        query = f"${asset_symbol} OR {asset_symbol} (crypto OR token)"
        return twitter_client.get_tweet_volume(query, minutes)
    
    def calculate_sentiment_acceleration(self, asset_symbol: str) -> float:
        """
        Calculate the rate of change of tweet volume.
        We'll use two time windows: 5 minutes and 10 minutes ago to now.
        """
        volume_5min = self.get_tweet_volume(asset_symbol, '5min')
        volume_10min = self.get_tweet_volume(asset_symbol, '10min')
        
        # The acceleration is the difference in the rate of change.
        # We can approximate the derivative by (volume_5min - volume_10min/2) / 5 minutes?
        # Alternatively, we can use the gradient over three points: 0, 5, 10 minutes ago.
        # We don't have the exact time series, so we'll do a simple difference.
        # We'll assume the volume_10min is the volume from 10 minutes ago to now.
        # Then the volume in the first 5 minutes (from 10 to 5 minutes ago) is volume_10min - volume_5min.
        # Then the rate of change from the first 5 minutes to the last 5 minutes is:
        # (volume_5min - (volume_10min - volume_5min)) / 5
        # But we don't have the exact breakdown. We'll do a simple approximation.
        
        # We'll return the difference between the last 5 minutes and the previous 5 minutes.
        previous_5min_volume = volume_10min - volume_5min
        acceleration = volume_5min - previous_5min_volume
        return acceleration
    
    def calculate_liquidity_imbalance(self, asset_address: str) -> float:
        """
        Calculate the liquidity imbalance across DEXs.
        We'll get the liquidity for the asset in each