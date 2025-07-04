import abc
import time
import logging
import os
# Hypothetical external library for Twitter API, replace with actual e.g., tweepy, requests-oauthlib
# For now, we'll mock its behavior.
# import tweepy

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Placeholder for where API credentials would be stored or fetched from
# In a real app, use environment variables, a secure vault, or a config file.
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET_KEY = os.environ.get("TWITTER_API_SECRET_KEY")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")


class SocialMediaCollector(abc.ABC):
    """
    Abstract base class for social media data collectors.
    """
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.client = self._authenticate()

    @abc.abstractmethod
    def _authenticate(self):
        """Handles authentication with the social media platform."""
        pass

    @abc.abstractmethod
    def fetch_posts_by_hashtag(self, hashtag, count):
        """Fetches posts containing a specific hashtag."""
        pass

    @abc.abstractmethod
    def fetch_posts_by_user(self, username, count):
        """Fetches posts made by a specific user."""
        pass

    @abc.abstractmethod
    def get_user_profile(self, username):
        """Fetches profile information for a specific user."""
        pass

    def _handle_rate_limit(self, response):
        """
        Basic rate limit handling.
        Specific implementations might need more sophisticated logic
        based on API responses (e.g., headers like 'x-rate-limit-reset').
        """
        # This is a very generic placeholder.
        # Real APIs provide headers like 'x-rate-limit-remaining' and 'x-rate-limit-reset'.
        if response.status_code == 429: # Too Many Requests
            logging.warning("Rate limit hit. Waiting for 60 seconds.")
            # In a real scenario, check 'Retry-After' header or API specific headers
            time.sleep(60)
            return True # Indicates rate limit was hit and handled by waiting
        return False # No rate limit issue detected by this basic check

class TwitterCollector(SocialMediaCollector):
    """
    Collects data from X (formerly Twitter).
    """
    def __init__(self, bearer_token=None, api_key=None, api_secret_key=None, access_token=None, access_token_secret=None):
        self.bearer_token = bearer_token or TWITTER_BEARER_TOKEN
        self.api_key = api_key or TWITTER_API_KEY
        self.api_secret_key = api_secret_key or TWITTER_API_SECRET_KEY
        self.access_token = access_token or TWITTER_ACCESS_TOKEN
        self.access_token_secret = access_token_secret or TWITTER_ACCESS_TOKEN_SECRET
        self.client = self._authenticate()

    def _authenticate(self):
        """
        Authenticates with the Twitter API.
        This is a mock implementation. A real one would use OAuth.
        It might initialize a library client like tweepy.API or tweepy.Client.
        """
        if self.bearer_token:
            logging.info("Attempting Twitter authentication with Bearer Token.")
            # Example: client = tweepy.Client(bearer_token=self.bearer_token)
            # For app-only access (searching tweets, user lookups)
            # For user-specific actions, full OAuth 1.0a or OAuth 2.0 PKCE flow is needed.
            logging.info("Mock Twitter client initialized with Bearer Token.")
            return "mock_twitter_bearer_client" # Placeholder for the actual client object
        elif self.api_key and self.api_secret_key and self.access_token and self.access_token_secret:
            logging.info("Attempting Twitter authentication with OAuth 1.0a User Context.")
            # Example:
            # auth = tweepy.OAuth1UserHandler(
            #    self.api_key, self.api_secret_key,
            #    self.access_token, self.access_token_secret
            # )
            # client = tweepy.API(auth)
            logging.info("Mock Twitter client initialized with OAuth 1.0a.")
            return "mock_twitter_oauth1_client"
        else:
            logging.error("Twitter API credentials not fully provided for authentication.")
            raise ValueError("Missing Twitter API credentials for selected auth method.")

    def fetch_posts_by_hashtag(self, hashtag, count=100):
        """
        MOCK: Fetches posts containing a specific hashtag from Twitter.
        In a real implementation, this would call the Twitter API.
        e.g., client.search_recent_tweets() or client.search_all_tweets() (for Academic Access)
        """
        logging.info(f"Mock fetching {count} Twitter posts for hashtag: #{hashtag}")
        if not self.client:
            logging.error("Twitter client not authenticated.")
            return []

        # Mocked response
        mock_posts = []
        for i in range(min(count, 5)): # return a small number of mock posts
            mock_posts.append({
                "post_id": f"twitter:mock_post_{hashtag}_{i}",
                "account_id": "twitter:mock_user_123",
                "platform": "twitter",
                "content": f"This is a mock tweet about #{hashtag}! Number {i}",
                "timestamp": time.time() - (i * 3600), # Mock timestamps
                "likes": 10 + i,
                "shares": 1 + i, # Twitter calls this retweets
                "comments_count": i, # Twitter calls this replies
                "raw_data": {"tweet_id_api": f"mock_api_id_{i}", "lang": "en"}
            })
        return mock_posts

    def fetch_posts_by_user(self, username, count=100):
        """
        MOCK: Fetches posts made by a specific user from Twitter.
        e.g., client.get_users_tweets()
        """
        logging.info(f"Mock fetching {count} Twitter posts for user: @{username}")
        if not self.client:
            logging.error("Twitter client not authenticated.")
            return []

        # Mocked response
        mock_posts = []
        for i in range(min(count,3)):
             mock_posts.append({
                "post_id": f"twitter:mock_post_user_{username}_{i}",
                "account_id": f"twitter:{username}",
                "platform": "twitter",
                "content": f"A mock tweet from @{username}. Post number {i}.",
                "timestamp": time.time() - (i * 86400), # Mock timestamps
                "likes": 20 + i,
                "shares": 2 + i,
                "comments_count": 1 + i,
                "raw_data": {"tweet_id_api": f"mock_api_user_id_{i}", "lang": "en"}
            })
        return mock_posts

    def get_user_profile(self, username):
        """
        MOCK: Fetches profile information for a specific user from Twitter.
        e.g., client.get_user()
        """
        logging.info(f"Mock fetching Twitter profile for user: @{username}")
        if not self.client:
            logging.error("Twitter client not authenticated.")
            return None

        # Mocked response
        return {
            "user_id": f"twitter:{username}_mock_id",
            "username": username,
            "display_name": f"Mock {username.capitalize()}",
            "followers_count": 1000,
            "following_count": 100,
            "description": f"This is a mock profile for @{username}.",
            "platform": "twitter",
            "raw_data": {"id_str": "mock_twitter_internal_id"}
        }


