import time
import random
import logging
import os
from datetime import datetime
from tradingview_ta import TA_Handler, Interval
import requests

# ===== CONFIGURATION =====
THRESHOLD_PERCENT = 0.5
DELAY_BETWEEN_STOCKS = 20
BATCH_SIZE = 5
BATCH_COOLDOWN = 90
MAX_RETRIES = 2

# ===== TELEGRAM CONFIGURATION =====
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Set in GitHub Secrets
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')     # Set in GitHub Secrets

def send_telegram_signal(symbol, price, ema200, threshold_percent):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        message = (
            f"🚨 <b>EMA200 Signal</b> �\n\n"
            f"<b>{symbol}</b>\n"
            f"Price: ₹{price:.2f}\n"
            f"EMA200: ₹{ema200:.2f}\n"
            f"Within ±{threshold_percent}% range\n"
            f"Diff: {(price-ema200)/ema200*100:.2f}%"
        )
        params = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        requests.post(url, params=params)
    except Exception as e:
        print(f"⚠️ Failed to send Telegram signal: {str(e)}")

# ===== STOCK DATA =====
STOCK_DICT = {
    "HDFCBANK": ("NSE", "Banking"),
    "INFY": ("NSE", "IT"),
    "TCS": ("NSE", "IT"),
    "ONGC": ("NSE", "Oil & Gas"),
    "GOLDBEES": ("NSE", "ETF"),
    "ANGELONE": ("NSE", "Brokerage"),
    "SUNPHARMA": ("BSE", "Pharma"),
    "TECHM": ("NSE", "IT"),
    "HINDUNILVR": ("BSE", "FMCG"),
    "BSE": ("NSE", "Exchange"),
    "SILVERBEES": ("NSE", "ETF"),
    "BAJAJ_AUTO": ("NSE", "Auto"),
    "WIPRO": ("BSE", "IT"),
    "BHARTIARTL": ("BSE", "Telecom"),
    "TATAMOTORS": ("NSE", "Auto"),
    "APOLLOTYRE": ("NSE", "Auto"),
    "JSWSTEEL": ("NSE", "Steel"),
    "HINDCOPPER": ("BSE", "Metals"),
    "HAL": ("NSE", "Defense"),
    "TATAPOWER": ("NSE", "Power"),
    "LT": ("NSE", "Infra"),
    "LTF": ("NSE", "Finance"),
    "MAZDOCK": ("NSE", "Shipbuilding"),
    "COCHINSHIP": ("BSE", "Shipping"),
    "MOTHERSON": ("BSE", "Auto Parts"),
    "BAJAJFINSV": ("NSE", "Financial"),
    "CAMS": ("BSE", "FinTech"),
    "TRENT": ("BSE", "Retail"),
    "GPPL": ("NSE", "Port"),
    "NCC": ("BSE", "Construction"),
    "RECLTD": ("BSE", "Power Finance"),
    "CDSL": ("NSE", "FinTech"),
    "MCX": ("NSE", "Commodities")
}

def fetch_stock_data(symbol, exchange):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            handler = TA_Handler(
                symbol=symbol,
                exchange=exchange,
                screener="india",
                interval=Interval.INTERVAL_1_DAY,
                timeout=20
            )
            analysis = handler.get_analysis()
            return analysis.indicators["close"], analysis.indicators["EMA200"]
        except Exception as e:
            wait = (DELAY_BETWEEN_STOCKS * 2) + random.uniform(10, 20)
            print(f"⚠️ Retry {attempt} for {symbol} in {wait:.1f}s...")
            time.sleep(wait)
    return None, None

def is_market_hours():
    return True  # For testing only

def run_scanner():
    if not is_market_hours():
        print("❌ Outside market hours - exiting")
        return

    print(f"\n🌀 Starting scan ({len(STOCK_DICT)} stocks)")
    start_time = time.time()

    try:
        for i, (symbol, (exchange, sector)) in enumerate(STOCK_DICT.items(), 1):
            if i % BATCH_SIZE == 0:
                print(f"🛑 Cooling down for {BATCH_COOLDOWN}s...")
                time.sleep(BATCH_COOLDOWN)

            price, ema200 = fetch_stock_data(symbol, exchange)

            if price is None or ema200 is None:
                print(f"❌ Failed: {symbol}.{exchange}")
                continue

            threshold = THRESHOLD_PERCENT / 100
            if ema200 * (1 - threshold) <= price <= ema200 * (1 + threshold):
                print(f"🚨 {symbol}: ₹{price:.2f} | EMA200: ₹{ema200:.2f} | WITHIN RANGE")
                send_telegram_signal(symbol, price, ema200, THRESHOLD_PERCENT)
            else:
                print(f"✅ {symbol}: ₹{price:.2f} | EMA200: ₹{ema200:.2f} | Diff: {(price-ema200)/ema200*100:.2f}%")

            time.sleep(DELAY_BETWEEN_STOCKS + random.uniform(0, 15))

    except Exception as e:
        print(f"💥 Critical error: {str(e)}")
        raise

    print(f"\n⏱️ Scan completed in {(time.time()-start_time)/60:.1f} minutes")

if __name__ == "__main__":
    print("=== EMA200 SCANNER ===")
    print(f"Config: {DELAY_BETWEEN_STOCKS}-35s per stock | {BATCH_COOLDOWN}s every {BATCH_SIZE} stocks")
    run_scanner()
