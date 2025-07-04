import datetime

class User:
    def __init__(self, user_id, username, email, password_hash):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.social_media_accounts = []  # List of SocialMediaAccount objects or IDs
        self.created_at = datetime.datetime.now(datetime.timezone.utc)

class SocialMediaAccount:
    def __init__(self, account_id, platform, user_id, access_token, refresh_token=None):
        self.account_id = account_id  # e.g., "twitter:12345"
        self.platform = platform      # e.g., "twitter", "instagram"
        self.user_id = user_id        # Foreign key to User
        self.access_token = access_token  # Should be stored encrypted
        self.refresh_token = refresh_token # Should be stored encrypted
        self.linked_at = datetime.datetime.now(datetime.timezone.utc)

class SocialMediaPost:
    def __init__(self, post_id, account_id, platform, content, timestamp,
                 likes=0, shares=0, comments_count=0, reach=None, media_urls=None, raw_data=None):
        self.post_id = post_id # e.g., "twitter:post_id_from_api"
        self.account_id = account_id # Foreign key to SocialMediaAccount
        self.platform = platform
        self.content = content
        self.media_urls = media_urls if media_urls is not None else []
        self.timestamp = timestamp
        self.likes = likes
        self.shares = shares
        self.comments_count = comments_count
        self.reach = reach
        self.raw_data = raw_data # For platform-specific fields
        self.fetched_at = datetime.datetime.now(datetime.timezone.utc)

class Campaign:
    def __init__(self, campaign_id, user_id, name, start_date, end_date,
                 tracked_keywords=None, tracked_hashtags=None, tracked_accounts=None):
        self.campaign_id = campaign_id
        self.user_id = user_id # Foreign key to User
        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.tracked_keywords = tracked_keywords if tracked_keywords is not None else []
        self.tracked_hashtags = tracked_hashtags if tracked_hashtags is not None else []
        self.tracked_accounts = tracked_accounts if tracked_accounts is not None else [] # List of account_ids

        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.status = "Planning" # Possible statuses: Planning, Active, Paused, Finished, Archived

        # Metrics - to be calculated
        self.total_posts = 0
        self.total_likes = 0
        self.total_shares = 0 # or retweets
        self.total_comments = 0 # or replies
        self.total_reach = 0 # Sum of reach if available, otherwise could be estimated
        self.avg_engagement_rate = 0.0 # (Total Likes + Shares + Comments) / Total Posts / (Followers if available) or / Total Reach

        self.associated_post_ids = [] # Store IDs of posts linked to this campaign

    def update_metrics(self, posts):
        """
        Calculates and updates campaign metrics based on a list of associated SocialMediaPost objects.
        Assumes 'posts' are already filtered and relevant to this campaign.
        """
        if not posts:
            self.total_posts = 0
            self.total_likes = 0
            self.total_shares = 0
            self.total_comments = 0
            self.total_reach = 0
            self.avg_engagement_rate = 0.0
            self.associated_post_ids = []
            return

        self.total_posts = len(posts)
        self.total_likes = sum(post.likes for post in posts if post.likes is not None)
        self.total_shares = sum(post.shares for post in posts if post.shares is not None)
        self.total_comments = sum(post.comments_count for post in posts if post.comments_count is not None)

        # Reach can be tricky; sum if available, otherwise it might need estimation or remain partial.
        # For simplicity, sum what's directly available.
        self.total_reach = sum(post.reach for post in posts if post.reach is not None)

        self.associated_post_ids = [post.post_id for post in posts]

        # Engagement Rate Calculation (Example)
        # (Total Engagements / Total Reach) * 100 if reach is available and significant
        # Or (Total Engagements / Total Posts) if reach is not reliable / available for all.
        # Or (Total Engagements / Follower Count of posting account) - more complex, needs follower data here.
        total_engagements = self.total_likes + self.total_shares + self.total_comments

        if self.total_reach > 0:
            self.avg_engagement_rate = round((total_engagements / self.total_reach) * 100, 2)
        elif self.total_posts > 0: # Fallback if reach is zero or unavailable
             # This isn't a standard "rate" but a per-post engagement average.
             # True engagement rate often needs follower counts.
             # For now, let's use a simplified engagement score per post.
            self.avg_engagement_rate = round(total_engagements / self.total_posts, 2) # More of an avg engagement number per post
        else:
            self.avg_engagement_rate = 0.0

        self.update_status() # Call status update after metrics are calculated

    def _update_status_logic(self, current_time):
        """Internal logic to update status based on a given current time."""
        # Ensure 'current_time' is offset-naive if campaign dates are naive for comparison.
        # Campaign dates (start_date, end_date) are assumed to be naive datetime objects representing UTC.
        ct_for_comparison = current_time
        if ct_for_comparison.tzinfo is not None:
            ct_for_comparison = ct_for_comparison.replace(tzinfo=None)

        if self.end_date and self.end_date < ct_for_comparison:
            self.status = "Finished"
        elif self.start_date and self.start_date <= ct_for_comparison:
            self.status = "Active"
        # If neither of the above, it remains in its current state (e.g. "Planning" or whatever was set)
        # or we can explicitly set it to "Planning" if no other condition met and start_date is in future.
        elif self.start_date and self.start_date > ct_for_comparison:
            self.status = "Planning"
        # If none of these conditions are met (e.g., start_date is None, and not finished by end_date),
        # it retains its current status (which is "Planning" by default from __init__).
        # This handles cases like start_date=None, end_date=None (remains Planning)
        # or start_date=None, end_date=future (remains Planning).

    def update_status(self, now=None):
        """
        Updates the campaign status based on its start/end dates.
        Accepts an optional 'now' parameter for testing.
        """
        if now is None:
            # In Python 3.12+, datetime.UTC is preferred.
            # For broader compatibility and to match existing utcnow() usage:
            current_time = datetime.datetime.now(datetime.timezone.utc)
        else:
            current_time = now

        self._update_status_logic(current_time)

