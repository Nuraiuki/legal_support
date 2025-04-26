#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tomyris Telegram Bot: A supportive AI assistant for women in Kazakhstan.
Provides legal and emotional support using OpenAI's GPT model.
"""

import os
import csv
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

import ai
import cache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# Ensure necessary directories exist
Path("data").mkdir(exist_ok=True)
Path("logs").mkdir(exist_ok=True)
Path("cache").mkdir(exist_ok=True)
Path("prompt").mkdir(exist_ok=True)

# Crisis keywords
CRISIS_KEYWORDS = ["боюсь", "нужна помощь", "panic", "I feel scared", "страшно", "беда"]

# YouTube lofi link for calming effect
LOFI_LINK = "https://youtu.be/5qap5aO4i9A"

# Emergency numbers
EMERGENCY_NUMBERS = "150, 111, 102"

# Callback data
AGREE_CB = "agree"

# User conversation histories
user_histories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    username = user.username or "No username"
    first_name = user.first_name or "No first name"
    
    # Create consent button using the AGREE_CB constant
    keyboard = [
        [InlineKeyboardButton("Согласен ✅", callback_data=AGREE_CB)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Приветствую, {first_name}! Я Томирис, ваш AI-ассистент по правовым и "
        f"эмоциональным вопросам для женщин в Казахстане.\n\n"
        f"Нажмите «Согласен» чтобы начать общение. "
        f"Я не храню ваши личные данные или историю диалогов.",
        reply_markup=reply_markup
    )
    
    # Log new user if not already in users.csv
    await log_new_user(user_id, username, first_name)

async def log_new_user(user_id, username, first_name):
    """Log new user to users.csv and notify admin."""
    users_file = Path("data/users.csv")
    
    # Create file with headers if it doesn't exist
    if not users_file.exists():
        with open(users_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["user_id", "username", "first_name", "joined_at"])
    
    # Check if user already exists
    existing_users = set()
    with open(users_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        for row in reader:
            if row:  # Check if row is not empty
                existing_users.add(int(row[0]))
    
    # Add user if new
    if user_id not in existing_users:
        with open(users_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                user_id, 
                username, 
                first_name, 
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        # Notify admin about new user
        if ADMIN_CHAT_ID:
            try:
                bot = Application.get_instance().bot
                await bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text=f"New user registered:\nID: {user_id}\nUsername: {username}\nName: {first_name}"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin: {e}")

async def agree_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user consent button press."""
    query = update.callback_query
    # Important: This line answers the callback query and removes the loading state
    await query.answer()
    
    await query.edit_message_text(
        text="Отлично! 💖 Чем могу помочь? Спросите меня о своих правах.\n\n"
        "Я здесь, чтобы ответить на вопросы о законодательстве Казахстана, "
        "оказать эмоциональную поддержку и направить вас к нужным ресурсам.\n\n"
        "Ты не одна. Томирис рядом — вместе мы справимся!"
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming text messages."""
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # Send "typing..." action
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, 
        action="typing"
    )
    
    # Check for crisis keywords
    if any(keyword in user_text.lower() for keyword in CRISIS_KEYWORDS):
        await send_crisis_response(update)
        return
    
    # Try to get from cache first
    cached_response = cache.get_cache(user_text)
    if cached_response:
        await update.message.reply_text(cached_response)
        return
    
    # Process with AI if not in cache
    try:
        # Get or initialize user history
        if user_id not in user_histories:
            user_histories[user_id] = []
        
        # Call OpenAI
        assistant_response, prompt_tokens, completion_tokens = await ai.ask_openai(
            user_histories[user_id], 
            user_text
        )
        
        # Update user history
        user_histories[user_id].append({"role": "user", "content": user_text})
        user_histories[user_id].append({"role": "assistant", "content": assistant_response})
        
        # Trim history to maximum length
        if len(user_histories[user_id]) > 2 * ai.MAX_HISTORY:
            user_histories[user_id] = user_histories[user_id][-2 * ai.MAX_HISTORY:]
        
        # Save to cache
        cache.set_cache(user_text, assistant_response)
        
        # Log token usage
        ai.log_usage(user_id, prompt_tokens, completion_tokens)
        
        # Send response
        await update.message.reply_text(assistant_response)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        
        # Check if it's a quota error (429)
        if "429" in str(e):
            await update.message.reply_text(
                "Сервис временно недоступен, попробуйте позже 💖"
            )
        else:
            await update.message.reply_text(
                "Извините, возникла ошибка при обработке вашего запроса. "
                "Пожалуйста, попробуйте еще раз позже."
            )

async def send_crisis_response(update: Update) -> None:
    """Send a calming response for crisis situations."""
    calming_message = (
        "💖 Я вижу, что вы сейчас переживаете сложный момент. "
        "Глубоко вдохните и помните - вы не одни.\n\n"
        "🎵 Вот успокаивающая музыка, которая может помочь: "
        f"{LOFI_LINK}\n\n"
        "📞 Если вам нужна немедленная поддержка, пожалуйста, позвоните по номерам: "
        f"{EMERGENCY_NUMBERS}\n\n"
        "Я здесь, чтобы выслушать вас. Томирис рядом — вместе мы справимся!"
    )
    await update.message.reply_text(calming_message)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    
    # Register callback query handler for the agreement button 
    # This is the fix for the "loading..." loop issue
    application.add_handler(CallbackQueryHandler(agree_callback, pattern=f"^{AGREE_CB}$"))
    
    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot using polling
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    logger.info("Bot started polling...")

if __name__ == "__main__":
    main()
