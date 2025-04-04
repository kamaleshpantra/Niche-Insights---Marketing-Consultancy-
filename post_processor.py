import json
import os
import re
import time
from api_clients import reddit, call_huggingface_api
from config import logging, MAX_TEXT_LENGTH

# Load company knowledge
def load_company_knowledge(file_path="company_knowledge.json"):
    default_knowledge = {
        "CI/CD": "Our AI-driven FlowCI optimizes CI/CD pipelines for startups, boosting efficiency in niche tech forums.",
        "Database": "DBScale uses AI to scale databases for SaaS, enhancing performance for niche online communities.",
        "Auth": "SecureAuth leverages AI for secure authentication, protecting niche community platforms.",
        "Marketing": "Our AI marketing tools drive engagement in niche communities, establishing thought leadership.",
        "SaaS": "Our AI-enhanced SaaS solutions redefine infrastructure and security for niche technical discussions.",
        "Other": "Engage with us to explore AI-driven opportunities in niche online communities."
    }
    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        with open(file_path, "w") as f:
            json.dump(default_knowledge, f, indent=4)
        return default_knowledge
    except Exception as e:
        logging.error(f"Error loading company knowledge: {e}")
        return default_knowledge

COMPANY_KNOWLEDGE = load_company_knowledge()

# Fetch Reddit posts
def fetch_reddit_posts(subreddit_name, limit=5):
    if not subreddit_name or not re.match(r'^[a-zA-Z0-9_]+$', subreddit_name):
        logging.error(f"Invalid subreddit name: {subreddit_name}")
        return []
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = []
        for submission in subreddit.hot(limit=limit):
            posts.append({
                "id": submission.id,
                "title": submission.title,
                "body": submission.selftext,
                "comments": [comment.body for comment in submission.comments],
                "score": submission.score,
                "num_comments": submission.num_comments,
                "url": submission.url
            })
            time.sleep(1)
        logging.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
        return sorted(posts, key=lambda x: x["score"] + x["num_comments"], reverse=True)
    except Exception as e:
        logging.error(f"Error fetching Reddit posts: {e}")
        return []

# Preprocess text
def preprocess_text(text):
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()

# Classify text (keyword-based)
def classify_text(text):
    keywords = {
        "CI/CD": ["ci/cd", "pipeline", "deployment", "automation", "tech"],
        "Database": ["database", "db", "scaling", "storage", "saas"],
        "Auth": ["authentication", "auth", "security", "microservices", "platform"],
        "Marketing": ["marketing", "campaign", "audience", "engagement", "community", "niche"],
        "SaaS": ["saas", "software", "service", "platform", "niche", "tech"],
    }
    text_lower = preprocess_text(text[:MAX_TEXT_LENGTH])
    matched_topics = [t for t, kw in keywords.items() if any(k in text_lower for k in kw)]
    return matched_topics or ["Other"]

# Generate response (Hugging Face with fallback)
def generate_response(post, topic):
    base_response = " ".join([COMPANY_KNOWLEDGE.get(t, "Engage with us for AI insights.") for t in topic])
    blog_snippet = "Our recent article on SaaS optimization highlights AI-driven efficiency gains."
    prompt = (
        f"Respond as an AI for niche community engagement on Reddit: '{post['title']} {post['body'][:200]}'. "
        f"Use this context: {base_response} Company insight: {blog_snippet} "
        f"Focus on SaaS, AI, marketing, or tech, emphasizing thought leadership. "
        f"Maintain a professional, friendly tone consistent with a tech-savvy marketing consultancy."
    )
    try:
        response = call_huggingface_api(prompt)[:1000]
        logging.info(f"Generated response for post '{post['title']}': {response[:100]}...")
        return response
    except Exception as e:
        logging.error(f"Response Generation Error: {str(e)}")
        fallback_response = (
            f"Thanks for sharing '{post['title']}'! {base_response} {blog_snippet} "
            "Visit our blog for more insights!"
        )
        logging.info(f"Falling back to static response: {fallback_response[:100]}...")
        return fallback_response