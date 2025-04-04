import os
from dotenv import load_dotenv
import logging

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")

if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, HUGGINGFACE_API_KEY, SLACK_WEBHOOK_URL]):
    raise ValueError("Missing environment variables. Check your .env file.")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

DEFAULT_SUBREDDIT = "SaaS"
MONITOR_INTERVAL = 300
MAX_TEXT_LENGTH = 300