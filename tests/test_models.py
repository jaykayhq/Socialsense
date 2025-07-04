import unittest
import datetime
import sys
import os

# Adjust Python path to import modules from 'src'
# This assumes 'tests' is a sibling directory to 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from models import User, SocialMediaAccount, SocialMediaPost, Campaign, Trend, Insight, Alert

class TestUserModels(unittest.TestCase):
    def test_user_creation(self):
        user = User(user_id="u001", username="testuser", email="test@example.com", password_hash="hashed")
        self.assertEqual(user.user_id, "u001")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.password_hash, "hashed")
        self.assertIsInstance(user.created_at, datetime.datetime)
        self.assertEqual(user.social_media_accounts, [])

class TestSocialMediaAccountModel(unittest.TestCase):
    def test_social_media_account_creation(self):
        account = SocialMediaAccount(account_id="twitter:123", platform="twitter",
                                     user_id="u001", access_token="fake_token")
        self.assertEqual(account.account_id, "twitter:123")
        self.assertEqual(account.platform, "twitter")
        self.assertEqual(account.user_id, "u001")
        self.assertEqual(account.access_token, "fake_token")
        self.assertIsNone(account.refresh_token)
        self.assertIsInstance(account.linked_at, datetime.datetime)

    def test_social_media_account_with_refresh_token(self):
        account = SocialMediaAccount(account_id="ig:456", platform="instagram",
                                     user_id="u002", access_token="ig_token", refresh_token="ig_refresh")
        self.assertEqual(account.refresh_token, "ig_refresh")

