#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
OpenAI integration wrapper for Tomyris bot.
Handles message formatting, token counting and API calls.
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path

import tiktoken
from openai import AsyncOpenAI, RateLimitError
from pythonjsonlogger import jsonlogger

# Load API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Constants for cost optimization
MAX_HISTORY = 3  # Number of conversation exchanges to keep
MAX_TOKENS = 500  # Maximum tokens in completion
TEMPERATURE = 0.7  # Temperature parameter for generation
MODEL_NAME = "gpt-4o-mini"  # Using gpt-4o-mini for cost efficiency

# Configure JSON logger for token usage
log_handler = None
logger = None

def setup_logging():
    """Set up rotating JSON logger for token usage."""
    global log_handler, logger
    
    import logging
    from logging.handlers import TimedRotatingFileHandler
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger("usage_logger")
    logger.setLevel(logging.INFO)
    
    # Create a handler that rotates daily
    log_handler = TimedRotatingFileHandler(
        "logs/usage.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    
    # Use JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(user_id)s %(prompt_tokens)s %(completion_tokens)s %(cost_usd)s'
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

# Initialize the OpenAI client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Initialize the tokenizer for GPT-4
encoding = tiktoken.encoding_for_model("gpt-4")

def count_tokens(text):
    """Count the number of tokens in a text."""
    return len(encoding.encode(text))

def build_messages(history, user_msg):
    """Build the messages array for OpenAI API."""
    # Load system prompt
    try:
        with open("prompt/system.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        # If the file doesn't exist, use a minimal system prompt
        system_prompt = "You are Tomiris, an AI assistant supporting women in Kazakhstan."
    
    # Start with system message
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (limited to MAX_HISTORY)
    if history:
        # Only include the most recent exchanges
        recent_history = history[-2*MAX_HISTORY:] if len(history) > 2*MAX_HISTORY else history
        messages.extend(recent_history)
    
    # Add current user message
    messages.append({"role": "user", "content": user_msg})
    
    return messages

async def ask_openai(history, user_msg):
    """Call OpenAI API with the given history and user message."""
    messages = build_messages(history, user_msg)
    
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        
        # Extract the assistant's message
        assistant_msg = response.choices[0].message.content
        
        # Extract token counts
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        return assistant_msg, prompt_tokens, completion_tokens
        
    except RateLimitError:
        raise Exception("OpenAI API rate limit exceeded (429)")
    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")

def log_usage(user_id, prompt_tokens, completion_tokens):
    """Log token usage and cost to JSON log file."""
    global logger
    
    # Set up logging if not already done
    if logger is None:
        setup_logging()
    
    # Calculate cost in USD (according to GPT-4o-mini pricing)
    cost_usd = (prompt_tokens * 0.15 + completion_tokens * 0.60) / 1_000_000
    
    # Log the usage
    logger.info(
        "", 
        extra={
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": cost_usd
        }
    )

# Ensure the prompt directory exists
Path("prompt").mkdir(exist_ok=True)