class InstagramCollector(SocialMediaCollector):
    """
    Collects data from Instagram.
    NOTE: Instagram API is very restrictive. Full implementation requires
    Business accounts, Facebook App review, and permissions.
    This will be a placeholder.
    """
    def __init__(self, access_token=None):
        # Instagram Graph API typically uses a user access token or system user token
        self.access_token = access_token
        super().__init__(api_keys={"access_token": access_token})

    def _authenticate(self):
        logging.info("Attempting Instagram authentication.")
        if not self.api_keys.get("access_token"):
            logging.warning("Instagram access token not provided. Collector will be non-functional.")
            return None
        # In a real scenario, you'd initialize a client for Facebook Graph API
        # e.g. using 'facebook-sdk' or 'requests'
        logging.info("Mock Instagram client initialized.")
        return "mock_instagram_client" # Placeholder

    def fetch_posts_by_hashtag(self, hashtag, count=25):
        """
        MOCK: Fetches posts by hashtag.
        Requires Instagram Graph API with specific permissions (e.g., instagram_basic, instagram_manage_insights).
        Hashtag search is limited.
        """
        logging.info(f"Mock fetching {count} Instagram posts for hashtag: #{hashtag}")
        if not self.client:
            logging.warning("Instagram client not authenticated or not functional.")
            return []
        # Mocked response
        return [{"post_id": f"instagram:mock_post_{hashtag}_0", "content": f"Mock Instagram post about #{hashtag}"}]

    def fetch_posts_by_user(self, username, count=25):
        """
        MOCK: Fetches posts by user.
        Requires permissions for the specific user's account (Business or Creator).
        Cannot fetch posts for arbitrary users easily.
        """
        logging.info(f"Mock fetching {count} Instagram posts for user: @{username}")
        if not self.client:
            logging.warning("Instagram client not authenticated or not functional.")
            return []
        return [{"post_id": f"instagram:mock_post_user_{username}_0", "content": f"Mock Instagram post from @{username}"}]

    def get_user_profile(self, username):
        logging.info(f"Mock fetching Instagram profile for user: @{username}")
        if not self.client:
            logging.warning("Instagram client not authenticated or not functional.")
            return None
        return {"user_id": f"instagram:{username}_mock_id", "username": username, "followers_count": 500}


# Example of how these might be used (for demonstration)
if __name__ == "__main__":
    logging.info("Data Collector Module Demonstration")

    # Attempt to use TwitterCollector (will use mock data as no real keys are set)
    # To test with real keys, set environment variables:
    # TWITTER_BEARER_TOKEN (for app-only search)
    # OR TWITTER_API_KEY, TWITTER_API_SECRET_KEY, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET (for user context)

    print("\n--- Twitter Collector (App-only/Bearer Token Mock) ---")
    # Assuming TWITTER_BEARER_TOKEN is not set, so this might log an error or use a mock client
    try:
        twitter_collector_bearer = TwitterCollector(bearer_token="fake_bearer_token_for_testing") # Force use of bearer
        if twitter_collector_bearer.client:
            hashtag_posts = twitter_collector_bearer.fetch_posts_by_hashtag("Tech conférence", count=2)
            print(f"Fetched {len(hashtag_posts)} posts for #TechConférence (Twitter):")
            for post in hashtag_posts:
                print(f"  - {post['content'][:50]}...")

            user_profile = twitter_collector_bearer.get_user_profile("TechGuru")
            if user_profile:
                print(f"Profile for @TechGuru (Twitter): {user_profile['display_name']}, Followers: {user_profile['followers_count']}")

            user_posts = twitter_collector_bearer.fetch_posts_by_user("OpenAI", count=1)
            print(f"Fetched {len(user_posts)} posts for @OpenAI (Twitter):")
            for post in user_posts:
                print(f" - {post['content'][:50]}...")

        else:
            print("Twitter collector (Bearer) not initialized properly (likely missing credentials).")
    except ValueError as e:
        print(f"Error initializing Twitter Collector (Bearer): {e}")


    print("\n--- Instagram Collector (Mock) ---")
    # Instagram collector is mostly a placeholder due to API complexities
    instagram_collector = InstagramCollector(access_token="fake_ig_access_token")
    if instagram_collector.client:
        ig_hashtag_posts = instagram_collector.fetch_posts_by_hashtag("NaijaFashion", count=1)
        print(f"Fetched {len(ig_hashtag_posts)} posts for #NaijaFashion (Instagram):")
        for post in ig_hashtag_posts:
            print(f"  - {post['content'][:50]}...")
    else:
        print("Instagram collector not initialized properly.")
```
