from textblob import TextBlob
from config import logging, MAX_TEXT_LENGTH

def analyze_sentiment(text):
    try:
        blob = TextBlob(text[:MAX_TEXT_LENGTH])
        sentiment = blob.sentiment.polarity
        return "Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"
    except Exception as e:
        logging.error(f"Sentiment analysis error: {e}")
        return "Neutral"

def calculate_engagement_metrics(response, post_text, post_url=None, post_score=0, num_comments=0):
    words = len(response.split())
    response_quality = min(1.0, words / 100.0)
    sentiment = analyze_sentiment(post_text)
    impact_score = response_quality * (1.0 if sentiment == "Positive" else 0.5 if sentiment == "Neutral" else 0.1)
    base_engagement = 0.1 + (0.2 if post_url else 0.0)
    conversion_potential = min(1.0, (impact_score + base_engagement) * (1.0 if sentiment == "Positive" else 0.5 if sentiment == "Neutral" else 0.1))
    reach = post_score + num_comments  # Reach as sum of upvotes and comments
    return response_quality, impact_score, sentiment, conversion_potential, reach