import datetime
import logging
# Assuming models.py is in src directory, and this script is also in src or a sub-directory
# If running this file directly for testing, Python path might need adjustment.
# For now, assume it's part of the larger src package.
try:
    from .models import Campaign, SocialMediaPost
except ImportError:
    # Fallback for direct execution if src is not in PYTHONPATH
    # This is mainly for dev/testing of this script itself.
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models import Campaign, SocialMediaPost


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_posts_for_campaign(campaign: Campaign, all_posts: list[SocialMediaPost]) -> list[SocialMediaPost]:
    """
    Filters a list of all social media posts to find those relevant to a specific campaign.

    Relevance is determined by:
    1. Post timestamp falling within campaign start and end dates.
    2. Post content containing any of the campaign's tracked keywords or hashtags.
    OR Post account_id being one of the campaign's tracked_accounts.
    """
    relevant_posts = []
    if not isinstance(campaign, Campaign):
        logging.error("Invalid campaign object provided.")
        return []
    if not isinstance(all_posts, list):
        logging.error("Invalid all_posts list provided.")
        return []
    if not all(isinstance(p, SocialMediaPost) for p in all_posts):
        logging.warning("Not all items in all_posts are SocialMediaPost objects. Filtering those out.")
        all_posts = [p for p in all_posts if isinstance(p, SocialMediaPost)]


    # Ensure campaign dates are valid datetime objects if they exist
    # For comparison, post timestamps should also be datetime objects
    # The SocialMediaPost model's timestamp is assumed to be a datetime object already.

    campaign_start_date = campaign.start_date
    campaign_end_date = campaign.end_date # Can be None for ongoing campaigns

    for post in all_posts:
        # Ensure post.timestamp is a datetime object for comparison
        # The model defines it as datetime, but data source might vary.
        # For mock data, it might be float (timestamp), convert if so.
        post_timestamp = post.timestamp
        if isinstance(post_timestamp, (int, float)): # if it's a Unix timestamp
            post_timestamp = datetime.datetime.fromtimestamp(post_timestamp, tz=datetime.timezone.utc)
        elif isinstance(post_timestamp, str): # if it's an ISO string
             try:
                post_timestamp = datetime.datetime.fromisoformat(post_timestamp.replace("Z", "+00:00"))
             except ValueError:
                logging.warning(f"Could not parse timestamp string for post {post.post_id}: {post.timestamp}")
                continue # Skip post if timestamp is unparseable

        if not isinstance(post_timestamp, datetime.datetime):
            logging.warning(f"Post {post.post_id} has invalid timestamp type: {type(post.timestamp)}. Skipping.")
            continue

        # Ensure timezone awareness for comparison or make them naive (choose one strategy)
        # Assuming campaign_start_date and campaign_end_date are UTC from model.
        # If post_timestamp is naive, localize it or make campaign dates naive.
        # For simplicity, if campaign dates are naive (as in current model init), make post_timestamp naive if it's aware.
        if post_timestamp.tzinfo is not None:
            post_timestamp = post_timestamp.replace(tzinfo=None) # Convert to naive UTC for comparison


        # 1. Date Filter
        if campaign_start_date and post_timestamp < campaign_start_date:
            continue
        if campaign_end_date and post_timestamp > campaign_end_date:
            continue

        # 2. Content/Account Filter
        matches_criteria = False
        post_content_lower = post.content.lower() if post.content else ""

        # Check tracked accounts
        if campaign.tracked_accounts and post.account_id in campaign.tracked_accounts:
            matches_criteria = True

        # Check keywords if not already matched by account
        if not matches_criteria and campaign.tracked_keywords:
            for keyword in campaign.tracked_keywords:
                if keyword.lower() in post_content_lower:
                    matches_criteria = True
                    break

        # Check hashtags if not already matched
        if not matches_criteria and campaign.tracked_hashtags:
            # Hashtags in post content usually look like #tag.
            # Campaign tracked_hashtags might be stored with or without '#'. Assume without for now.
            for hashtag in campaign.tracked_hashtags:
                # Simple check: presence of #hashtag_text
                if f"#{hashtag.lower()}" in post_content_lower:
                    matches_criteria = True
                    break

        if matches_criteria:
            relevant_posts.append(post)

    logging.info(f"Found {len(relevant_posts)} posts relevant to campaign '{campaign.name}'.")
    return relevant_posts


def process_campaigns(campaign_list: list[Campaign], all_social_posts: list[SocialMediaPost]):
    """
    Processes a list of campaigns, finds relevant posts for each, and updates their metrics.
    Returns the list of campaigns with updated metrics.
    """
    if not isinstance(campaign_list, list) or not all(isinstance(c, Campaign) for c in campaign_list):
        logging.error("Invalid campaign_list provided to process_campaigns.")
        return []

    for campaign in campaign_list:
        relevant_posts_for_campaign = get_posts_for_campaign(campaign, all_social_posts)
        campaign.update_metrics(relevant_posts_for_campaign) # update_metrics is a method of Campaign model
        logging.info(f"Updated metrics for campaign '{campaign.name}': {campaign.total_posts} posts, "
                     f"{campaign.total_likes} likes, Avg Eng Rate: {campaign.avg_engagement_rate}%")
    return campaign_list


