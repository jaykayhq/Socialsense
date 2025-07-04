from flask import Flask, render_template
from flask_compress import Compress # Import Flask-Compress
import datetime
import random # For mock data

# Initialize Flask App
app = Flask(__name__)
Compress(app) # Initialize Flask-Compress with the app

# Attempt to import campaign_logic and models for mock data generation
# This setup assumes 'src' is in PYTHONPATH or app is run from root where 'src' is a package.
try:
    from src.models import Campaign as AppCampaign, SocialMediaPost as AppSocialMediaPost
    from src.campaign_logic import process_campaigns as app_process_campaigns
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    # Basic mock classes if full models can't be imported (e.g. running ui/app.py directly without full project context)
    class MockCampaign:
        def __init__(self, name, status, reach, engagement_rate, start_date=None, end_date=None,
                     tracked_hashtags=None, tracked_keywords=None, tracked_accounts=None,
                     total_posts=0, total_likes=0, total_shares=0, total_comments=0, total_reach=0, avg_engagement_rate=0.0):
            self.name = name
            self.status = status
            self.reach = reach # Keep for simplicity in dashboard display if needed
            self.engagement_rate = engagement_rate # Keep for simplicity
            self.start_date = start_date or datetime.date.today()
            self.end_date = end_date
            self.tracked_hashtags = tracked_hashtags or []
            self.tracked_keywords = tracked_keywords or []
            self.tracked_accounts = tracked_accounts or []
            self.total_posts = total_posts
            self.total_likes = total_likes
            self.total_shares = total_shares
            self.total_comments = total_comments
            self.total_reach = total_reach
            self.avg_engagement_rate = avg_engagement_rate
            # Format reach for display
            self.total_reach_formatted = f"{total_reach:,}" if isinstance(total_reach, int) else total_reach
            self.reach_formatted = f"{reach:,}" if isinstance(reach, int) else reach


    class MockSocialMediaPost:
        def __init__(self, post_id, account_id, platform, content, timestamp,
                     likes=0, shares=0, comments_count=0, reach=None):
            self.post_id = post_id
            self.account_id = account_id
            self.platform = platform
            self.content = content
            self.timestamp = timestamp
            self.likes = likes
            self.shares = shares
            self.comments_count = comments_count
            self.reach = reach

    if MODELS_AVAILABLE:
        Campaign = AppCampaign
        SocialMediaPost = AppSocialMediaPost
        process_campaigns = app_process_campaigns
    else: # Fallback to mock if imports failed
        Campaign = MockCampaign
        SocialMediaPost = MockSocialMediaPost
        def process_campaigns(campaign_list, all_posts):
            # Mock processing: just return the list, actual logic is in campaign_logic.py
            print("Warning: Using MOCK process_campaigns due to import error.")
            # Simulate some metric calculation for mock display
            for camp in campaign_list:
                if not hasattr(camp, 'total_posts'): # If it's the simple MockCampaign
                    camp.total_posts = random.randint(10,50)
                    camp.total_likes = random.randint(100,500)
                    camp.total_shares = random.randint(20,100)
                    camp.total_comments = random.randint(10,80)
                    camp.total_reach = camp.reach if hasattr(camp, 'reach') else random.randint(1000,10000)
                    camp.avg_engagement_rate = camp.engagement_rate if hasattr(camp, 'engagement_rate') else round(random.uniform(1.0, 8.0), 2)
                    camp.total_reach_formatted = f"{camp.total_reach:,}"
            return campaign_list


