import os
import threading
import requests
import uvicorn
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Environment Variables
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_URL = os.environ.get("API_URL", "https://moviebox-api-98dn.onrender.com")

# FastAPI Server for Render Free Tier
app_web = FastAPI()

@app_web.get("/")
async def root():
    return {"message": "Bot is running"}

def run_server():
    uvicorn.run(app_web, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Telegram Bot Setup
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("नमस्ते! किसी भी मूवी का नाम लिखकर भेजें।")

@app.on_message(filters.text & ~filters.command("start"))
async def search(client, message):
    query = message.text.strip()
    msg = await message.reply("🔍 सर्च कर रहा हूँ...")
    
    try:
        r = requests.get(f"{API_URL}/search?q={query}", timeout=20)
        data = r.json()
        
        # API Response format handle karna (list ya dict)
        if isinstance(data, dict):
            movies = data.get("results") or data.get("data") or data.get("movies") or []
        elif isinstance(data, list):
            movies = data
        else:
            movies = []
            
        if not movies:
            await msg.edit("❌ कोई मूवी नहीं मिली। नाम की स्पेलिंग चेक करें।")
            return
        
        # Buttons generate karna
        buttons = []
        for m in movies[:6]:
            if isinstance(m, dict):
                title = m.get("title") or m.get("name") or "Watch Movie"
                slug = m.get("slug") or m.get("id") or m.get("url") or ""
                # Telegram callback data limit (max 64 bytes)
                cb_data = f"m_{str(slug)[:50]}"
                buttons.append([InlineKeyboardButton(text=title, callback_data=cb_data)])
        
        if buttons:
            await msg.edit(f"🎬 **'{query}'** के लिए नतीजे:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await msg.edit("❌ रिज़ल्ट पार्स नहीं हो सका।")
            
    except Exception as e:
        await msg.edit(f"⚠️ एरर: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app.run()
    
