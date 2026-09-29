"""
Supabase Edge Function for CallCoach-AI Flask Backend
Wraps existing app logic into a serverless-compatible handler
"""
import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv

# Load root app if available
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Load .env if present
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_UPLOAD_MB", "2048")) * 1024 * 1024

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DB setup
DB_PATH = os.getenv("DB_PATH", "/tmp/callcoach.db")


@app.before_request
def before_request():
    logger.info(f"{datetime.utcnow().isoformat()} | Request: {request.method} {request.path}")


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", os.getenv("CORS_ORIGINS", "*"))
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    return response


# Health Check
@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "callcoach-backend",
        "platform": "supabase-edge-function",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("GIT_COMMIT", "dev")
    }), 200


# Proxy to existing Flask logic
@app.route("/api/upload", methods=["POST"])
def upload():
    try:
        from src.api.whip_api import process_uploaded_file
        return process_uploaded_file(request)
    except ImportError:
        return jsonify({"error": "Upload module not found"}), 500
    except Exception as e:
        logger.exception("Upload failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze/<job_id>", methods=["POST"])
def analyze(job_id: str):
    try:
        from src.core.evaluator import analyze_job
        return analyze_job(job_id, request)
    except Exception as e:
        logger.exception("Analysis failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/jobs", methods=["GET"])
def jobs():
    try:
        from src.core.evaluator import list_jobs
        return list_jobs()
    except Exception as e:
        logger.exception("Job listing failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/trends-data", methods=["GET"])
def trends():
    try:
        from src.core.metrics import get_trends
        return get_trends()
    except Exception as e:
        logger.exception("Trends fetch failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/settings", methods=["POST"])
def save_settings():
    try:
        from src.core.config import update_settings
        return update_settings(request)
    except Exception as e:
        logger.exception("Settings update failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/report/<int:report_id>", methods=["GET"])
def get_report(report_id: int):
    try:
        from src.core.evaluator import fetch_report
        return fetch_report(report_id)
    except Exception as e:
        logger.exception("Report fetch failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/clip-candidates/<job_id>", methods=["GET"])
def clip_candidates(job_id: str):
    try:
        from src.api.whip_api import get_clip_candidates
        return get_clip_candidates(job_id)
    except Exception as e:
        logger.exception("Clip candidates fetch failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/search-transcript", methods=["GET"])
def search_transcript():
    try:
        from src.core.search import search_transcripts
        query = request.args.get("q", "")
        return search_transcripts(query)
    except Exception as e:
        logger.exception("Search failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/deliver/slack", methods=["POST"])
def deliver_slack():
    try:
        from src.api.slack import send_summary
        return send_summary(request)
    except Exception as e:
        logger.exception("Slack delivery failed")
        return jsonify({"error": str(e)}), 500


@app.route("/api/deliver/notion", methods=["POST"])
def deliver_notion():
    try:
        from src.api.notion import export_report
        return export_report(request)
    except Exception as e:
        logger.exception("Notion export failed")
        return jsonify({"error": str(e)}), 500


def handle_request(req):
    """Main entry point for Supabase Edge Function"""
    # Convert incoming JSON request to Flask request context
    with app.test_request_context(
        path=req.url,
        method=req.method,
        headers=dict(req.headers),
        data=req.body,
        json=req.json if req.headers.get('content-type') == 'application/json' else None,
        query_string=req.query_params
    ):
        try:
            response = app.full_dispatch_request()
            return {
                "body": response.response,
                "status": int(response.status_code),
                "headers": dict(response.headers)
            }
        except Exception as e:
            logger.exception(f"Unhandled error in {req.method} {req.url}")
            return {
                "body": [json.dumps({"error": "Internal Server Error", "details": str(e)})],
                "status": 500,
                "headers": {"Content-Type": "application/json"}
            }


# For local testing
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))