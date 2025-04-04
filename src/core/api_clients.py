import praw
import requests
from .config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, HUGGINGFACE_API_KEY, HUGGINGFACE_MODEL, logging
import backoff

def init_reddit():
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        logging.info("Reddit API initialized successfully.")
        return reddit
    except Exception as e:
        logging.error(f"Reddit API Initialization Error: {e}")
        raise

reddit = init_reddit()

@backoff.on_exception(backoff.expo, requests.exceptions.RequestException, max_tries=3, max_time=180)
def call_huggingface_api(prompt, timeout=60):
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}", "Content-Type": "application/json"}
    try:
        logging.info(f"Sending request to Hugging Face API with model: {HUGGINGFACE_MODEL} and prompt: {prompt[:100]}...")
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}",
            headers=headers,
            json={"inputs": prompt},
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        logging.info(f"Hugging Face API response: {result}")
        if isinstance(result, list) and result and "generated_text" in result[0]:
            return result[0]["generated_text"].strip()
        logging.error(f"Unexpected Hugging Face response format: {result}")
        raise ValueError("Invalid API response format")
    except requests.RequestException as e:
        logging.error(f"Hugging Face API request failed: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error in Hugging Face API call: {str(e)}")
        raise