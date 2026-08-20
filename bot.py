import os
import threading
import requests
import uvicorn
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Configuration
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_URL = os.environ.get("API_URL", "https://moviebox-api-98dn.onrender.com").strip().rstrip("/")

# FastAPI server to keep Render web service alive
app_web = FastAPI()

@app_web.get("/")
async def root():
    return {"status": "ok"}

def run_server():
    uvicorn.run(app_web, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Pyrogram Bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 **नमस्ते!** किसी भी मूवी या वेब-सीरीज़ का नाम लिखकर भेजें।")

@app.on_message(filters.text & ~filters.command("start"))
async def search_movie(client, message):
    query = message.text.strip()
    status_msg = await message.reply_text("🔍 **सर्च कर रहा हूँ...**")
    
    try:
        url = f"{API_URL}/search?q={query}"
        response = requests.get(url, timeout=20)
        data = response.json()
        
        # API items extraction
        items = data.get("items", [])
        
        if not items:
            await status_msg.edit_text("❌ कोई मूवी नहीं मिली। कृपया नाम की स्पेलिंग चेक करें।")
            return
        
        # Movie Buttons (Top 6 results)
        buttons = []
        for item in items[:6]:
            title = item.get("name", "Unknown Movie")
            subject_id = item.get("subject_id", "")
            buttons.append([InlineKeyboardButton(text=f"🎬 {title}", callback_data=f"sub_{subject_id}")])
            
        await status_msg.edit_text(
            f"🍿 **'{query}'** के लिए रिजल्ट्स मिले ({len(items)}):",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        await status_msg.edit_text(f"⚠️ एरर: {e}")

# Handle Button Click
@app.on_callback_query()
async def on_button_click(client, callback_query: CallbackQuery):
    data = callback_query.data
    
    if data.startswith("sub_"):
        subject_id = data.split("_")[1]
        await callback_query.answer("मूवी लोड हो रही है...")
        
        # You can call movie details endpoint if available or show direct status
        await callback_query.message.reply_text(
            f"✅ **Movie Selected!**\n\n🆔 **Subject ID:** `{subject_id}`\n\n🔗 [Watch on MovieBox](https://moviebox.ph)"
        )

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app.run()
