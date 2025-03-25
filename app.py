import streamlit as st
import pandas as pd
import plotly.express as px
from config import DEFAULT_SUBREDDIT, logging
from post_processor import fetch_reddit_posts, classify_text, generate_response
from slack_notifier import send_to_slack
from analytics import calculate_engagement_metrics, analyze_sentiment

def main():
    st.set_page_config(page_title="Niche Insights | Marketing Consultancy", layout="wide", page_icon="🧩")
    st.markdown("""
    <style>
    .main { background-color: #ffffff; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    .header { color: #1a73e8; font-size: 36px; font-weight: bold; text-align: center; }
    .subheader { color: #333333; font-size: 24px; margin-top: 20px; font-weight: 600; }
    .input-container { display: flex; gap: 20px; background-color: #f5f7fa; padding: 15px; border-radius: 6px; }
    .stButton>button { background-color: #1a73e8; color: #ffffff; border-radius: 4px; padding: 10px 30px; }
    .output { background-color: #f5f7fa; padding: 15px; border-radius: 6px; margin-top: 15px; }
    .metric { background-color: #ffffff; padding: 10px; border-radius: 6px; text-align: center; font-size: 18px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="header">Niche Insights | Marketing Consultancy</div>', unsafe_allow_html=True)

    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    subreddit = st.text_input("Subreddit", DEFAULT_SUBREDDIT)
    limit = st.number_input("Posts to Analyze", min_value=1, max_value=10, value=5)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Analyze Niche Opportunities"):
        with st.spinner("Analyzing niche communities..."):
            posts = fetch_reddit_posts(subreddit, limit)
            if not posts:
                st.error("No posts found or error occurred. Check logs.")
                return

            st.markdown(f'<div class="subheader">Opportunities from r/{subreddit}</div>', unsafe_allow_html=True)
            data = []
            for post in posts:
                full_text = post['title'] + " " + post['body']
                topic = classify_text(full_text)
                ai_response = generate_response(post, topic)
                quality, impact, sentiment, conversion = calculate_engagement_metrics(ai_response, full_text, post['url'])
                slack_status = send_to_slack(post, ai_response)
                data.append({
                    "Title": post['title'], "Body": post['body'], "Topic": ", ".join(topic),
                    "AI Response": ai_response, "Sentiment": sentiment, "Response Quality": quality,
                    "Impact Score": impact, "Conversion Potential": conversion, "Slack Status": slack_status,
                    "Post Score": post['score'], "Comment Count": post['num_comments']
                })

            df = pd.DataFrame(data)
            for _, row in df.iterrows():
                st.markdown(f'''
                    <div class="output">
                        <strong>Title:</strong> {row["Title"]}<br>
                        <strong>Body:</strong> {row["Body"][:300] + "..." if len(row["Body"]) > 300 else row["Body"]}<br>
                        <strong>Topic:</strong> {row["Topic"]}<br>
                        <strong>AI Response:</strong> {row["AI Response"]}<br>
                        <strong>Impact Score:</strong> {row["Impact Score"]:.2f}<br>
                        <strong>Slack Status:</strong> {row["Slack Status"]}
                    </div>
                ''', unsafe_allow_html=True)

            st.markdown('<div class="subheader">Engagement Analytics</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f'<div class="metric">Posts Analyzed: {len(df)}</div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div class="metric">Avg Impact: {df["Impact Score"].mean():.2f}</div>', unsafe_allow_html=True)

            if not df.empty:
                fig = px.pie(names=df["Topic"].value_counts().index, values=df["Topic"].value_counts().values, title="Topic Distribution")
                st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()