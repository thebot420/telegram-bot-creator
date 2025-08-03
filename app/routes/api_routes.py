from flask import Blueprint, request, jsonify, current_app
from .. import db
from ..models import User, Bot, Category, Product, Order
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
import asyncio
import os
import requests
import hmac
import hashlib
import json

api = Blueprint('api', __name__)

SERVER_URL = "https://telegram-bot-creator.onrender.com"
NOWPAYMENTS_API_KEY = os.environ.get('NOWPAYMENTS_API_KEY')
NOWPAYMENTS_IPN_SECRET_KEY = os.environ.get('NOWPAYMENTS_IPN_SECRET_KEY')

def run_async(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

async def setup_bot_webhook(bot_token):
    # ... (Full function code)
    pass

async def handle_telegram_update(bot_token, update_data):
    # ... (Full function code)
    pass

# --- ALL API ROUTES GO HERE ---
# (e.g., @api.route('/api/login'), etc.)