# Mock data generation using the (potentially real) Campaign model
def get_mock_campaigns_data():
    """Generates mock campaign data, potentially using the real Campaign model and logic."""

    campaign1_start = datetime.datetime(2024, 1, 1, 0, 0, 0)
    campaign1_end = datetime.datetime(2024, 1, 31, 23, 59, 59)
    c1 = Campaign(
        campaign_id="camp001", user_id="user001", name="Christmas Sales Drive",
        start_date=campaign1_start, end_date=campaign1_end,
        tracked_hashtags=["ChristmasSale", "HolidayDeals"],
        tracked_keywords=["festive offer", "xmas discount"],
        tracked_accounts=["twitter:MyBrandXmas"]
    )

    campaign2_start = datetime.datetime.now() - datetime.timedelta(days=15)
    campaign2_end = datetime.datetime.now() + datetime.timedelta(days=15)
    c2 = Campaign(
        campaign_id="camp002", user_id="user001", name="New Product Launch (Q1)",
        start_date=campaign2_start, end_date=campaign2_end, # Active campaign
        tracked_hashtags=["NewProduct", "FreshArrival"],
        tracked_accounts=["twitter:MyBrandGlobal", "instagram:MyBrandGlobal"]
    )

    c3_start = datetime.datetime.now() + datetime.timedelta(days=30) # Future campaign
    c3 = Campaign(
        campaign_id="camp003", user_id="user001", name="Brand Awareness Push (Q2)",
        start_date=c3_start, end_date=None,
        tracked_keywords=["brand story", "our values"]
    )

    mock_campaign_objects = [c1, c2, c3]

    # Create mock SocialMediaPost objects that might relate to these campaigns
    mock_posts_for_campaign_logic = [
        SocialMediaPost(post_id="p1", account_id="twitter:MyBrandXmas", platform="twitter",
                        content="Big #ChristmasSale! Get your festive offer now. #HolidayDeals",
                        timestamp=datetime.datetime(2024, 1, 10, 10, 0, 0),
                        likes=120, shares=30, comments_count=15, reach=5000),
        SocialMediaPost(post_id="p2", account_id="twitter:MyBrandGlobal", platform="twitter",
                        content="Our #NewProduct is finally here! #FreshArrival",
                        timestamp=datetime.datetime.now() - datetime.timedelta(days=5),
                        likes=250, shares=50, comments_count=40, reach=15000),
        SocialMediaPost(post_id="p3", account_id="instagram:MyBrandGlobal", platform="instagram",
                        content="Look at this #FreshArrival! Isn't it amazing? #NewProduct",
                        timestamp=datetime.datetime.now() - datetime.timedelta(days=2),
                        likes=500, shares=0, comments_count=80, reach=25000),
         SocialMediaPost(post_id="p4", account_id="twitter:MyBrandXmas", platform="twitter",
                        content="Last chance for Xmas discount! #ChristmasSale",
                        timestamp=datetime.datetime(2024, 1, 25, 10, 0, 0),
                        likes=80, shares=10, comments_count=5, reach=3000),
    ]

    # Use the actual campaign_logic.process_campaigns if available
    processed_campaigns = process_campaigns(mock_campaign_objects, mock_posts_for_campaign_logic)

    # Format for template if necessary (e.g., large numbers)
    for camp in processed_campaigns:
        if hasattr(camp, 'total_reach') and isinstance(camp.total_reach, int):
            camp.total_reach_formatted = f"{camp.total_reach:,}"
        if hasattr(camp, 'reach') and isinstance(camp.reach, int): # For older dashboard view
             camp.reach_formatted = f"{camp.reach:,}"
        if hasattr(camp, 'total_followers') and isinstance(camp.total_followers, int):
            camp.total_followers_formatted = f"{camp.total_followers:,}"


    return processed_campaigns


def get_mock_dashboard_data(all_campaigns_data):
    """Generates mock data for the dashboard, using processed campaign data."""
    mock_trends = [
        {"term": "#NaijaBusiness", "count": random.randint(50, 200)},
        {"term": "Lagos SMEs", "count": random.randint(30, 150)},
        {"term": "#SocialMediaMarketing", "count": random.randint(20, 100)},
    ]
    mock_trends.sort(key=lambda x: x['count'], reverse=True)

    mock_insights = [
        {"id": "ins_001", "description": "Post more engaging content on Instagram between 4 PM - 6 PM on weekdays.", "type": "engagement_time", "generated_at": datetime.datetime.now() - datetime.timedelta(hours=2)},
        {"id": "ins_002", "description": "Consider using the hashtag #MadeInNigeria for better reach in your next campaign.", "type": "hashtag_recommendation", "generated_at": datetime.datetime.now() - datetime.timedelta(days=1)},
    ]

    key_metrics = {
        "total_followers": random.randint(1000, 100000),
        "avg_engagement_rate": round(random.uniform(1.0, 5.0), 2),
        "posts_this_week": random.randint(5, 50)
    }
    key_metrics["total_followers_formatted"] = f"{key_metrics['total_followers']:,}"


    # Use a subset of campaign data for the dashboard overview
    dashboard_campaign_overview = []
    for camp in all_campaigns_data:
        dashboard_campaign_overview.append({
            "name": camp.name,
            "status": camp.status,
            "reach": camp.total_reach if hasattr(camp, 'total_reach') else (camp.reach if hasattr(camp, 'reach') else 0), # Prioritize total_reach
            "engagement_rate": camp.avg_engagement_rate if hasattr(camp, 'avg_engagement_rate') else (camp.engagement_rate if hasattr(camp, 'engagement_rate') else 0.0),
            "reach_formatted": f"{(camp.total_reach if hasattr(camp, 'total_reach') else (camp.reach if hasattr(camp, 'reach') else 0)):,}"
        })


    return {
        "key_metrics": key_metrics,
        "trends": mock_trends,
        "insights": mock_insights,
        "campaigns_overview": dashboard_campaign_overview
    }

