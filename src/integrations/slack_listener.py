import json
import logging
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse
import requests
from src.core.database import update_post_status

# Initialize FastAPI
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/slack/interactivity")
async def slack_interactivity(payload: str = Form(...)):
    """
    Handle Slack interaction payloads (e.g., button clicks).
    """
    try:
        data = json.loads(payload)
        user = data["user"]["username"]
        actions = data["actions"]
        
        for action in actions:
            action_id = action["action_id"]
            post_id = action_id.split("_")[1]
            
            if action_id.startswith("approve_"):
                status = f"Approved by {user}"
                update_post_status(post_id, status)
                logger.info(f"Post {post_id} approved by {user}")
                
                # Optionally send a message back to Slack
                response_url = data["response_url"]
                message = {
                    "text": f"✅ Opportunity approved by @{user}. Insight saved to database.",
                    "replace_original": False
                }
                requests.post(response_url, json=message)
                
            elif action_id.startswith("reject_"):
                status = f"Rejected by {user}"
                update_post_status(post_id, status)
                logger.info(f"Post {post_id} rejected by {user}")
                
                response_url = data["response_url"]
                message = {
                    "text": f"❌ Opportunity rejected by @{user}.",
                    "replace_original": False
                }
                requests.post(response_url, json=message)

        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        logger.error(f"Error processing Slack interactivity: {e}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
