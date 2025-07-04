import unittest
import datetime
import sys
import os

# Adjust Python path to import modules from 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from models import Campaign, SocialMediaPost
from campaign_logic import get_posts_for_campaign, process_campaigns

class TestCampaignLogic(unittest.TestCase):

    def setUp(self):
        # Common campaign setup for multiple tests
        self.campaign_start = datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        self.campaign_end = datetime.datetime(2024, 1, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)

        # Make campaign dates naive for comparison, as model and logic currently assume naive UTC for these
        self.campaign_start_naive = self.campaign_start.replace(tzinfo=None)
        self.campaign_end_naive = self.campaign_end.replace(tzinfo=None)

        self.campaign1 = Campaign(
            campaign_id="camp1", user_id="user1", name="Test Campaign Alpha",
            start_date=self.campaign_start_naive, end_date=self.campaign_end_naive,
            tracked_hashtags=["alphaTest", "promo"],
            tracked_keywords=["special deal", "limited time"],
            tracked_accounts=["twitter:BrandAlpha"]
        )

        # Posts - use timezone-aware datetimes for post timestamps initially
        self.post1_match_hashtag = SocialMediaPost(
            post_id="p1", account_id="twitter:UserA", platform="twitter",
            content="Check out our #alphaTest event! #promo",
            timestamp=datetime.datetime(2024, 1, 5, 10, 0, 0, tzinfo=datetime.timezone.utc),
            likes=10, shares=1, comments_count=1, reach=100
        )
        self.post2_match_keyword = SocialMediaPost(
            post_id="p2", account_id="twitter:UserB", platform="twitter",
            content="We have a special deal just for you.",
            timestamp=datetime.datetime(2024, 1, 10, 12, 0, 0, tzinfo=datetime.timezone.utc),
            likes=20, shares=2, comments_count=2, reach=200
        )
        self.post3_match_account = SocialMediaPost(
            post_id="p3", account_id="twitter:BrandAlpha", platform="twitter",
            content="A message from BrandAlpha for our followers.",
            timestamp=datetime.datetime(2024, 1, 15, 14, 0, 0, tzinfo=datetime.timezone.utc),
            likes=30, shares=3, comments_count=3, reach=300
        )
        self.post4_out_of_date_before = SocialMediaPost(
            post_id="p4", account_id="twitter:UserC", platform="twitter",
            content="Early bird #alphaTest news!",
            timestamp=datetime.datetime(2023, 12, 25, 10, 0, 0, tzinfo=datetime.timezone.utc), # Before campaign
            likes=5, shares=0, comments_count=0, reach=50
        )
        self.post5_out_of_date_after = SocialMediaPost(
            post_id="p5", account_id="twitter:UserD", platform="twitter",
            content="Late #alphaTest thoughts.",
            timestamp=datetime.datetime(2024, 2, 5, 10, 0, 0, tzinfo=datetime.timezone.utc), # After campaign
            likes=3, shares=0, comments_count=0, reach=30
        )
        self.post6_no_match = SocialMediaPost(
            post_id="p6", account_id="twitter:UserE", platform="twitter",
            content="Just a regular tweet about something else.",
            timestamp=datetime.datetime(2024, 1, 20, 10, 0, 0, tzinfo=datetime.timezone.utc),
            likes=2, shares=0, comments_count=0, reach=20
        )
        self.post7_match_case_insensitive_hashtag = SocialMediaPost(
            post_id="p7", account_id="twitter:UserF", platform="twitter",
            content="Loving this #ALPHATEST content!", # Case difference
            timestamp=datetime.datetime(2024, 1, 7, 10, 0, 0, tzinfo=datetime.timezone.utc),
            likes=15, shares=1, comments_count=1, reach=150
        )
        self.post8_match_case_insensitive_keyword = SocialMediaPost(
            post_id="p8", account_id="twitter:UserG", platform="twitter",
            content="A SPECIAL DEAL for everyone!", # Case difference
            timestamp=datetime.datetime(2024, 1, 12, 10, 0, 0, tzinfo=datetime.timezone.utc),
            likes=25, shares=2, comments_count=2, reach=250
        )

        self.all_test_posts = [
            self.post1_match_hashtag, self.post2_match_keyword, self.post3_match_account,
            self.post4_out_of_date_before, self.post5_out_of_date_after, self.post6_no_match,
            self.post7_match_case_insensitive_hashtag, self.post8_match_case_insensitive_keyword
        ]

    def test_get_posts_for_campaign_no_posts_input(self):
        relevant_posts = get_posts_for_campaign(self.campaign1, [])
        self.assertEqual(len(relevant_posts), 0)

    def test_get_posts_for_campaign_match_by_hashtag(self):
        relevant_posts = get_posts_for_campaign(self.campaign1, [self.post1_match_hashtag, self.post6_no_match])
        self.assertEqual(len(relevant_posts), 1)
        self.assertIn(self.post1_match_hashtag, relevant_posts)

    def test_get_posts_for_campaign_match_by_keyword(self):
        relevant_posts = get_posts_for_campaign(self.campaign1, [self.post2_match_keyword, self.post6_no_match])
        self.assertEqual(len(relevant_posts), 1)
        self.assertIn(self.post2_match_keyword, relevant_posts)

    def test_get_posts_for_campaign_match_by_account(self):
        relevant_posts = get_posts_for_campaign(self.campaign1, [self.post3_match_account, self.post6_no_match])
        self.assertEqual(len(relevant_posts), 1)
        self.assertIn(self.post3_match_account, relevant_posts)

    def test_get_posts_for_campaign_case_insensitivity(self):
        # Hashtags are stored as "alphaTest", post has "#ALPHATEST"
        # Keywords are stored as "special deal", post has "SPECIAL DEAL"
        # campaign_logic.py converts post content to lower, and hashtag/keyword matching should be case-insensitive
        # The current logic in campaign_logic.py for hashtags is `f"#{hashtag.lower()}" in post_content_lower`
        # and for keywords `keyword.lower() in post_content_lower`. This should work.
        relevant_posts = get_posts_for_campaign(self.campaign1, [self.post7_match_case_insensitive_hashtag, self.post8_match_case_insensitive_keyword])
        self.assertEqual(len(relevant_posts), 2)
        self.assertIn(self.post7_match_case_insensitive_hashtag, relevant_posts)
        self.assertIn(self.post8_match_case_insensitive_keyword, relevant_posts)


    def test_get_posts_for_campaign_date_filtering(self):
        # Only posts 1, 2, 3, 7, 8 are within date range and match other criteria from self.all_test_posts
        # Posts 4 (before) and 5 (after) should be excluded even if content matches
        # Post 6 (no match) should be excluded
        relevant_posts = get_posts_for_campaign(self.campaign1, self.all_test_posts)
        self.assertEqual(len(relevant_posts), 5) # p1, p2, p3, p7, p8
        self.assertNotIn(self.post4_out_of_date_before, relevant_posts)
        self.assertNotIn(self.post5_out_of_date_after, relevant_posts)
        self.assertNotIn(self.post6_no_match, relevant_posts)
        self.assertIn(self.post1_match_hashtag, relevant_posts)
        self.assertIn(self.post2_match_keyword, relevant_posts)
        self.assertIn(self.post3_match_account, relevant_posts)
        self.assertIn(self.post7_match_case_insensitive_hashtag, relevant_posts)
        self.assertIn(self.post8_match_case_insensitive_keyword, relevant_posts)

    def test_get_posts_for_campaign_no_tracking_criteria(self):
        campaign_no_criteria = Campaign(
            campaign_id="camp_nc", user_id="user1", name="No Criteria Campaign",
            start_date=self.campaign_start_naive, end_date=self.campaign_end_naive,
            tracked_hashtags=[], tracked_keywords=[], tracked_accounts=[]
        )
        # If no criteria, it should return no posts, as a post must match at least one criterion.
        relevant_posts = get_posts_for_campaign(campaign_no_criteria, self.all_test_posts)
        self.assertEqual(len(relevant_posts), 0)

    def test_get_posts_for_campaign_ongoing_campaign_no_end_date(self):
        ongoing_campaign = Campaign(
            campaign_id="camp_ongoing", user_id="user1", name="Ongoing Campaign",
            start_date=self.campaign_start_naive, end_date=None, # No end date
            tracked_hashtags=["alphaTest"]
        )
        # post1 matches hashtag and is after start_date. post5 is after start_date but also after campaign_end (which is None here)
        # So both post1 and post5 should be included if they match criteria and are after start_date
        # Let's re-evaluate post5's timestamp for this test
        post5_modified_for_ongoing_test = SocialMediaPost(
            post_id="p5_mod", account_id="twitter:UserD", platform="twitter",
            content="Late #alphaTest thoughts, but campaign is ongoing!",
            # Timestamp is after campaign_start_naive and campaign_logic should handle no end_date
            timestamp=datetime.datetime(2024, 2, 5, 10, 0, 0, tzinfo=datetime.timezone.utc),
            likes=3, shares=0, comments_count=0, reach=30
        )
        relevant_posts = get_posts_for_campaign(ongoing_campaign, [self.post1_match_hashtag, post5_modified_for_ongoing_test])
        self.assertEqual(len(relevant_posts), 2)
        self.assertIn(self.post1_match_hashtag, relevant_posts)
        self.assertIn(post5_modified_for_ongoing_test, relevant_posts)

    def test_process_campaigns(self):
        # This test relies on the correctness of Campaign.update_metrics, which is tested in test_models.py
        # Here we test the orchestration.
        # Set a fixed past date for campaign2 start to ensure post2 and post8 are included
        campaign2_start_naive = datetime.datetime(2024, 1, 1, 0, 0, 0) # Start of Jan 2024
        campaign2 = Campaign(
            campaign_id="camp2", user_id="user1", name="Second Campaign",
            start_date=campaign2_start_naive, end_date=None, # No end date, so effectively ongoing from Jan 1, 2024
            tracked_keywords=["special deal"]
        )

        campaigns_to_process = [self.campaign1, campaign2]
        processed_campaigns = process_campaigns(campaigns_to_process, self.all_test_posts)

        self.assertEqual(len(processed_campaigns), 2)

        # Check Campaign1 (should have 5 posts: p1,p2,p3,p7,p8)
        camp1_processed = next(c for c in processed_campaigns if c.campaign_id == "camp1")
        self.assertEqual(camp1_processed.total_posts, 5)
        expected_likes_c1 = self.post1_match_hashtag.likes + self.post2_match_keyword.likes + \
                              self.post3_match_account.likes + self.post7_match_case_insensitive_hashtag.likes + \
                              self.post8_match_case_insensitive_keyword.likes
        self.assertEqual(camp1_processed.total_likes, expected_likes_c1)

        # Check Campaign2 (should have 2 posts: p2, p8 - "special deal")
        camp2_processed = next(c for c in processed_campaigns if c.campaign_id == "camp2")
        self.assertEqual(camp2_processed.total_posts, 2)
        expected_likes_c2 = self.post2_match_keyword.likes + self.post8_match_case_insensitive_keyword.likes
        self.assertEqual(camp2_processed.total_likes, expected_likes_c2)

    def test_get_posts_for_campaign_post_timestamp_is_naive_datetime(self):
        # campaign_logic converts aware post timestamps to naive. What if they are already naive?
        post_naive_ts = SocialMediaPost(
            post_id="p_naive", account_id="twitter:UserN", platform="twitter",
            content="A post with #alphaTest and naive timestamp.",
            timestamp=datetime.datetime(2024, 1, 18, 10, 0, 0), # Naive datetime
            likes=5, shares=0, comments_count=0, reach=50
        )
        relevant_posts = get_posts_for_campaign(self.campaign1, [post_naive_ts])
        self.assertEqual(len(relevant_posts), 1)
        self.assertIn(post_naive_ts, relevant_posts)

    def test_get_posts_for_campaign_post_timestamp_is_unix_float(self):
        # campaign_logic converts numeric timestamps to datetime objects
        # Timestamp for Jan 19, 2024, 10:00:00 AM UTC
        unix_timestamp_float = datetime.datetime(2024, 1, 19, 10, 0, 0, tzinfo=datetime.timezone.utc).timestamp()
        post_unix_ts_float = SocialMediaPost(
            post_id="p_unix_float", account_id="twitter:UserU", platform="twitter",
            content="Another #alphaTest post with UNIX float timestamp.",
            timestamp=unix_timestamp_float,
            likes=6, shares=1, comments_count=0, reach=60
        )
        relevant_posts = get_posts_for_campaign(self.campaign1, [post_unix_ts_float])
        self.assertEqual(len(relevant_posts), 1)
        self.assertIn(post_unix_ts_float, relevant_posts)

    def test_get_posts_for_campaign_post_timestamp_is_iso_string(self):
        iso_timestamp_str = "2024-01-21T10:00:00Z" # ISO 8601 format
        post_iso_ts_str = SocialMediaPost(
            post_id="p_iso_str", account_id="twitter:UserISO", platform="twitter",
            content="An #alphaTest post with ISO string timestamp.",
            timestamp=iso_timestamp_str,
            likes=7, shares=1, comments_count=1, reach=70
        )
        relevant_posts = get_posts_for_campaign(self.campaign1, [post_iso_ts_str])
        self.assertEqual(len(relevant_posts), 1)
        self.assertIn(post_iso_ts_str, relevant_posts)


if __name__ == '__main__':
    unittest.main()