@app.route('/')
def dashboard():
    """Renders the main dashboard page."""
    all_campaigns = get_mock_campaigns_data() # This now returns processed Campaign objects
    dashboard_data = get_mock_dashboard_data(all_campaigns) # Pass them to generate dashboard specific view
    return render_template('dashboard.html', data=dashboard_data, current_year=datetime.datetime.now().year, alerts=get_mock_alerts())

@app.route('/campaigns')
def campaigns_page():
    """Renders the dedicated campaigns page."""
    all_campaigns_data = get_mock_campaigns_data() # Get the full, processed campaign objects
    return render_template('campaigns.html', campaigns=all_campaigns_data, current_year=datetime.datetime.now().year, alerts=get_mock_alerts())

# Placeholder for Alert model if models.py is not available (e.g. direct ui/app.py run)
if not MODELS_AVAILABLE:
    class MockAlert:
        def __init__(self, alert_id, user_id, message, alert_type="general", severity="info",
                     related_entity_id=None, related_entity_type=None, timestamp=None, is_read=False):
            self.alert_id = alert_id
            self.user_id = user_id
            self.message = message
            self.type = alert_type
            self.severity = severity
            self.related_entity_id = related_entity_id
            self.related_entity_type = related_entity_type
            self.timestamp = timestamp or datetime.datetime.utcnow()
            self.is_read = is_read
    Alert = MockAlert if not MODELS_AVAILABLE else AppAlert # Use AppAlert if available from src.models
else:
    from src.models import Alert as AppAlert # Explicitly import if MODELS_AVAILABLE is True
    Alert = AppAlert


def get_mock_alerts():
    """Generates a list of mock Alert objects."""
    # In a real app, these would be fetched from the AlertingService/database for the current user
    alerts_list = [
        Alert(alert_id="alert1", user_id="mock_user",
              message="🚀 New significant trend: '#TechThursday' is gaining traction with 150 mentions.",
              alert_type="new_trend", severity="info", timestamp=datetime.datetime.now() - datetime.timedelta(minutes=30)),
        Alert(alert_id="alert2", user_id="mock_user",
              message="⚠️ Campaign 'Q1 Sales Push' engagement dropped by 25%! Current rate: 1.8%.",
              alert_type="campaign_performance_change", severity="critical", related_entity_id="camp_Q1Sales",
              timestamp=datetime.datetime.now() - datetime.timedelta(hours=1), is_read=False),
        Alert(alert_id="alert3", user_id="mock_user",
              message="💡 New insight: Your audience is most active on Instagram around 6 PM on Fridays.",
              alert_type="new_insight", severity="info", timestamp=datetime.datetime.now() - datetime.timedelta(hours=3), is_read=True),
        Alert(alert_id="alert4", user_id="mock_user",
              message="📈 Trend '#NaijaInnovation' is growing rapidly! Now at 250 mentions.",
              alert_type="trend_velocity_spike", severity="warning",
              timestamp=datetime.datetime.now() - datetime.timedelta(minutes=5), is_read=False),
    ]
    # Filter out read alerts for badge count, but pass all to template for dropdown
    # unread_alerts = [a for a in alerts_list if not a.is_read]
    return alerts_list


@app.route('/trends')
def trends_page():
    """A dedicated page for all trends (example)."""
    # For now, reuse some mock data logic
    # This part of mock data generation should ideally be centralized or use the AI module
    mock_trends_data = get_mock_dashboard_data(get_mock_campaigns_data())['trends'] # Re-evaluate how trends are sourced

    full_mock_trends_display = [ # More detailed for the trends page
        {"term": "#NaijaBusiness", "count": random.randint(50, 200)},
        {"term": "Lagos SMEs", "count": random.randint(30, 150)},
        {"term": "#SocialMediaMarketing", "count": random.randint(20, 100)},
        {"term": "Fintech in Nigeria", "count": random.randint(10, 80)},
        {"term": "#SupportLocalNG", "count": random.randint(40, 180)},
        {"term": "Ecommerce growth", "count": random.randint(35,160)},
        {"term": "#DigitalNigeria", "count": random.randint(25,120)},
    ]
    full_mock_trends_display.sort(key=lambda x: x['count'], reverse=True)
    return render_template('trends.html', trends=full_mock_trends_display, current_year=datetime.datetime.now().year, alerts=get_mock_alerts())

@app.route('/settings')
def settings_page():
    """Placeholder for a settings page."""
    return render_template('settings.html', current_year=datetime.datetime.now().year, alerts=get_mock_alerts())


if __name__ == '__main__':
    # Note: In a production environment, use a WSGI server like Gunicorn or Waitress.
    # The host '0.0.0.0' makes the app accessible from other devices on the network.
    # Debug mode should be OFF in production.
    app.run(debug=True, host='0.0.0.0', port=5001)