class Trend:
    def __init__(self, trend_id, topic, platform, start_time, relevance_score, end_time=None):
        self.trend_id = trend_id
        self.topic = topic
        self.platform = platform # "twitter", "instagram", or "all"
        self.start_time = start_time
        self.end_time = end_time
        self.relevance_score = relevance_score
        self.identified_at = datetime.datetime.now(datetime.timezone.utc)

class Insight:
    def __init__(self, insight_id, user_id, description, insight_type,
                 campaign_id=None, is_actioned=False):
        self.insight_id = insight_id
        self.user_id = user_id # Foreign key to User
        self.campaign_id = campaign_id # Optional foreign key to Campaign
        self.type = insight_type # e.g., "posting_time_suggestion", "hashtag_recommendation"
        self.description = description # e.g., "Post more on Wednesdays at 5 PM"
        self.generated_at = datetime.datetime.now(datetime.timezone.utc)
        self.is_actioned = is_actioned


class Alert:
    def __init__(self, alert_id, user_id, message, alert_type="general",
                 severity="info", related_entity_id=None, related_entity_type=None):
        self.alert_id = alert_id
        self.user_id = user_id # To whom this alert belongs
        self.message = message # Detailed message for the user
        self.type = alert_type # e.g., "trend_spike", "performance_drop", "sentiment_change", "new_insight"
        self.severity = severity # e.g., "info", "warning", "critical"
        self.related_entity_id = related_entity_id # e.g., campaign_id, trend_id, post_id
        self.related_entity_type = related_entity_type # e.g., "campaign", "trend", "post"
        self.timestamp = datetime.datetime.now(datetime.timezone.utc)
        self.is_read = False
        self.read_at = None

    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.datetime.now(datetime.timezone.utc)

    def __repr__(self):
        return f"<Alert(id='{self.alert_id}', type='{self.type}', user='{self.user_id}', read={self.is_read})>"


# Example Usage (optional, for testing or demonstration)
if __name__ == '__main__':
    # Create a user
    user1 = User(user_id="user_001", username="test_user", email="test@example.com", password_hash="hashed_password")
    print(f"User created: {user1.username} at {user1.created_at}")

    # Link a social media account
    sm_account1 = SocialMediaAccount(account_id="twitter:123456789", platform="twitter",
                                     user_id=user1.user_id, access_token="dummy_access_token")
    user1.social_media_accounts.append(sm_account1.account_id)
    print(f"Social media account linked: {sm_account1.platform} ({sm_account1.account_id})")

    # Create a campaign
    campaign1 = Campaign(campaign_id="camp_001", user_id=user1.user_id, name="Summer Sale 2024",
                         start_date=datetime.datetime(2024, 6, 1), end_date=datetime.datetime(2024, 6, 30),
                         tracked_hashtags=["#SummerSale", "#LagosDeals"])
    print(f"Campaign created: {campaign1.name}")

    # Log a social media post
    post1_timestamp = datetime.datetime(2024, 6, 5, 17, 0, 0)
    post1 = SocialMediaPost(post_id="twitter:post_98765", account_id=sm_account1.account_id,
                            platform="twitter", content="Big summer sale! #SummerSale",
                            timestamp=post1_timestamp, likes=150, shares=30)
    print(f"Social media post logged: {post1.content[:20]}... on {post1.platform}")

    # Generate an insight
    insight1 = Insight(insight_id="ins_001", user_id=user1.user_id, campaign_id=campaign1.campaign_id,
                       insight_type="hashtag_performance",
                       description="The hashtag #SummerSale is performing well.")
    print(f"Insight generated: {insight1.description}")

    # Identify a trend
    trend1 = Trend(trend_id="trend_001", topic="#LagosFashionWeek", platform="instagram",
                   start_time=datetime.datetime(2024, 6, 3), relevance_score=0.85)
    print(f"Trend identified: {trend1.topic} on {trend1.platform}")
