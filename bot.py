from telethon import TelegramClient, events
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random, string, asyncio, threading, aiohttp, json, os
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- RENDER HEALTH CHECK ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_check():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_check, daemon=True).start()

# --- CONFIGURATION ---
# Integrated your specific MongoDB URI (Brackets removed from password)
MONGO_URI = "mongodb+srv://riot_adminn:A2723Dscyq3gYhFi@cluster0.agit2bo.mongodb.net/?appName=Cluster0"
ADMIN_ID = 5541778617
BOT_TOKEN = '8284884126:AAFYSgVRWYh9ClQ-p6okChEyGyLnQo_OQaE'
API_ID = 38807471
API_HASH = '9bbfb9efe1a47596cf7f1b20017f5dc6'

# Initialize MongoDB and Telegram Bot
client = AsyncIOMotorClient(MONGO_URI)
db = client.shop_checker_db
bot = TelegramClient('checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- SECURITY LOGIC ---
async def is_premium(user_id):
    if user_id == ADMIN_ID: return True
    user = await db.users.find_one({"user_id": str(user_id)})
    if user:
        expiry = datetime.strptime(user['expiry'], '%Y-%m-%d %H:%M:%S')
        return expiry > datetime.now()
    return False

# --- EMOJI HELPERS ---
PREMIUM_EMOJI_IDS = {
    "✅": "6023660820544623088", 
    "🔥": "5999340396432333728", 
    "💠": "5971837723676249096", 
    "🍄": "6023660820544623088",
    "🔑": "5974235702701853774"
}

def p_emoji(text):
    for emoji, doc_id in PREMIUM_EMOJI_IDS.items():
        text = text.replace(emoji, f'<tg-emoji emoji-id="{doc_id}">{emoji}</tg-emoji>')
    return text

# --- COMMANDS ---

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    welcome = (
        "<b>⚡💳 Welcome to Shopiiiii ! 💳⚡</b>\n"
        "<b>━━━━━━━━━━━━━━━━━</b>\n"
        "<b>⚡💠 𝐂𝐂 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
        "<blockquote>• /cc card|mm|yy|cvv - Single Check\n"
        "• /chk - Bulk Check (Reply to .txt)\n"
        "• /bin 123456 - Get BIN info</blockquote>\n"
        "<b>⚡💠 𝐀𝐜𝐜𝐞𝐬𝐬 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
        "<blockquote>• /redeem [KEY] - Activate subscription</blockquote>\n"
        "<b>⚡💠 𝐒𝐢𝐭𝐞 & 𝐏𝐫𝐨𝐱𝐲</b>\n"
        "<blockquote>• /addsite [url] | /site (Status)\n"
        "• /addproxy [proxy] | /proxy (Count)</blockquote>\n"
        "<b>⚡💠 𝐀𝐝𝐦𝐢𝐧 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
        "<blockquote>• /genkey [days] - Create access key\n"
        "• /setapi [url] - Update Checker API</blockquote>\n"
        "<b>━━━━━━━━━━━━━━━━━</b>\n"
        "<b>Made wt ♥️: <a href='tg://user?id=5541778617'>P.o.Riot 🍄</a></b>"
    )
    await event.reply(p_emoji(welcome), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/genkey\s+(\d+)'))
async def generate_key(event):
    if event.sender_id != ADMIN_ID: return
    days = int(event.pattern_match.group(1))
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    await db.keys.insert_one({"key": key, "days": days})
    await event.reply(p_emoji(f"🔑 **Key Generated & Saved to Cloud**\n`{key}` ({days} Days)\n**Made wt ♥️: P.o.Riot 🍄**"))

@bot.on(events.NewMessage(pattern=r'^/redeem\s+(\w+)'))
async def redeem_key(event):
    key_text = event.pattern_match.group(1)
    key_doc = await db.keys.find_one_and_delete({"key": key_text})
    if key_doc:
        days = key_doc['days']
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        await db.users.update_one(
            {"user_id": str(event.sender_id)},
            {"$set": {"expiry": expiry_date}},
            upsert=True
        )
        await event.reply(p_emoji(f"✅ **Success!** Subscription activated for {days} days.\n**Made wt ♥️: P.o.Riot 🍄**"))
    else:
        await event.reply(p_emoji("❌ **Invalid or Used Key.**"))

@bot.on(events.NewMessage(pattern=r'^/setapi\s+(.+)'))
async def set_api(event):
    if event.sender_id != ADMIN_ID: return
    new_url = event.pattern_match.group(1).strip()
    await db.config.update_one({"type": "settings"}, {"$set": {"api_url": new_url}}, upsert=True)
    await event.reply(p_emoji(f"✅ **API Updated in Cloud!**\n**Made wt ♥️: P.o.Riot 🍄**"))

@bot.on(events.NewMessage(pattern=r'^/addsite\s+'))
async def add_site(event):
    if not await is_premium(event.sender_id): return
    urls = event.message.text.replace('/addsite ', '').split()
    with open('sites.txt', 'a') as f:
        for url in urls: f.write(f"{url}\n")
    await event.reply(p_emoji("✅ Sites added by **P.o.Riot 🍄**"))

# --- STARTUP ---
print("✅ Bot is online with MONGODB - Made wt ♥️ by P.o.Riot 🍄")
bot.run_until_disconnected()

