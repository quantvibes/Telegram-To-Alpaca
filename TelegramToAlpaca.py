import logging
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)
from alpaca_trade_api.rest import REST

# === Configuration ===
TELEGRAM_TOKEN    = "" # Your telegram bot token - you can use BotFather
ALPACA_API_KEY    = "" 
ALPACA_SECRET_KEY = ""
ALPACA_BASE_URL   = "https://paper-api.alpaca.markets" # Use live URL for real trading
ALLOWED_CHANNELS  = []  # Your channel’s numeric ID, where you will type commands. You can use RawDataBot to get your channel ID

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Alpaca client ===
alpaca = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)

# === Command Handlers ===

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, args):
    chat_id = update.effective_chat.id
    qty, symbol = int(args[0]), args[1].upper()
    order = alpaca.submit_order(
        symbol=symbol, qty=qty,
        side="buy", type="market", time_in_force="gtc"
    )
    await context.bot.send_message(
        chat_id,
        f"✅ Bought {qty} shares of {symbol}. Order ID: {order.id}"
    )

async def handle_sell_all(update: Update, context: ContextTypes.DEFAULT_TYPE, args):
    chat_id = update.effective_chat.id
    symbol = args[0].upper()
    positions = alpaca.list_positions()
    qty = next((int(p.qty) for p in positions if p.symbol == symbol), 0)
    if qty:
        order = alpaca.submit_order(
            symbol=symbol, qty=qty,
            side="sell", type="market", time_in_force="gtc"
        )
        await context.bot.send_message(
            chat_id,
            f"✅ Sold all ({qty}) shares of {symbol}. Order ID: {order.id}"
        )
    else:
        await context.bot.send_message(chat_id, f"⚠️ No position in {symbol}.")

async def handle_sell_qty(update: Update, context: ContextTypes.DEFAULT_TYPE, args):
    chat_id = update.effective_chat.id
    qty, symbol = int(args[0]), args[1].upper()
    order = alpaca.submit_order(
        symbol=symbol, qty=qty,
        side="sell", type="market", time_in_force="gtc"
    )
    await context.bot.send_message(
        chat_id,
        f"✅ Sold {qty} shares of {symbol}. Order ID: {order.id}"
    )

async def handle_limit_sell_all(update: Update, context: ContextTypes.DEFAULT_TYPE, args):
    chat_id = update.effective_chat.id
    symbol, price = args[0].upper(), float(args[1])
    positions = alpaca.list_positions()
    qty = next((int(p.qty) for p in positions if p.symbol == symbol), 0)
    if qty:
        order = alpaca.submit_order(
            symbol=symbol, qty=qty,
            side="sell", type="limit",
            time_in_force="gtc", limit_price=price
        )
        await context.bot.send_message(
            chat_id,
            f"✅ Placed GTC LIMIT sell of all ({qty}) {symbol} @ ${price:.2f}. ID {order.id}"
        )
    else:
        await context.bot.send_message(chat_id, f"⚠️ No position in {symbol}.")

async def handle_limit_sell_qty(update: Update, context: ContextTypes.DEFAULT_TYPE, args):
    chat_id = update.effective_chat.id
    qty, symbol, price = int(args[0]), args[1].upper(), float(args[2])
    order = alpaca.submit_order(
        symbol=symbol, qty=qty,
        side="sell", type="limit",
        time_in_force="gtc", limit_price=price
    )
    await context.bot.send_message(
        chat_id,
        f"✅ Placed GTC LIMIT sell of {qty} {symbol} @ ${price:.2f}. ID {order.id}"
    )

async def handle_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE, args):
    chat_id = update.effective_chat.id
    positions = alpaca.list_positions()
    if not positions:
        return await context.bot.send_message(chat_id, "📭 No open positions.")
    lines = ["📊 Your portfolio:"]
    for p in positions:
        mv = float(p.market_value)
        lines.append(f"{p.symbol}: {p.qty} shares, Value ${mv:.2f}")
    await context.bot.send_message(chat_id, "\n".join(lines))

# === Regex → handler mapping ===

COMMAND_PATTERNS = [
    (re.compile(r"^buy\s+(\d+)\s+([A-Za-z]+)$", re.IGNORECASE), handle_buy),
    (re.compile(r"^sell\s+([A-Za-z]+)$", re.IGNORECASE), handle_sell_all),
    (re.compile(r"^sell\s+(\d+)\s+([A-Za-z]+)$", re.IGNORECASE), handle_sell_qty),
    (re.compile(r"^sell\s+([A-Za-z]+)\s+limit\s+(\d+(\.\d+)?)$", re.IGNORECASE), handle_limit_sell_all),
    (re.compile(r"^sell\s+(\d+)\s+([A-Za-z]+)\s+limit\s+(\d+(\.\d+)?)$", re.IGNORECASE), handle_limit_sell_qty),
    (re.compile(r"^portfolio$", re.IGNORECASE), handle_portfolio),
]

# === Main update handler ===

async def handle_channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text:
        return

    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHANNELS:
        return

    text = msg.text.strip()
    for pattern, func in COMMAND_PATTERNS:
        match = pattern.match(text)
        if match:
            try:
                await func(update, context, match.groups())
            except Exception as e:
                logger.exception("Command error")
                await context.bot.send_message(chat_id, f"⚠️ Error: {e}")
            return

    # Fallback for unknown commands
    await context.bot.send_message(
        chat_id,
        "❓ Unknown command.\nSupported:\n"
        "• BUY <qty> <SYMBOL>\n"
        "• SELL <SYMBOL>\n"
        "• SELL <qty> <SYMBOL>\n"
        "• SELL <SYMBOL> LIMIT <price>\n"
        "• SELL <qty> <SYMBOL> LIMIT <price>\n"
        "• PORTFOLIO"
    )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(
        MessageHandler(filters.Chat(ALLOWED_CHANNELS) & filters.TEXT,
                       handle_channel_command)
    )

    print("🚀 Bot is up and running – polling for messages…")
    logger.info("Bot is up and running – polling for messages…")
    app.run_polling()

if __name__ == "__main__":
    main()
