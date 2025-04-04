import requests
import time
from config import SLACK_WEBHOOK_URL, logging
from datetime import datetime

def send_to_slack(post, response, max_retries=3, delay=5, real_time=False):
    headers = {"Content-Type": "application/json"}
    sanitized_title = post['title'].replace("`", "'").replace("\n", " ")[:200]
    sanitized_body = post['body'].replace("`", "'").replace("\n", " ")[:500]
    sanitized_response = response.replace("`", "'").replace("\n", " ")[:1000]
    payload = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"Niche Opportunity: {sanitized_title}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Title:*\n{sanitized_title}\n*Body:*\n>{sanitized_body}\n*Suggested Response:*\n>{sanitized_response}"}},
            {"type": "actions", "elements": [
                {"type": "button", "action_id": f"approve_{post['id']}", "text": {"type": "plain_text", "text": "Approve 🌠"}, "style": "primary", "value": sanitized_response},
                {"type": "button", "action_id": f"reject_{post['id']}", "text": {"type": "plain_text", "text": "Reject ⚠️"}, "style": "danger", "value": "reject"}
            ]}
        ]
    }
    for attempt in range(max_retries):
        try:
            response = requests.post(SLACK_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logging.info(f"Slack message sent for post: {sanitized_title}")
            return "Sent to Slack for Approval"
        except requests.RequestException as e:
            logging.error(f"Slack attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                with open("slack_failures.log", "a", encoding="utf-8") as f:
                    f.write(f"Failed at {datetime.now()}: Title='{sanitized_title}', Body='{sanitized_body}', Response='{sanitized_response}'\n")
                return "Slack send failed (Logged locally)"
    return "Slack send failed"