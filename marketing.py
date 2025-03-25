import os
import streamlit as st
import praw
import requests
import time
import logging
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv("details.env")

# Secure API keys using environment variables
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Validate environment variables
if not all([REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, HUGGINGFACE_API_KEY, SLACK_WEBHOOK_URL]):
    raise ValueError("Missing environment variables. Check your .env file.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Logs to console
    ]
)

# Initialize Reddit API
try:
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    logging.info("Reddit API initialized successfully.")
except Exception as e:
    logging.error(f"Reddit API Initialization Error: {e}")
    raise

# Knowledge base
company_knowledge = {
    "CI/CD": "Our tool, FlowCI, automates pipelines for startups, improving speed and reliability.",
    "Database": "DBScale provides scalable, reliable database solutions for SaaS companies.",
    "Auth": "SecureAuth ensures advanced authentication security for microservices.",
    "Marketing": "We offer marketing automation tools to help you engage your audience effectively.",
    "SaaS": "Comprehensive solutions for SaaS companies, including infrastructure, security, and marketing.",
    "Other": "Thanks for the discussion! We appreciate your insights."
}

# Fetch Reddit posts
def fetch_reddit_posts(subreddit_name, limit=10):
    try:
        subreddit = reddit.subreddit(subreddit_name)
        posts = []
        for submission in subreddit.hot(limit=limit):
            post = {
                "id": submission.id,
                "title": submission.title,
                "text": submission.selftext,
                "comments": [comment.body for comment in submission.comments]
            }
            posts.append(post)
            time.sleep(1)  # Prevent rate limiting
        logging.info(f"Fetched {len(posts)} posts from r/{subreddit_name}")
        return posts
    except Exception as e:
        logging.error(f"Error fetching Reddit posts: {e}")
        return []

# Classify posts using Hugging Face API
def classify_text(text):
    try:
        topics = list(company_knowledge.keys())
        prompt = f"Classify this text strictly into one or more of: CI/CD, Database, Auth, Marketing, SaaS, Other. If none apply, return 'Other'. Return a single topic or multiple topics separated by ' and ' (e.g., 'SaaS and Marketing'). Do not add extra text or explanations. Text: '{text}'"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
            headers=headers,
            json={"inputs": prompt},
            timeout=60  # Add a timeout to prevent indefinite hanging
        )
        response.raise_for_status()
        result = response.json()
        logging.info(f"Hugging Face response for classification: {result}")
        if isinstance(result, dict) and 'error' not in result:
            if isinstance(result, list) and len(result) > 0:
                if "generated_text" in result[0]:
                    generated_text = result[0]["generated_text"].strip()
                # Handle multi-topic responses (e.g., "SaaS and Marketing")
                if " and " in generated_text:
                    return [t.strip() for t in generated_text.split(" and ")]  # Keep exact case from Hugging Face
                return generated_text if generated_text in topics else "Other"
            else:
                logging.warning(f"Hugging Face API response missing 'generated_text': {result}")
                return "Other"
        return "Other"
    except requests.RequestException as e:
        logging.error(f"Classification Error (Hugging Face API): {e}")
        st.error(f"Classification Error: {e}")
        return "Other"

# Generate AI response using Hugging Face API
def generate_response(post, topic):
    if isinstance(topic, list):
        # Combine knowledge for multiple topics
        base_responses = [company_knowledge.get(t, "Thanks for the discussion!") for t in topic]
        base_response = " ".join(base_responses)
    else:
        base_response = company_knowledge.get(topic, "Thanks for the discussion!")
    prompt = f"Respond professionally as a company rep: '{post['title']} {post['text']}'. Use this info: {base_response}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1",
            headers=headers,
            json={"inputs": prompt}
        )
        response.raise_for_status()
        result = response.json()
        logging.info(f"Hugging Face response for generation: {result}")
        if isinstance(result, list) and len(result) > 0:
            if "generated_text" in result[0]:
                return result[0]["generated_text"].strip()
            else:
                logging.warning(f"Hugging Face API response missing 'generated_text': {result}")
                return "Unable to generate a response."
        return "Unable to generate a response."
    except requests.RequestException as e:
        logging.error(f"Response Generation Error: {e}")
        st.error(f"Response Generation Error: {e}")
        return "Unable to generate a response."

