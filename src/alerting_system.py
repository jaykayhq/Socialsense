import datetime
import logging
import uuid # For generating unique alert IDs

try:
    from .models import Alert, Campaign, Trend, SocialMediaPost # Assuming models are in the same package level
    from .ai_analysis.analyzer import AIAnalyzerService # For sentiment if needed
except ImportError:
    # Fallback for direct execution or if src isn't perfectly in path
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__))) # Add src to path
    from models import Alert, Campaign, Trend, SocialMediaPost
    # This might still fail if ai_analysis isn't found directly.
    # For robust direct testing, ensure PYTHONPATH is set or use a test runner.
    # For now, if AIAnalyzerService is critical and fails, we mock it or limit functionality.
    try:
        from ai_analysis.analyzer import AIAnalyzerService
    except ImportError:
        AIAnalyzerService = None
        logging.warning("AIAnalyzerService not available for alerting_system.py direct run. Sentiment checks might be limited.")


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration for Alert Thresholds (examples) ---
# These would ideally be configurable per user or system-wide via a config file/DB
TREND_VOLUME_THRESHOLD = 100 # Minimum volume for a new trend to be considered significant
TREND_VELOCITY_THRESHOLD = 50 # Min increase in count for an existing trend to be notable
CAMPAIGN_ENGAGEMENT_DROP_PERCENTAGE = -20.0 # e.g., -20%
CAMPAIGN_ENGAGEMENT_SPIKE_PERCENTAGE = 30.0  # e.g., +30%
NEGATIVE_SENTIMENT_THRESHOLD = 0.6 # e.g., 60% of recent posts for a campaign are negative
NEGATIVE_SENTIMENT_POST_COUNT = 10 # Min number of posts to consider for negative sentiment surge


