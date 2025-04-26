"""
Tomyris Bot - A supportive AI assistant for women in Kazakhstan
Minimal Flask application that just reports bot status
"""
from flask import Flask, render_template_string
import logging
import os
import subprocess
import time
import threading
from pathlib import Path

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create the Flask app
app = Flask(__name__)

# Bot process tracking
bot_process = None
bot_thread = None

def ensure_folders_exist():
    """Ensure required folders exist."""
    folders = ["data", "logs", "cache", "prompt"]
    for folder in folders:
        Path(folder).mkdir(exist_ok=True)
    
    # Create data/users.csv with headers if it doesn't exist
    users_file = Path("data/users.csv")
    if not users_file.exists():
        users_file.parent.mkdir(exist_ok=True)
        with open(users_file, 'w', encoding='utf-8') as f:
            f.write("user_id,username,first_name,joined_at\n")
    
    # Create an empty cache file if it doesn't exist
    cache_file = Path("cache/faq.json")
    if not cache_file.exists():
        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write("{}")

def run_bot():
    """Run the bot in a separate thread"""
    import bot
    bot.main()

# Start the bot in a separate thread
def start_bot_thread():
    global bot_thread
    if bot_thread is None or not bot_thread.is_alive():
        ensure_folders_exist()
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True  # This thread will be terminated when main thread exits
        bot_thread.start()
        logger.info("Bot thread started")
    return bot_thread.is_alive()

# Routes
@app.route('/')
def index():
    """Simple status page"""
    bot_running = bot_thread is not None and bot_thread.is_alive()
    status = "RUNNING" if bot_running else "STOPPED"
    
    # Count users
    user_count = 0
    users_file = Path("data/users.csv")
    if users_file.exists():
        with open(users_file, 'r', encoding='utf-8') as f:
            # Skip header
            next(f)
            for line in f:
                if line.strip():
                    user_count += 1
    
    html = """
    <!DOCTYPE html>
    <html data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tomyris Bot Status</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row">
                <div class="col-md-8 offset-md-2">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h2 class="text-center mb-0">Tomyris Bot Status</h2>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-{{ 'success' if running else 'danger' }}">
                                <h4 class="alert-heading">Status: {{ status }}</h4>
                                <p>The Tomyris bot is a Telegram bot that provides AI-powered legal and emotional support for women in Kazakhstan.</p>
                            </div>
                            
                            <p class="lead">Bot is currently {{ 'online' if running else 'offline' }}</p>
                            <p>Registered users: {{ users }}</p>
                            
                            <div class="mt-4">
                                <h5>🤖 Bot Features</h5>
                                <ul class="list-group">
                                    <li class="list-group-item">Legal support for women in Kazakhstan</li>
                                    <li class="list-group-item">Emotional support and resources</li>
                                    <li class="list-group-item">Crisis response system</li>
                                    <li class="list-group-item">Multi-language support (Kazakh and Russian)</li>
                                </ul>
                            </div>
                        </div>
                        <div class="card-footer text-center text-muted">
                            Tomyris - Supporting women in Kazakhstan
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(
        html, 
        running=bot_running,
        status=status,
        users=user_count
    )

# Start the bot thread when the app starts
start_bot_thread()