# Example Usage (for testing this module)
if __name__ == '__main__':
    logging.info("Campaign Logic Module Demonstration")

    # Create mock Campaign objects (referencing the updated Campaign model)
    campaign1_start = datetime.datetime(2024, 1, 1, 0, 0, 0)
    campaign1_end = datetime.datetime(2024, 1, 31, 23, 59, 59)
    campaign1 = Campaign(
        campaign_id="camp001", user_id="user001", name="New Year Promo",
        start_date=campaign1_start, end_date=campaign1_end,
        tracked_hashtags=["NewYear", "Promo2024"],
        tracked_keywords=["special offer", "discount"],
        tracked_accounts=["twitter:MyBrandAccount"]
    )

    campaign2_start = datetime.datetime(2024, 2, 1, 0, 0, 0) # Ongoing campaign
    campaign2 = Campaign(
        campaign_id="camp002", user_id="user001", name="February Love",
        start_date=campaign2_start, end_date=None, # No end date = ongoing
        tracked_hashtags=["FebLove"],
        tracked_accounts=["twitter:MyBrandAccount", "instagram:MyBrandIG"]
    )

    mock_campaigns = [campaign1, campaign2]

    # Create mock SocialMediaPost objects
    mock_posts = [
        SocialMediaPost(post_id="post1", account_id="twitter:MyBrandAccount", platform="twitter",
                        content="Our #NewYear special offer is here! Get 20% discount. #Promo2024",
                        timestamp=datetime.datetime(2024, 1, 5, 10, 0, 0), # clearly within campaign1
                        likes=100, shares=20, comments_count=5, reach=1000),
        SocialMediaPost(post_id="post2", account_id="twitter:AnotherAccount", platform="twitter",
                        content="Talking about New Year resolutions. Not a promo.",
                        timestamp=datetime.datetime(2024, 1, 6, 12, 0, 0),
                        likes=10, shares=1, comments_count=1, reach=100),
        SocialMediaPost(post_id="post3", account_id="twitter:MyBrandAccount", platform="twitter",
                        content="Happy February! #FebLove is in the air.",
                        timestamp=datetime.datetime(2024, 2, 2, 9, 0, 0), # within campaign2
                        likes=150, shares=30, comments_count=10, reach=1200),
        SocialMediaPost(post_id="post4", account_id="instagram:MyBrandIG", platform="instagram",
                        content="Our #FebLove contest starts now!",
                        timestamp=datetime.datetime(2024, 2, 3, 10, 0, 0), # within campaign2
                        likes=200, shares=0, comments_count=25, reach=2000), # IG has no "shares" typically
        SocialMediaPost(post_id="post5", account_id="twitter:MyBrandAccount", platform="twitter",
                        content="Throwback to our old products. No special offer here.", # Matches account and date for C1, but not keywords
                        timestamp=datetime.datetime(2024, 1, 10, 10, 0, 0),
                        likes=50, shares=5, comments_count=2, reach=500),
         SocialMediaPost(post_id="post6", account_id="twitter:MyBrandAccount", platform="twitter",
                        content="Our #NewYear special offer is here! Get 20% discount. #Promo2024",
                        timestamp=datetime.datetime(2023, 12, 15, 10, 0, 0), # Outside campaign1 date range
                        likes=100, shares=20, comments_count=5, reach=1000),
    ]

    print(f"\nInitial state of Campaign 1 ('{campaign1.name}'):")
    print(f"  Total Posts: {campaign1.total_posts}, Total Likes: {campaign1.total_likes}, Avg Eng Rate: {campaign1.avg_engagement_rate}%, Status: {campaign1.status}")
    print(f"Initial state of Campaign 2 ('{campaign2.name}'):")
    print(f"  Total Posts: {campaign2.total_posts}, Total Likes: {campaign2.total_likes}, Avg Eng Rate: {campaign2.avg_engagement_rate}%, Status: {campaign2.status}")

    # Process campaigns
    updated_campaigns = process_campaigns(mock_campaigns, mock_posts)

    print("\n--- Updated Campaign Metrics ---")
    for campaign in updated_campaigns:
        print(f"\nCampaign: {campaign.name} (ID: {campaign.campaign_id})")
        print(f"  Status: {campaign.status}")
        print(f"  Tracked Hashtags: {campaign.tracked_hashtags}")
        print(f"  Tracked Keywords: {campaign.tracked_keywords}")
        print(f"  Tracked Accounts: {campaign.tracked_accounts}")
        print(f"  Total Posts: {campaign.total_posts}")
        print(f"  Total Likes: {campaign.total_likes}")
        print(f"  Total Shares: {campaign.total_shares}")
        print(f"  Total Comments: {campaign.total_comments}")
        print(f"  Total Reach: {campaign.total_reach}")
        print(f"  Avg Engagement Rate: {campaign.avg_engagement_rate}%")
        print(f"  Associated Post IDs: {campaign.associated_post_ids}")

    # Test get_posts_for_campaign directly for campaign1
    # c1_posts = get_posts_for_campaign(campaign1, mock_posts)
    # print(f"\nPosts found for Campaign 1 by direct call: {len(c1_posts)}")
    # for p in c1_posts:
    #     print(f"  - Post ID: {p.post_id}, Content: '{p.content[:30]}...'")

    # campaign1.update_metrics(c1_posts) # Manual update
    # print(f"\nCampaign 1 after direct update_metrics call:")
    # print(f"  Total Posts: {campaign1.total_posts}, Total Likes: {campaign1.total_likes}, Avg Eng Rate: {campaign1.avg_engagement_rate}%")

    print("\nCampaign Logic Module demo finished.")