# Send to Slack
def send_to_slack(post, response):
    try:
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚀 New Post Alert: {post['title']}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Post Content:*\n```{post['title']}```\n\n*Suggested Response:*\n>{response}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Action Required:*\nPlease approve this response (Y/N)"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Approve (Y) 🚀"
                            },
                            "style": "primary",
                            "value": "approve"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Reject (N) ❌"
                            },
                            "style": "danger",
                            "value": "reject"
                        }
                    ]
                }
            ]
        }
        slack_response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        slack_response.raise_for_status()
        logging.info(f"Slack message sent for post: {post['title']}")
        return "Sent to Slack" if slack_response.status_code == 200 else "Slack send failed"
    except requests.RequestException as e:
        logging.error(f"Error sending to Slack: {e}")
        return "Slack send failed"

# Streamlit UI with enhanced, perfectly aligned, and visually stunning design
def main():
    # Set page configuration for a premium, perfectly aligned look
    st.set_page_config(
        page_title="AI-Powered Community Engagement Platform",
        layout="wide",
        initial_sidebar_state="collapsed",
        page_icon="🌟"
    )

    # Custom styling for a stunning, professional, and perfectly aligned design
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .header {
        color: #2c3e50;
        font-size: 60px;
        font-weight: bold;
        text-align: center;
        text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.15);
        margin-bottom: 40px;
        animation: fadeIn 1.5s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .subheader {
        color: #1E90FF;
        font-size: 36px;
        margin-top: 30px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        animation: slideIn 1s ease-in-out;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    .input-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin-bottom: 30px;
    }
    .stTextInput, .stButton {
        margin: 0 !important;
    }
    .stButton>button {
        background: linear-gradient(45deg, #1E90FF, #4169E1);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 18px 40px;
        font-size: 20px;
        box-shadow: 0 8px 20px rgba(30, 144, 255, 0.4);
        transition: transform 0.3s, box-shadow 0.3s, background 0.3s;
    }
    .stButton>button:hover {
        background: linear-gradient(45deg, #4169E1, #1E90FF);
        transform: translateY(-8px);
        box-shadow: 0 12px 25px rgba(30, 144, 255, 0.6);
    }
    .output {
        background: white;
        padding: 25px;
        border-radius: 12px;
        border: 2px solid #e0e6f1;
        margin-top: 20px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        animation: bounceIn 1s ease-in-out;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    @keyframes bounceIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }
    .error {
        color: #FF4D4F;
        background: #FFF0F0;
        padding: 25px;
        border-radius: 12px;
        border: 2px solid #FF4D4F;
        box-shadow: 0 8px 20px rgba(255, 77, 79, 0.4);
        animation: shake 0.5s ease-in-out;
        margin-top: 20px;
    }
    @keyframes shake {
        0% { transform: translateX(0); }
        25% { transform: translateX(-15px); }
        50% { transform: translateX(15px); }
        75% { transform: translateX(-15px); }
        100% { transform: translateX(0); }
    }
    .metric {
        background: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #e0e6f1;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        text-align: center;
        font-size: 24px;
        color: #2c3e50;
        transition: transform 0.3s, box-shadow 0.3s;
    }
    .metric:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 25px rgba(0, 0, 0, 0.2);
    }
    .visualization-container {
        margin-top: 30px;
        padding: 20px;
        background: white;
        border-radius: 12px;
        border: 2px solid #e0e6f1;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
    }
    .spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }
    .warning {
        color: #FFA500;
        background: #FFF8E1;
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #FFA500;
        box-shadow: 0 8px 20px rgba(255, 165, 0, 0.3);
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header with animation
    st.markdown('<div class="header">🌟 AI-Powered Community Engagement Platform</div>', unsafe_allow_html=True)

    # Input section with perfectly aligned, centered layout
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3, 1, 1], gap="medium")
    with col1:
        subreddit_name = st.text_input(
            "Enter a Subreddit to Monitor",
            "SaaS",
            help="Enter a subreddit name like 'SaaS', 'python', or 'technology'",
            key="subreddit_input",
            placeholder="e.g., SaaS",
            label_visibility="collapsed"
        )
    with col2:
        if st.button("Start Monitoring", help="Fetch and analyze posts from the subreddit", key="monitor_button"):
            st.session_state['monitoring'] = True
    with col3:
        st.image("https://via.placeholder.com/100x50.png?text=Logo", caption="Your Company Logo", use_column_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Output sections with animations, perfect alignment, and visualizations
    if 'monitoring' in st.session_state and st.session_state['monitoring']:
        st.markdown('<div class="subheader">Monitoring Results</div>', unsafe_allow_html=True)

        # Fetch and display posts with a progress bar and spinner
        st.write("Fetching posts...")
        with st.spinner("Loading posts..."):
            posts = fetch_reddit_posts(subreddit_name)
        st.write(f"<div class='output'>Fetched {len(posts)} posts: {posts[:2]}</div>", unsafe_allow_html=True)
        
        if not posts:
            st.markdown('<div class="error">No posts fetched. Check Reddit credentials and network.</div>', unsafe_allow_html=True)
            return
        
        relevant_posts = []
        progress_bar = st.progress(0)
        st.write("Classifying posts...")
        total_posts = len(posts)
        for i, post in enumerate(posts, 1):
            with st.spinner(f"Classifying post {i}/{total_posts}..."):
                combined_text = f"{post['title']} {post['text']}"
                topic = classify_text(combined_text)
            st.write(f"<div class='output'>Post: {post['title']} | Classified as: {topic}</div>", unsafe_allow_html=True)
            if isinstance(topic, list):
                for t in topic:
                    if t in company_knowledge:
                        relevant_posts.append({"post": post, "topic": t})
                        break
            elif topic in company_knowledge:
                relevant_posts.append({"post": post, "topic": topic})
            progress_bar.progress(i / total_posts)

        if not relevant_posts:
            st.markdown('<div class="warning">No relevant opportunities found.</div>', unsafe_allow_html=True)
            return
        
        st.write("Generating responses...")
        responses = []
        for item in relevant_posts:
            with st.spinner(f"Generating response for {item['post']['title']}..."):
                response = generate_response(item["post"], item["topic"])
            responses.append({"post": item["post"]["title"], "response": response})
            st.write(f"<div class='output'>Post: {item['post']['title']} | Response: {response}</div>", unsafe_allow_html=True)

        st.write("Sending to Slack...")
        for resp in responses:
            with st.spinner(f"Sending to Slack for {resp['post']}..."):
                slack_status = send_to_slack({"title": resp["post"]}, resp["response"])
            st.write(f"<div class='output'>{resp['post']} → {slack_status}</div>", unsafe_allow_html=True)

        # Analytics section with visualizations and perfect alignment
        st.markdown('<div class="subheader">Engagement Analytics</div>', unsafe_allow_html=True)

        # Prepare data for visualization
        analytics = {
            "posts_processed": len(posts),
            "responses_generated": len(responses),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        topic_counts = {}
        for post in relevant_posts:
            topic = post["topic"]
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Create a bar chart for topic distribution with enhanced styling
        df_topics = pd.DataFrame(list(topic_counts.items()), columns=['Topic', 'Count'])
        fig_topics = px.bar(df_topics, x='Topic', y='Count', title="Distribution of Classified Topics",
                           color='Count', color_continuous_scale='Viridis',
                           height=450, width=800)
        fig_topics.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=16, color="#2c3e50"),
            title_font_size=28,
            title_x=0.5,
            xaxis_title="Topics",
            yaxis_title="Count",
            showlegend=True
        )
        st.markdown('<div class="visualization-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_topics, use_container_width=False, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        # Create a pie chart for engagement metrics with enhanced styling
        engagement_data = pd.DataFrame({
            'Metric': ['Posts Processed', 'Responses Generated'],
            'Value': [analytics['posts_processed'], analytics['responses_generated']]
        })
        fig_engagement = px.pie(engagement_data, names='Metric', values='Value',
                               title="Engagement Metrics Overview",
                               color_discrete_sequence=px.colors.sequential.Viridis,
                               hole=0.3)
        fig_engagement.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=16, color="#2c3e50"),
            title_font_size=28,
            title_x=0.5,
            showlegend=True
        )
        st.markdown('<div class="visualization-container">', unsafe_allow_html=True)
        st.plotly_chart(fig_engagement, use_container_width=False, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        # Display metrics in a perfectly aligned, interactive grid
        col1, col2, col3 = st.columns(3, gap="large")
        with col1:
            st.markdown(f"<div class='metric'>Posts Processed: {analytics['posts_processed']}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric'>Responses Generated: {analytics['responses_generated']}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric'>Last Updated: {analytics['timestamp']}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()