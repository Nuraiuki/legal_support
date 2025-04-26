# Tomyris Telegram Bot

An AI-powered Telegram bot that offers legal and emotional support for women in Kazakhstan.

## Features

- 💬 AI-powered responses based on OpenAI's GPT model
- ⚖️ Legal information tailored to Kazakhstan laws
- 🧘‍♀️ Emotional support with crisis resources
- 💰 Cost-saving caching mechanism for common questions
- 📊 Usage tracking and token counting

## Setup and Usage

- **Replit run:** add secrets → click **Run** → bot starts polling.  
- **Local dev:**  
  ```bash
  pip install -r requirements.txt
  export OPENAI_API_KEY=... TELEGRAM_BOT_TOKEN=... ADMIN_CHAT_ID=...
  python bot.py
  ```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `ADMIN_CHAT_ID`: Telegram chat ID for admin notifications

## Project Structure

- `bot.py`: Main entry point, handles Telegram interactions
- `ai.py`: OpenAI integration wrapper
- `cache.py`: Caching system for reducing API costs
- `prompt/system.txt`: System prompt for the Tomyris AI persona
- `data/users.csv`: First-time users log
- `logs/usage.log`: Daily rotating JSON logs for token usage and costs

## Cost Optimization

The bot implements several cost-saving measures:
- 24-hour response caching
- Limited conversation history (max 3 exchanges)
- Token limits for AI responses
- Daily usage logging for monitoring