class TestSocialMediaPostModel(unittest.TestCase):
    def test_post_creation_basic(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        post = SocialMediaPost(post_id="post:001", account_id="acc:001", platform="platformX",
                               content="Test content", timestamp=now)
        self.assertEqual(post.post_id, "post:001")
        self.assertEqual(post.account_id, "acc:001")
        self.assertEqual(post.platform, "platformX")
        self.assertEqual(post.content, "Test content")
        self.assertEqual(post.timestamp, now)
        self.assertEqual(post.likes, 0)
        self.assertEqual(post.shares, 0)
        self.assertEqual(post.comments_count, 0)
        self.assertIsNone(post.reach)
        self.assertEqual(post.media_urls, [])
        self.assertIsNone(post.raw_data)
        self.assertIsInstance(post.fetched_at, datetime.datetime)

    def test_post_creation_with_all_fields(self):
        # now = datetime.datetime.now(datetime.timezone.utc) # 'now' is not used in this test method
        ts = datetime.datetime(2023, 1, 1, 12, 0, 0) # This is a naive datetime
        # If models require timezone-aware datetimes for timestamps, this should be:
        # ts = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        # However, current model usage for timestamp seems to handle naive ones by assuming UTC.
        raw_data_example = {"id_str": "123api", "lang": "en"}
        media_urls_example = ["http://example.com/img1.jpg"]

        post = SocialMediaPost(post_id="post:002", account_id="acc:002", platform="platformY",
                               content="More test content with details", timestamp=ts,
                               likes=100, shares=20, comments_count=5, reach=1000,
                               media_urls=media_urls_example, raw_data=raw_data_example)

        self.assertEqual(post.likes, 100)
        self.assertEqual(post.shares, 20)
        self.assertEqual(post.comments_count, 5)
        self.assertEqual(post.reach, 1000)
        self.assertEqual(post.media_urls, media_urls_example)
        self.assertEqual(post.raw_data, raw_data_example)

class TestCampaignModel(unittest.TestCase):
    def setUp(self):
        self.user_id = "user_camp_test"
        self.campaign_id = "camp_test_001"
        self.start_date = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.end_date = datetime.datetime(2024, 1, 31, 23, 59, 59)
        self.campaign = Campaign(
            campaign_id=self.campaign_id, user_id=self.user_id, name="Test Campaign",
            start_date=self.start_date, end_date=self.end_date,
            tracked_hashtags=["#test", "#promo"],
            tracked_keywords=["special offer"],
            tracked_accounts=["twitter:TestBrand"]
        )

    def test_campaign_initialization(self):
        self.assertEqual(self.campaign.campaign_id, self.campaign_id)
        self.assertEqual(self.campaign.user_id, self.user_id)
        self.assertEqual(self.campaign.name, "Test Campaign")
        self.assertEqual(self.campaign.start_date, self.start_date)
        self.assertEqual(self.campaign.end_date, self.end_date)
        self.assertEqual(self.campaign.tracked_hashtags, ["#test", "#promo"])
        self.assertEqual(self.campaign.tracked_keywords, ["special offer"])
        self.assertEqual(self.campaign.tracked_accounts, ["twitter:TestBrand"])
        self.assertIsInstance(self.campaign.created_at, datetime.datetime)

        # Initial metrics
        self.assertEqual(self.campaign.total_posts, 0)
        self.assertEqual(self.campaign.total_likes, 0)
        self.assertEqual(self.campaign.total_shares, 0)
        self.assertEqual(self.campaign.total_comments, 0)
        self.assertEqual(self.campaign.total_reach, 0)
        self.assertEqual(self.campaign.avg_engagement_rate, 0.0)
        self.assertEqual(self.campaign.associated_post_ids, [])

        # Initial status based on dates (assuming current date is after end_date for this test)
        # To make this robust, we might need to mock datetime.datetime.utcnow() or pass it in.
        # For now, let's assume a fixed 'now' for status testing.
        # If we can't mock 'now' easily here, we'll test status logic separately or make it less strict.
        # The Campaign model's update_metrics also updates status.
        # Default status is "Planning". If start_date is in past and end_date in future, it becomes "Active".

    def test_campaign_update_metrics_no_posts(self):
        self.campaign.update_metrics([])
        self.assertEqual(self.campaign.total_posts, 0)
        self.assertEqual(self.campaign.total_likes, 0)
        self.assertEqual(self.campaign.avg_engagement_rate, 0.0)
        self.assertEqual(self.campaign.associated_post_ids, [])

    def test_campaign_update_metrics_with_posts(self):
        posts_data = [
            SocialMediaPost("p1", "acc1", "twitter", "Post 1 content #test", datetime.datetime(2024,1,5), likes=10, shares=1, comments_count=1, reach=100),
            SocialMediaPost("p2", "acc2", "twitter", "Post 2 content special offer", datetime.datetime(2024,1,10), likes=20, shares=2, comments_count=2, reach=200),
            SocialMediaPost("p3", "acc3", "twitter", "Post 3 unrelated", datetime.datetime(2024,1,15), likes=5, shares=0, comments_count=0, reach=50) # Assume this is also part of campaign for test
        ]
        self.campaign.update_metrics(posts_data)
        self.assertEqual(self.campaign.total_posts, 3)
        self.assertEqual(self.campaign.total_likes, 35) # 10 + 20 + 5
        self.assertEqual(self.campaign.total_shares, 3)  # 1 + 2 + 0
        self.assertEqual(self.campaign.total_comments, 3) # 1 + 2 + 0
        self.assertEqual(self.campaign.total_reach, 350) # 100 + 200 + 50

        total_engagements = 35 + 3 + 3 # likes + shares + comments = 41
        expected_engagement_rate = round((total_engagements / 350) * 100, 2) if 350 > 0 else 0.0
        self.assertEqual(self.campaign.avg_engagement_rate, expected_engagement_rate)
        self.assertEqual(len(self.campaign.associated_post_ids), 3)
        self.assertIn("p1", self.campaign.associated_post_ids)

    def test_campaign_update_metrics_posts_with_nones(self):
        posts_data = [
            SocialMediaPost("p1", "acc1", "twitter", "Post 1", datetime.datetime(2024,1,5), likes=10, shares=None, comments_count=1, reach=100),
            SocialMediaPost("p2", "acc2", "twitter", "Post 2", datetime.datetime(2024,1,10), likes=None, shares=2, comments_count=None, reach=None)
        ]
        self.campaign.update_metrics(posts_data)
        self.assertEqual(self.campaign.total_posts, 2)
        self.assertEqual(self.campaign.total_likes, 10)
        self.assertEqual(self.campaign.total_shares, 2)
        self.assertEqual(self.campaign.total_comments, 1)
        self.assertEqual(self.campaign.total_reach, 100)

        total_engagements = 10 + 2 + 1 # 13
        expected_engagement_rate = round((total_engagements / 100) * 100, 2) if 100 > 0 else 0.0
        self.assertEqual(self.campaign.avg_engagement_rate, expected_engagement_rate)

    def test_campaign_status_finished(self):
        # Mock datetime.datetime.utcnow() to be after campaign.end_date
        # This is tricky without a mocking library like 'freezegun' or passing 'now' into update_metrics.
        # The model's update_metrics() handles this. Let's test it by setting dates appropriately.

        # Scenario 1: Campaign is finished
        # Define a 'now' that is clearly after the campaign's end date.
        mock_now_after_end = datetime.datetime(2023, 2, 15) # Campaign ended Jan 31, 2023
        past_campaign = Campaign("c_past", "u1", "Past Campaign",
                                 datetime.datetime(2023,1,1), datetime.datetime(2023,1,31))
        past_campaign.update_status(now=mock_now_after_end) # Call update_status directly with mock_now
        self.assertEqual(past_campaign.status, "Finished")

        # Scenario 2: Campaign is active
        mock_now_during_active = datetime.datetime.now() # Use current time for active test relative to now
        active_campaign = Campaign("c_active", "u1", "Active Campaign",
                                   mock_now_during_active - datetime.timedelta(days=5), # Started 5 days ago
                                   mock_now_during_active + datetime.timedelta(days=5)) # Ends 5 days from now
        active_campaign.update_status(now=mock_now_during_active)
        self.assertEqual(active_campaign.status, "Active")

        # Scenario 3: Campaign is planned (start date in future)
        mock_now_before_planned = datetime.datetime.now()
        planned_campaign = Campaign("c_planned", "u1", "Planned Campaign",
                                    mock_now_before_planned + datetime.timedelta(days=5), # Starts 5 days in future
                                    mock_now_before_planned + datetime.timedelta(days=10)) # Ends 10 days in future
        planned_campaign.update_status(now=mock_now_before_planned)
        self.assertEqual(planned_campaign.status, "Planning")

        # Scenario 4: Default status is Planning, and remains so if conditions aren't met to change it.
        # Campaign with start_date=None should remain Planning unless end_date makes it Finished.
        default_status_campaign = Campaign("c_default", "u1", "Default Campaign (No Start)", None, None)
        default_status_campaign.update_status(now=datetime.datetime.now())
        self.assertEqual(default_status_campaign.status, "Planning")

        # Scenario 5: Campaign with no start_date but end_date in past should be Finished.
        finished_no_start = Campaign("c_finished_no_start", "u1", "Finished No Start",
                                     None, datetime.datetime(2023,1,1))
        finished_no_start.update_status(now=datetime.datetime(2023,2,1)) # 'now' is after end_date
        self.assertEqual(finished_no_start.status, "Finished")


class TestTrendModel(unittest.TestCase):
    def test_trend_creation(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        trend = Trend(trend_id="t001", topic="#NaijaTech", platform="twitter",
                      start_time=now, relevance_score=0.85)
        self.assertEqual(trend.trend_id, "t001")
        self.assertEqual(trend.topic, "#NaijaTech")
        self.assertEqual(trend.platform, "twitter")
        self.assertEqual(trend.start_time, now)
        self.assertEqual(trend.relevance_score, 0.85)
        self.assertIsNone(trend.end_time)
        self.assertIsInstance(trend.identified_at, datetime.datetime)

class TestInsightModel(unittest.TestCase):
    def test_insight_creation(self):
        insight = Insight(insight_id="i001", user_id="u001",
                          description="Post more on Wednesdays at 5 PM.",
                          insight_type="posting_time_suggestion")
        self.assertEqual(insight.insight_id, "i001")
        self.assertEqual(insight.user_id, "u001")
        self.assertEqual(insight.description, "Post more on Wednesdays at 5 PM.")
        self.assertEqual(insight.type, "posting_time_suggestion")
        self.assertIsNone(insight.campaign_id)
        self.assertFalse(insight.is_actioned)
        self.assertIsInstance(insight.generated_at, datetime.datetime)

class TestAlertModel(unittest.TestCase):
    def test_alert_creation(self):
        alert = Alert(alert_id="alert001", user_id="u001", message="New trend detected!",
                      alert_type="new_trend", severity="info")
        self.assertEqual(alert.alert_id, "alert001")
        self.assertEqual(alert.user_id, "u001")
        self.assertEqual(alert.message, "New trend detected!")
        self.assertEqual(alert.type, "new_trend")
        self.assertEqual(alert.severity, "info")
        self.assertIsNone(alert.related_entity_id)
        self.assertIsNone(alert.related_entity_type)
        self.assertFalse(alert.is_read)
        self.assertIsNone(alert.read_at)
        self.assertIsInstance(alert.timestamp, datetime.datetime)

    def test_alert_mark_as_read(self):
        alert = Alert(alert_id="alert002", user_id="u002", message="Test")
        self.assertFalse(alert.is_read)
        self.assertIsNone(alert.read_at)

        alert.mark_as_read()
        self.assertTrue(alert.is_read)
        self.assertIsInstance(alert.read_at, datetime.datetime)

if __name__ == '__main__':
    unittest.main()
