#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple disk-based caching system for Tomyris bot.
Caches responses to frequent questions to minimize OpenAI API costs.
"""

import os
import json
import time
import hashlib
from pathlib import Path

# Cache settings
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "faq.json")
CACHE_TTL = 86400  # 24 hours (in seconds)

# Initialize cache folder
Path(CACHE_DIR).mkdir(exist_ok=True)

def _hash_text(text):
    """Create SHA-256 hash of the input text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def _load_cache():
    """Load the cache from disk."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {}
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is corrupted or doesn't exist, return an empty cache
        return {}

def _save_cache(cache_data):
    """Save the cache to disk."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

def get_cache(text):
    """
    Try to get a cached response for the given text.
    Returns None if not found or expired.
    """
    # Create a hash of the input text
    text_hash = _hash_text(text)
    
    # Load the cache
    cache = _load_cache()
    
    # Check if the hash exists in the cache
    if text_hash in cache:
        entry = cache[text_hash]
        current_time = time.time()
        
        # Check if the entry has expired
        if current_time - entry["ts"] <= CACHE_TTL:
            return entry["answer"]
        else:
            # Remove expired entry
            del cache[text_hash]
            _save_cache(cache)
    
    return None

def set_cache(text, answer):
    """Cache a response for the given text."""
    # Create a hash of the input text
    text_hash = _hash_text(text)
    
    # Load the cache
    cache = _load_cache()
    
    # Add or update the entry
    cache[text_hash] = {
        "answer": answer,
        "ts": time.time()
    }
    
    # Save the updated cache
    _save_cache(cache)

def clear_expired():
    """Clear expired entries from the cache."""
    cache = _load_cache()
    current_time = time.time()
    updated = False
    
    # Check each entry
    for text_hash in list(cache.keys()):
        if current_time - cache[text_hash]["ts"] > CACHE_TTL:
            del cache[text_hash]
            updated = True
    
    # Save if any entries were removed
    if updated:
        _save_cache(cache)

# Create cache file if it doesn't exist
if not os.path.exists(CACHE_FILE):
    _save_cache({})
