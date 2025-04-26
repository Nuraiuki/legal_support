from flask import Flask, jsonify, request
import os
import logging
import subprocess
import time
from datetime import datetime, timedelta
import json
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "tomyris-default-secret-key")

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Start the bot process
bot_process = None
start_time = datetime.now()

# Start bot in a separate process
def ensure_bot_running():
    global bot_process, start_time
    
    # Check if bot process exists and is still running
    if bot_process is None or bot_process.poll() is not None:
        logger.info("Starting Telegram bot process...")
        try:
            # Create a new bot process
            bot_process = subprocess.Popen(
                ["python3", "bot.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            start_time = datetime.now()
            logger.info(f"Bot process started with PID: {bot_process.pid}")
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            return False
    return True

# Initial bot start
ensure_bot_running()

# Check bot status and restart if needed
@app.before_request
def check_bot():
    ensure_bot_running()

# Routes
@app.route('/')
def index():
    # Check if bot is running
    is_running = bot_process is not None and bot_process.poll() is None
    bot_status = "Running" if is_running else "Not running"
    
    # Calculate uptime
    uptime = datetime.now() - start_time
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    return f"""
    <!DOCTYPE html>
    <html data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tomyris Bot Dashboard</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row">
                <div class="col-md-8 offset-md-2">
                    <div class="card">
                        <div class="card-header">
                            <h2 class="text-center">Tomyris Telegram Bot</h2>
                        </div>
                        <div class="card-body">
                            <div class="alert {'alert-success' if is_running else 'alert-danger'}">
                                <h4 class="alert-heading">Status: {bot_status}</h4>
                                <p>This is the dashboard for the Tomyris Telegram Bot. The bot runs in the background and provides legal and emotional support for women in Kazakhstan.</p>
                            </div>
                            <hr>
                            <h5>Bot Information</h5>
                            <ul class="list-group mb-3">
                                <li class="list-group-item">Started at: {start_time.strftime("%Y-%m-%d %H:%M:%S")}</li>
                                <li class="list-group-item">Uptime: {uptime_str}</li>
                                <li class="list-group-item">Environment: Replit</li>
                                <li class="list-group-item">Mode: Long-polling</li>
                            </ul>
                        </div>
                        <div class="card-footer text-muted text-center">
                            Tomyris Bot - A supportive AI assistant for women in Kazakhstan
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/status')
def status():
    # Check if bot is running
    is_running = bot_process is not None and bot_process.poll() is None
    
    # Count users
    user_count = 0
    users_file = Path("data/users.csv")
    if users_file.exists():
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                # Skip header
                next(f)
                user_count = sum(1 for line in f if line.strip())
        except Exception as e:
            logger.error(f"Error counting users: {e}")
    
    # Count cached responses
    cache_count = 0
    cache_file = Path("cache/faq.json")
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                cache_count = len(cache_data)
        except Exception as e:
            logger.error(f"Error counting cache entries: {e}")
    
    # Calculate uptime
    uptime = datetime.now() - start_time
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    return jsonify({
        "status": "running" if is_running else "not_running",
        "users": user_count,
        "cached_responses": cache_count,
        "uptime": uptime_str,
        "started_at": start_time.isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)