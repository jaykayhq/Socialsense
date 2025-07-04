import logging
from .collectors import TwitterCollector, InstagramCollector
# We would import our defined model classes here if we were creating model instances
# from src.models import SocialMediaPost, User # etc.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataCollectionManager:
    def __init__(self, twitter_config=None, instagram_config=None):
        """
        Initializes the DataCollectionManager.
        Configs are dictionaries that would contain API keys, tokens, etc.
        Example: twitter_config = {"bearer_token": "YOUR_BEARER_TOKEN"}
        """
        self.collectors = {}
        if twitter_config:
            try:
                # Pass specific config items to the collector
                self.collectors['twitter'] = TwitterCollector(
                    bearer_token=twitter_config.get('bearer_token'),
                    api_key=twitter_config.get('api_key'),
                    api_secret_key=twitter_config.get('api_secret_key'),
                    access_token=twitter_config.get('access_token'),
                    access_token_secret=twitter_config.get('access_token_secret')
                )
                logging.info("TwitterCollector initialized in Manager.")
            except ValueError as e:
                logging.error(f"Failed to initialize TwitterCollector: {e}")

        if instagram_config:
            try:
                self.collectors['instagram'] = InstagramCollector(
                    access_token=instagram_config.get('access_token')
                )
                logging.info("InstagramCollector initialized in Manager.")
            except ValueError as e: # Though current mock InstagramCollector doesn't raise ValueError
                logging.error(f"Failed to initialize InstagramCollector: {e}")

        if not self.collectors:
            logging.warning("DataCollectionManager initialized with no active collectors.")

    def fetch_data_for_campaign(self, campaign_details):
        """
        Fetches data relevant to a campaign.
        'campaign_details' would be an object or dict containing keywords, hashtags, users to track.
        For now, it's a simplified mock.
        """
        all_posts_data = []

        hashtags = campaign_details.get('hashtags', [])
        # In a real app, we'd map these to our src.models.SocialMediaPost
        # For now, we're just aggregating the raw-ish dicts from collectors.

        for platform, collector in self.collectors.items():
            logging.info(f"Fetching data for campaign from {platform}...")
            for hashtag in hashtags:
                try:
                    logging.info(f"Fetching posts for hashtag '{hashtag}' from {platform}")
                    posts = collector.fetch_posts_by_hashtag(hashtag, count=campaign_details.get('posts_per_hashtag', 20))
                    logging.info(f"Fetched {len(posts)} posts for hashtag '{hashtag}' from {platform}")
                    all_posts_data.extend(posts) # Assuming posts are dicts for now
                except Exception as e:
                    logging.error(f"Error fetching hashtag '{hashtag}' from {platform}: {e}")

            # Potentially add fetching by user mentions or for specific users if defined in campaign_details
            # users_to_track = campaign_details.get('users_to_track', [])
            # for user in users_to_track:
            #     try:
            #         user_posts = collector.fetch_posts_by_user(user, count=campaign_details.get('posts_per_user', 10))
            #         all_posts_data.extend(user_posts)
            #     except Exception as e:
            #         logging.error(f"Error fetching posts for user '{user}' from {platform}: {e}")

        # Here, you might convert these raw_post_data items into SocialMediaPost model instances
        # and store them in a database.
        # For this step, we just return the aggregated list of dictionaries.
        logging.info(f"Total raw posts fetched for campaign: {len(all_posts_data)}")
        return all_posts_data

    def get_profile_info(self, platform, username):
        """
        Fetches profile information for a user on a specific platform.
        """
        if platform in self.collectors:
            try:
                return self.collectors[platform].get_user_profile(username)
            except Exception as e:
                logging.error(f"Error fetching profile for {username} from {platform}: {e}")
                return None
        else:
            logging.warning(f"No collector available for platform: {platform}")
            return None

# Example Usage
if __name__ == "__main__":
    logging.info("Data Collection Manager Demonstration")

    # Mock configurations (in a real app, these come from env vars or a config file)
    # Note: The collectors themselves will use mock clients if full credentials aren't found/passed.
    mock_twitter_config = {"bearer_token": "dummy_bearer_for_manager_test"}
    mock_instagram_config = {"access_token": "dummy_ig_token_for_manager_test"}

    manager = DataCollectionManager(twitter_config=mock_twitter_config, instagram_config=mock_instagram_config)

    if not manager.collectors:
        print("No collectors were initialized. Exiting demo.")
    else:
        # Define a mock campaign
        campaign1 = {
            "name": "Naija Tech Week Promotion",
            "hashtags": ["NaijaTechWeek", "LagosStartup"],
            "posts_per_hashtag": 2 # Small number for demo
        }

        print(f"\nFetching data for campaign: {campaign1['name']}")
        campaign_data = manager.fetch_data_for_campaign(campaign1)

        print(f"\nTotal posts collected by manager for campaign '{campaign1['name']}': {len(campaign_data)}")
        for i, post_data in enumerate(campaign_data):
            print(f"  Post {i+1}: Platform: {post_data.get('platform')}, Content: '{post_data.get('content', '')[:40]}...'")
            if i > 5: # Print only a few
                print(f"  ... and {len(campaign_data) - (i+1)} more posts.")
                break

        if not campaign_data:
            print("  No data collected (this is expected if collectors are purely mock and return empty lists).")

        print("\nFetching profile information:")
        twitter_user = "FutureDev"
        ig_user = "NaijaInfluencer"

        twitter_profile = manager.get_profile_info("twitter", twitter_user)
        if twitter_profile:
            print(f"  Twitter Profile for @{twitter_user}: Name: {twitter_profile.get('display_name')}, Followers: {twitter_profile.get('followers_count')}")
        else:
            print(f"  Could not fetch Twitter profile for @{twitter_user} (or collector not available).")

        instagram_profile = manager.get_profile_info("instagram", ig_user)
        if instagram_profile:
            print(f"  Instagram Profile for @{ig_user}: Username: {instagram_profile.get('username')}, Followers: {instagram_profile.get('followers_count')}")
        else:
            print(f"  Could not fetch Instagram profile for @{ig_user} (or collector not available).")

        print("\nData Collection Manager demo finished.")
