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