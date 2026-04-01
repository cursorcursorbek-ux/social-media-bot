from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

CONFIG = {
    "youtube": {
        "client_id": "YOUR_YOUTUBE_CLIENT_ID",
        "client_secret": "YOUR_YOUTUBE_CLIENT_SECRET",
        "refresh_token": "YOUR_YOUTUBE_REFRESH_TOKEN",
    },
    "instagram": {
        "access_token": "YOUR_INSTAGRAM_ACCESS_TOKEN",
        "user_id": "YOUR_INSTAGRAM_USER_ID",
    },
    "tiktok": {
        "access_token": "YOUR_TIKTOK_ACCESS_TOKEN",
    },
    "twitter": {
        "api_key": "YOUR_TWITTER_API_KEY",
        "api_secret": "YOUR_TWITTER_API_SECRET",
        "access_token": "YOUR_TWITTER_ACCESS_TOKEN",
        "access_token_secret": "YOUR_TWITTER_ACCESS_TOKEN_SECRET",
    }
}

scheduled_posts = []
sent_posts = []

def post_to_youtube(text):
    try:
        import google.oauth2.credentials
        import googleapiclient.discovery
        creds = google.oauth2.credentials.Credentials(
            token=None,
            refresh_token=CONFIG["youtube"]["refresh_token"],
            client_id=CONFIG["youtube"]["client_id"],
            client_secret=CONFIG["youtube"]["client_secret"],
            token_uri="https://oauth2.googleapis.com/token"
        )
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
        request_body = {"snippet": {"text": text}}
        response = youtube.communityPosts().insert(part="snippet", body=request_body).execute()
        return {"success": True, "id": response.get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def post_to_instagram(text):
    try:
        import requests
        user_id = CONFIG["instagram"]["user_id"]
        token = CONFIG["instagram"]["access_token"]
        create_url = f"https://graph.facebook.com/v18.0/{user_id}/media"
        create_data = {"caption": text, "media_type": "TEXT", "access_token": token}
        create_resp = requests.post(create_url, data=create_data)
        media_id = create_resp.json().get("id")
        if not media_id:
            return {"success": False, "error": create_resp.json()}
        publish_url = f"https://graph.facebook.com/v18.0/{user_id}/media_publish"
        publish_data = {"creation_id": media_id, "access_token": token}
        publish_resp = requests.post(publish_url, data=publish_data)
        return {"success": True, "id": publish_resp.json().get("id")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def post_to_twitter(text):
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=CONFIG["twitter"]["api_key"],
            consumer_secret=CONFIG["twitter"]["api_secret"],
            access_token=CONFIG["twitter"]["access_token"],
            access_token_secret=CONFIG["twitter"]["access_token_secret"]
        )
        response = client.create_tweet(text=text)
        return {"success": True, "id": response.data["id"]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def post_to_tiktok(text):
    try:
        import requests
        url = "https://open.tiktokapis.com/v2/post/publish/text/init/"
        headers = {
            "Authorization": f"Bearer {CONFIG['tiktok']['access_token']}",
            "Content-Type": "application/json"
        }
        data = {
            "post_info": {"title": text, "privacy_level": "PUBLIC_TO_EVERYONE", "disable_comment": False},
            "source_info": {"source": "PULL_FROM_URL", "video_url": ""}
        }
        response = requests.post(url, headers=headers, json=data)
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/api/publish", methods=["POST"])
def publish():
    data = request.json
    text = data.get("text", "")
    platforms = data.get("platforms", [])
    if not text:
        return jsonify({"error": "Matn bo'sh"}), 400
    results = {}
    for platform in platforms:
        if platform == "youtube":
            results["youtube"] = post_to_youtube(text)
        elif platform == "instagram":
            results["instagram"] = post_to_instagram(text)
        elif platform == "twitter":
            results["twitter"] = post_to_twitter(text)
        elif platform == "tiktok":
            results["tiktok"] = post_to_tiktok(text)
    sent_posts.append({"text": text, "platforms": platforms, "time": datetime.now().isoformat(), "results": results})
    return jsonify({"success": True, "results": results})

@app.route("/api/schedule", methods=["POST"])
def schedule():
    data = request.json
    text = data.get("text", "")
    platforms = data.get("platforms", [])
    schedule_time = data.get("schedule_time", "")
    if not text or not schedule_time:
        return jsonify({"error": "Matn yoki vaqt bo'sh"}), 400
    post = {"id": len(scheduled_posts) + 1, "text": text, "platforms": platforms, "schedule_time": schedule_time, "status": "scheduled"}
    scheduled_posts.append(post)
    return jsonify({"success": True, "post": post})

@app.route("/api/posts", methods=["GET"])
def get_posts():
    return jsonify({"sent": sent_posts, "scheduled": scheduled_posts})

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "running", "sent_count": len(sent_posts), "scheduled_count": len(scheduled_posts)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
