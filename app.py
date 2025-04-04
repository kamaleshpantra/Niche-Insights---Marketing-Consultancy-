import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.core.config import DEFAULT_SUBREDDIT, MONITOR_INTERVAL, logging
from src.core.processor import fetch_reddit_posts, classify_text, generate_response
from src.integrations.slack import send_to_slack
from src.core.analytics import calculate_engagement_metrics, analyze_sentiment
import time

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
    .metric { background-color: #ffffff; padding: 10px; border-radius: 6px; text-align: center; font-size: 18px; border: 1px solid #e0e0e0; }
    .insight { background-color: #e8f0fe; padding: 15px; border-radius: 6px; margin-top: 15px; color: #1a73e8; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="header">Niche Insights | Marketing Consultancy</div>', unsafe_allow_html=True)
    st.write("Uncover actionable insights from niche communities with AI-driven analysis and storytelling.")

    if "data" not in st.session_state:
        st.session_state.data = []
        st.session_state.last_update = 0

    # Input Section
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    subreddit = st.text_input("Subreddit", DEFAULT_SUBREDDIT, help="Enter a subreddit to analyze (e.g., SaaS, Marketing).")
    limit = st.number_input("Posts to Analyze", min_value=1, max_value=10, value=5, help="Number of top posts to fetch.")
    auto_refresh = st.checkbox("Monitor Every 5 Minutes", value=False, help="Auto-refresh every 5 minutes.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Analyze Now") or (auto_refresh and time.time() - st.session_state.last_update > MONITOR_INTERVAL):
        with st.spinner("Analyzing niche communities..."):
            posts = fetch_reddit_posts(subreddit, limit)
            if not posts:
                st.error("No posts found or error occurred. Check logs.")
                if st.button("Retry"):
                    st.experimental_rerun()
                return

            st.session_state.data = []
            for post in posts:
                full_text = post['title'] + " " + post['body']
                topic = classify_text(full_text)
                ai_response = generate_response(post, topic)
                quality, impact, sentiment, conversion, reach = calculate_engagement_metrics(ai_response, full_text, post['url'], post['score'], post['num_comments'])
                slack_status = send_to_slack(post, ai_response)
                st.session_state.data.append({
                    "Title": post['title'], "Body": post['body'], "Topic": ", ".join(topic),
                    "AI Response": ai_response, "Sentiment": sentiment, "Response Quality": quality,
                    "Impact Score": impact, "Conversion Potential": conversion, "Slack Status": slack_status,
                    "Post Score": post['score'], "Comment Count": post['num_comments'], "Reach": reach
                })
            st.session_state.last_update = time.time()

    # Data Storytelling Section
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)

        # Story Header
        st.markdown(f'<div class="subheader">Storytelling Insights from r/{subreddit}</div>', unsafe_allow_html=True)
        st.write("Here’s what the data tells us about engagement opportunities in this community.")

        # Key Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric">Posts Analyzed: {len(df)}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric">Avg Impact Score: {df["Impact Score"].mean():.2f}</div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric">Total Reach: {int(df["Reach"].sum())}</div>', unsafe_allow_html=True)

        # Insight 1: Top Opportunity
        top_post = df.loc[df["Impact Score"].idxmax()]
        st.markdown(f'<div class="insight">📈 <strong>Top Opportunity:</strong> "{top_post["Title"]}" stands out with an impact score of {top_post["Impact Score"]:.2f} and reach of {int(top_post["Reach"])}. This post’s {top_post["Sentiment"]} sentiment suggests a high-potential engagement point.</div>', unsafe_allow_html=True)

        # Visualization 1: Sentiment Distribution
        sentiment_counts = df["Sentiment"].value_counts()
        fig_sentiment = px.bar(
            x=sentiment_counts.index, y=sentiment_counts.values,
            title="Sentiment Distribution Across Posts",
            labels={"x": "Sentiment", "y": "Number of Posts"},
            color=sentiment_counts.index,
            color_discrete_map={"Positive": "#00cc96", "Neutral": "#636efa", "Negative": "#ef553b"}
        )
        fig_sentiment.update_layout(showlegend=False)
        st.plotly_chart(fig_sentiment, use_container_width=True)
        st.write(f"The community leans {sentiment_counts.idxmax()} with {sentiment_counts.max()} posts, indicating the overall mood and potential response tone.")

        # Visualization 2: Topic Breakdown
        topic_counts = df["Topic"].str.split(", ").explode().value_counts()
        fig_topics = px.pie(
            names=topic_counts.index, values=topic_counts.values,
            title="Dominant Topics in the Community",
            hole=0.3
        )
        st.plotly_chart(fig_topics, use_container_width=True)
        st.write(f"Hot topics like {topic_counts.idxmax()} (mentioned {topic_counts.max()} times) drive discussions—ideal focus areas for engagement.")

        # Visualization 3: Reach vs Impact
        fig_reach_impact = px.scatter(
            df, x="Reach", y="Impact Score", size="Comment Count", color="Sentiment",
            hover_data=["Title"], title="Reach vs Impact: Where to Focus",
            color_discrete_map={"Positive": "#00cc96", "Neutral": "#636efa", "Negative": "#ef553b"}
        )
        st.plotly_chart(fig_reach_impact, use_container_width=True)
        st.write("Posts with high reach and impact (top-right) are prime candidates for thought leadership.")

        # Insight 2: Engagement Potential
        high_potential = df[df["Conversion Potential"] > df["Conversion Potential"].mean()]
        st.markdown(f'<div class="insight">🚀 <strong>Engagement Potential:</strong> {len(high_potential)} posts exceed average conversion potential ({df["Conversion Potential"].mean():.2f}). Targeting these could amplify your influence.</div>', unsafe_allow_html=True)

        # Detailed Post Breakdown
        st.markdown('<div class="subheader">Post-Level Insights</div>', unsafe_allow_html=True)
        for _, row in df.iterrows():
            st.markdown(f'''
                <div class="output">
                    <strong>Title:</strong> {row["Title"]}<br>
                    <strong>Body:</strong> {row["Body"][:300] + "..." if len(row["Body"]) > 300 else row["Body"]}<br>
                    <strong>Topic:</strong> {row["Topic"]}<br>
                    <strong>AI Response:</strong> {row["AI Response"]}<br>
                    <strong>Sentiment:</strong> {row["Sentiment"]}<br>
                    <strong>Impact Score:</strong> {row["Impact Score"]:.2f}<br>
                    <strong>Reach:</strong> {int(row["Reach"])}<br>
                    <strong>Slack Status:</strong> {row["Slack Status"]}
                </div>
            ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()