class AlertingService:
    def __init__(self, user_id="default_user"):
        self.user_id = user_id # In a multi-user system, this would be specific to the user being processed
        self.previous_campaign_metrics = {} # Store campaign_id: {metric: value, timestamp: ...}
        self.seen_trends = {} # Store trend_term: {volume: count, timestamp: ...}
        if AIAnalyzerService:
            self.ai_analyzer = AIAnalyzerService()
        else:
            self.ai_analyzer = None
            logging.info("AIAnalyzerService not initialized in AlertingService.")

    def _generate_alert_id(self):
        return f"alert_{uuid.uuid4().hex[:10]}"

    def check_trend_alerts(self, current_trends: list[dict]) -> list[Alert]:
        """
        Checks for new or rapidly growing trends.
        `current_trends` is a list of dicts like [{"term": "NaijaTech", "count": 150}, ...]
        """
        alerts = []
        now = datetime.datetime.utcnow()

        for trend_data in current_trends:
            term = trend_data.get("term")
            count = trend_data.get("count", 0)

            if not term:
                continue

            if term not in self.seen_trends:
                if count >= TREND_VOLUME_THRESHOLD:
                    msg = f"🚀 New significant trend detected: '{term}' with {count} mentions."
                    alerts.append(Alert(alert_id=self._generate_alert_id(), user_id=self.user_id,
                                        message=msg, alert_type="new_trend", severity="info",
                                        related_entity_id=term, related_entity_type="trend_term"))
                self.seen_trends[term] = {"volume": count, "timestamp": now}
            else:
                # Check for velocity if trend was seen before
                prev_volume = self.seen_trends[term].get("volume", 0)
                volume_increase = count - prev_volume
                if volume_increase >= TREND_VELOCITY_THRESHOLD and count >= TREND_VOLUME_THRESHOLD : # Ensure it's still a significant trend
                    msg = f"📈 Trend '{term}' is growing rapidly! Now at {count} mentions (up by {volume_increase})."
                    alerts.append(Alert(alert_id=self._generate_alert_id(), user_id=self.user_id,
                                        message=msg, alert_type="trend_velocity_spike", severity="warning",
                                        related_entity_id=term, related_entity_type="trend_term"))
                # Update seen trend data
                self.seen_trends[term]["volume"] = count
                self.seen_trends[term]["timestamp"] = now

        # Optional: Prune old trends from self.seen_trends to avoid memory bloat over time
        # (e.g., remove trends not seen in X days)
        return alerts

    def check_campaign_performance_alerts(self, campaigns: list[Campaign]) -> list[Alert]:
        """
        Checks for significant spikes or drops in campaign performance metrics.
        Compares current avg_engagement_rate with previously stored values.
        """
        alerts = []
        now = datetime.datetime.utcnow()

        for campaign in campaigns:
            if campaign.status != "Active": # Only monitor active campaigns for this type of alert
                continue

            current_engagement_rate = campaign.avg_engagement_rate

            if campaign.campaign_id in self.previous_campaign_metrics:
                prev_metrics = self.previous_campaign_metrics[campaign.campaign_id]
                prev_engagement_rate = prev_metrics.get("avg_engagement_rate", 0.0)

                # Avoid division by zero if previous rate was 0
                if prev_engagement_rate != 0:
                    percentage_change = ((current_engagement_rate - prev_engagement_rate) / abs(prev_engagement_rate)) * 100
                elif current_engagement_rate > 0: # Went from 0 to something positive
                    percentage_change = CAMPAIGN_ENGAGEMENT_SPIKE_PERCENTAGE + 1 # Ensure it's a spike
                else: # Still 0 or also 0
                    percentage_change = 0.0

                alert_msg = None
                alert_severity = "info"

                if percentage_change >= CAMPAIGN_ENGAGEMENT_SPIKE_PERCENTAGE:
                    alert_msg = (f"🎉 Campaign '{campaign.name}' engagement spiked by {percentage_change:.1f}%! "
                                 f"Current rate: {current_engagement_rate:.2f}%.")
                    alert_severity = "warning"
                elif percentage_change <= CAMPAIGN_ENGAGEMENT_DROP_PERCENTAGE:
                    alert_msg = (f"⚠️ Campaign '{campaign.name}' engagement dropped by {abs(percentage_change):.1f}%! "
                                 f"Current rate: {current_engagement_rate:.2f}%.")
                    alert_severity = "critical"

                if alert_msg:
                    alerts.append(Alert(alert_id=self._generate_alert_id(), user_id=self.user_id,
                                        message=alert_msg, alert_type="campaign_performance_change", severity=alert_severity,
                                        related_entity_id=campaign.campaign_id, related_entity_type="campaign"))

            # Update stored metrics for next check
            self.previous_campaign_metrics[campaign.campaign_id] = {
                "avg_engagement_rate": current_engagement_rate,
                "total_likes": campaign.total_likes, # Could track other metrics too
                "timestamp": now
            }
        return alerts

    def check_sentiment_alerts(self, campaign: Campaign, campaign_posts: list[SocialMediaPost]) -> list[Alert]:
        """
        Checks for a surge in negative sentiment for a specific campaign.
        This requires AIAnalyzerService to be available.
        """
        alerts = []
        if not self.ai_analyzer:
            logging.warning("Sentiment alerts skipped: AIAnalyzerService not available.")
            return alerts
        if not campaign_posts or len(campaign_posts) < NEGATIVE_SENTIMENT_POST_COUNT:
            return alerts # Not enough posts to make a reliable sentiment judgment

        negative_post_count = 0
        for post in campaign_posts:
            if post.content:
                # This is a simplified call. In a real scenario, AIAnalyzerService might analyze posts
                # in batch and results would be pre-associated or fetched.
                # For now, assume analyze_posts returns a list of posts with sentiment.
                # This is inefficient if calling one by one.
                # Let's assume we have a way to get sentiment for each post.
                # For this example, let's mock that the sentiment is already on the post object or easily gettable.

                # Mocking: if post has a 'sentiment' attr (e.g. added by AI module earlier)
                sentiment_label = getattr(post, 'sentiment_label', None)
                if not sentiment_label and hasattr(post, 'sentiment') and isinstance(post.sentiment, dict):
                     sentiment_label = post.sentiment.get('label')


                # If not pre-analyzed, analyze now (less efficient for many posts)
                if not sentiment_label:
                    sentiment_result = self.ai_analyzer.sentiment_analyzer.analyze_sentiment(post.content)
                    sentiment_label = sentiment_result.get('label')

                if sentiment_label == "negative":
                    negative_post_count += 1

        if negative_post_count > 0: # Avoid division by zero
            negative_percentage = (negative_post_count / len(campaign_posts)) * 100
            if negative_percentage >= (NEGATIVE_SENTIMENT_THRESHOLD * 100):
                msg = (f"🚨 High negative sentiment ({negative_percentage:.1f}%) detected for campaign '{campaign.name}' "
                       f"based on {negative_post_count}/{len(campaign_posts)} recent posts.")
                alerts.append(Alert(alert_id=self._generate_alert_id(), user_id=self.user_id,
                                    message=msg, alert_type="negative_sentiment_surge", severity="critical",
                                    related_entity_id=campaign.campaign_id, related_entity_type="campaign"))
        return alerts


    def run_all_checks(self, campaigns: list[Campaign], current_trends_data: list[dict],
                       all_posts_for_sentiment_analysis: dict[str, list[SocialMediaPost]]=None) -> list[Alert]:
        """
        Runs all alert checks and aggregates the results.
        `all_posts_for_sentiment_analysis` is a dict mapping campaign_id to its list of posts.
        """
        all_new_alerts = []

        # 1. Trend Alerts
        trend_alerts = self.check_trend_alerts(current_trends_data)
        all_new_alerts.extend(trend_alerts)
        if trend_alerts: logging.info(f"Generated {len(trend_alerts)} trend alerts.")

        # 2. Campaign Performance Alerts
        perf_alerts = self.check_campaign_performance_alerts(campaigns)
        all_new_alerts.extend(perf_alerts)
        if perf_alerts: logging.info(f"Generated {len(perf_alerts)} campaign performance alerts.")

        # 3. Sentiment Alerts (per campaign)
        if self.ai_analyzer and all_posts_for_sentiment_analysis:
            for campaign in campaigns:
                if campaign.status == "Active" and campaign.campaign_id in all_posts_for_sentiment_analysis:
                    campaign_posts = all_posts_for_sentiment_analysis[campaign.campaign_id]
                    sentiment_campaign_alerts = self.check_sentiment_alerts(campaign, campaign_posts)
                    all_new_alerts.extend(sentiment_campaign_alerts)
                    if sentiment_campaign_alerts: logging.info(f"Generated {len(sentiment_campaign_alerts)} sentiment alerts for campaign '{campaign.name}'.")

        logging.info(f"Total new alerts generated: {len(all_new_alerts)}")
        return all_new_alerts


