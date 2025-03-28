import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv("details.env")

# Environment variables
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Validate environment variables
if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, HUGGINGFACE_API_KEY, SLACK_WEBHOOK_URL]):
    raise ValueError("Missing environment variables. Check your details.env file.")

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Application settings
DEFAULT_SUBREDDIT = "SaaS"
MONITOR_INTERVAL = 300  # 5 minutes
MAX_TEXT_LENGTH = 300   # For classification/sentiment