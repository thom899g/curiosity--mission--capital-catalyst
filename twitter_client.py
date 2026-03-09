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