# Example Usage (for testing this module)
if __name__ == "__main__":
    logging.info("Alerting System Module Demonstration")
    alert_service = AlertingService(user_id="test_user_123")

    # --- Mock Data for Testing ---
    # Mock Campaigns (from models.Campaign)
    campaignA_start = datetime.datetime.now() - datetime.timedelta(days=10)
    campaignA = Campaign(campaign_id="campA", user_id="test_user_123", name="Active Summer Sale",
                         start_date=campaignA_start, end_date=None, status="Active")
    campaignA.avg_engagement_rate = 2.5 # Initial rate

    campaignB_start = datetime.datetime.now() - datetime.timedelta(days=30)
    campaignB_end = datetime.datetime.now() - datetime.timedelta(days=5)
    campaignB = Campaign(campaign_id="campB", user_id="test_user_123", name="Finished Spring Promo",
                         start_date=campaignB_start, end_date=campaignB_end, status="Finished")
    campaignB.avg_engagement_rate = 5.0

    mock_campaigns_list = [campaignA, campaignB]

    # Mock Trends Data (list of dicts from AIAnalyzerService)
    mock_trends_list = [
        {"term": "#NaijaTechNow", "count": 150}, # New significant trend
        {"term": "#LagosFashionWeek", "count": 80}, # Existing, no major change yet
        {"term": "#FintechFriday", "count": 30}, # Below threshold
    ]
    alert_service.seen_trends["#LagosFashionWeek"] = {"volume": 70, "timestamp": datetime.datetime.utcnow() - datetime.timedelta(hours=2)}


    # Mock Posts for Sentiment Analysis (list of SocialMediaPost objects)
    # These would typically be fetched by DataCollectionManager and filtered by CampaignLogic
    posts_for_campA = []
    if AIAnalyzerService: # Only create posts if AI service is available for sentiment
        for i in range(12):
            content = f"This is post {i} for Summer Sale. It's okay."
            if i >= 7: # Last 5 posts are negative
                content = f"This Summer Sale is bad, I hate this product {i}."

            # Simulate sentiment already being on the post for testing check_sentiment_alerts
            post = SocialMediaPost(post_id=f"pA{i}", account_id="user_acc", platform="twitter", content=content, timestamp=datetime.datetime.now())
            # Mock sentiment analysis result directly on post for testing
            # In real flow, AI module would do this.
            if "bad" in content or "hate" in content:
                post.sentiment = {"label": "negative", "score": -0.8}
            else:
                post.sentiment = {"label": "neutral", "score": 0.1}
            posts_for_campA.append(post)

    mock_posts_map = {"campA": posts_for_campA} if AIAnalyzerService else {}

    # --- Run Initial Checks (Round 1) ---
    print("\n--- Round 1: Initial Alert Checks ---")
    alerts_round1 = alert_service.run_all_checks(mock_campaigns_list, mock_trends_list, mock_posts_map)
    for alert in alerts_round1:
        print(f"  ALERT: {alert.message} (Severity: {alert.severity}, Type: {alert.type})")

    # --- Simulate Changes for Round 2 ---
    print("\n--- Round 2: Simulating Changes & Re-checking ---")
    # Campaign A engagement drops significantly
    campaignA.avg_engagement_rate = 1.5
    # Trend #LagosFashionWeek spikes
    updated_mock_trends_list = [
        {"term": "#NaijaTechNow", "count": 160}, # Slight increase
        {"term": "#LagosFashionWeek", "count": 150}, # Spike!
        {"term": "#FintechFriday", "count": 40},
        {"term": "#NewHotTopic", "count": 200}, # Another new significant trend
    ]

    # Assume sentiment for Campaign A remains largely negative for this round

    alerts_round2 = alert_service.run_all_checks(mock_campaigns_list, updated_mock_trends_list, mock_posts_map)
    for alert in alerts_round2:
        # Filter to show only *newly* generated alerts for this round by checking timestamp or by managing state
        # For this demo, it will re-evaluate and might show similar alerts if conditions persist.
        # A real system would avoid duplicate alerts for the exact same unchanged condition.
        print(f"  ALERT: {alert.message} (Severity: {alert.severity}, Type: {alert.type})")

    print("\nAlerting System Module demo finished.")
