import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from fastapi import FastAPI
import uvicorn
import threading

# API Details
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_URL = "https://moviebox-api-98dn.onrender.com"

# FastAPI Server (Render को खुश रखने के लिए)
app_web = FastAPI()

@app_web.get("/")
async def root():
    return {"message": "Bot is running"}

def run_server():
    uvicorn.run(app_web, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Telegram Bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("नमस्ते! मूवी का नाम लिखें।")

@app.on_message(filters.text & ~filters.command("start"))
async def search(client, message):
    query = message.text
    msg = await message.reply("🔍 सर्च कर रहा हूँ...")
    try:
        r = requests.get(f"{API_URL}/search?q={query}")
        movies = r.json()
        if not movies:
            await msg.edit("❌ मूवी नहीं मिली।")
            return
        buttons = []
        for m in movies[:5]:
            buttons.append([InlineKeyboardButton(m['title'], callback_data=f"link_{m['slug']}")])
        await msg.edit(f"🎬 '{query}' के नतीजे:", reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await msg.edit(f"⚠️ एरर: {e}")

# सर्वर और बोट को साथ चलाना
if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    app.run()
    
