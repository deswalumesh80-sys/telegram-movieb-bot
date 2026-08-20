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

# Temporary storage for pagination
USER_DATA = {}

app_web = FastAPI()

@app_web.get("/")
async def root():
    return {"status": "ok"}

def run_server():
    uvicorn.run(app_web, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 1. Start Interface (Video jaisa banner style)
@app.on_message(filters.command("start"))
async def start(client, message):
    text = (
        "🥷 **I am Movie Finder Bot**\n"
        "📦 **Unlimited files**\n"
        "⚡ **Get instant file / links**\n"
        "💯 **100% Free, always**\n"
        "🏷️ **By Your Community**\n\n"
        "🔍 *Neeche movie ka naam type karein aur search karein.*"
    )
    buttons = [
        [InlineKeyboardButton("🔍 Quick Help", callback_data="help"), InlineKeyboardButton("👮 Admin Support", url="https://t.me/")],
        [InlineKeyboardButton("💡 Movie Ideas", callback_data="ideas"), InlineKeyboardButton("💳 Upgrade Plan", callback_data="plan")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# 2. Movie Search with Pagination & UI
@app.on_message(filters.text & ~filters.command("start"))
async def search_movie(client, message):
    query = message.text.strip()
    status_msg = await message.reply_text("🔍 **Searching...**")
    
    try:
        url = f"{API_URL}/search?q={query}"
        response = requests.get(url, timeout=20)
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            await status_msg.edit_text("❌ **Koi movie nahi mili. Spelling check karein.**")
            return
        
        USER_DATA[message.from_user.id] = {"items": items, "query": query, "page": 0}
        await send_page(client, message.chat.id, status_msg.id, message.from_user.id, edit=True)
        
    except Exception as e:
        await status_msg.edit_text(f"⚠️ Error: {e}")

async def send_page(client, chat_id, message_id, user_id, edit=False):
    user_info = USER_DATA.get(user_id)
    if not user_info:
        return
    
    items = user_info["items"]
    page = user_info["page"]
    query = user_info["query"]
    
    per_page = 7
    total_pages = (len(items) + per_page - 1) // per_page
    start_idx = page * per_page
    end_idx = start_idx + per_page
    current_items = items[start_idx:end_idx]
    
    buttons = []
    
    # Files list buttons (Video style UI)
    for idx, item in enumerate(current_items):
        title = item.get("name", "Watch Movie")
        subject_id = item.get("subject_id", "")
        buttons.append([InlineKeyboardButton(f"📁 [{idx+1+start_idx}] {title[:38]} ↗️", callback_data=f"info_{subject_id}")])
    
    # Navigation buttons
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data="prev_page"))
    nav.append(InlineKeyboardButton(f"📑 {page+1}/{total_pages} Pages", callback_data="pages_info"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data="next_page"))
    
    buttons.append(nav)
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_btn")])
    
    text = (
        f"🏷️ **Requested By :** [{client.me.first_name}](tg://user?id={user_id})\n"
        f"🎬 **Results for :** `{query}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    if edit:
        await client.edit_message_text(chat_id, message_id, text, reply_markup=InlineKeyboardMarkup(buttons))

# 3. Callbacks (Next/Prev & Details)
@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    if data == "close_btn":
        await query.message.delete()
        return
        
    elif data == "next_page":
        if user_id in USER_DATA:
            USER_DATA[user_id]["page"] += 1
            await send_page(client, query.message.chat.id, query.message.id, user_id, edit=True)
            
    elif data == "prev_page":
        if user_id in USER_DATA:
            USER_DATA[user_id]["page"] -= 1
            await send_page(client, query.message.chat.id, query.message.id, user_id, edit=True)
            
    elif data.startswith("info_"):
        subject_id = data.split("_")[1]
        await query.answer("Fetching Movie Details...")
        
        # Details layout (Video jaisa Download/Stream Interface)
        detail_text = (
            f"🎬 **Movie Details Ready**\n"
            f"🆔 **Subject ID:** `{subject_id}`\n\n"
            f"⚡ **Powered By :** MovieBox API\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        detail_buttons = [
            [
                InlineKeyboardButton("▶️ Watch / Stream", url=f"https://moviebox-api-98dn.onrender.com/detail?subject_id={subject_id}"),
                InlineKeyboardButton("📥 Download", url=f"https://moviebox.ph")
            ],
            [InlineKeyboardButton("🔙 Back to List", callback_data="back_to_list")]
        ]
        await query.message.reply_text(detail_text, reply_markup=InlineKeyboardMarkup(detail_buttons))
        
    elif data == "back_to_list":
        await send_page(client, query.message.chat.id, query.message.id, user_id, edit=True)
        
    elif data in ["help", "ideas", "plan"]:
        await query.answer("Ye feature setup ho raha hai!", show_alert=True)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    app.run()
