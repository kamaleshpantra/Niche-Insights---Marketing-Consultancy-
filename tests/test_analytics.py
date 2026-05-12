import pytest
from src.core.analytics import analyze_sentiment, calculate_engagement_metrics

def test_analyze_sentiment_positive():
    assert analyze_sentiment("This is amazing and great!") == "Positive"

def test_analyze_sentiment_negative():
    assert analyze_sentiment("This is terrible and bad.") == "Negative"

def test_calculate_engagement_metrics():
    response = "This is a long response that should have good quality because it has many words." * 10
    post_text = "Good news everyone!"
    quality, impact, sentiment, conversion, reach = calculate_engagement_metrics(response, post_text, post_score=10, num_comments=5)
    
    assert quality > 0.5
    assert sentiment == "Positive"
    assert reach == 15
    assert impact > 0
