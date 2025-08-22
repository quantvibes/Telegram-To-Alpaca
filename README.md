# Telegram-To-Alpaca
Trades posted from Telegram to Alpaca

# === Configuration ===
TELEGRAM_TOKEN    = "" # Your telegram bot token - you can use BotFather
ALPACA_API_KEY    = "" 
ALPACA_SECRET_KEY = ""
ALPACA_BASE_URL   = "https://paper-api.alpaca.markets" # Use live URL for real trading
ALLOWED_CHANNELS  = []  # Your channel’s numeric ID, where you will type commands. You can use RawDataBot to get your channel ID

**Commands Sample -**
       BUY qty SYMBOL,
       SELL SYMBOL,
       SELL qty SYMBOL,
       SELL SYMBOL LIMIT price,
       SELL qty SYMBOL LIMIT price,
       PORTFOLIO
