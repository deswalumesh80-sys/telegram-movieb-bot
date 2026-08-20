import os
import threading
import uvicorn
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

# Configuration
API_ID = int(os.environ.get("API_ID", "38398715"))
API_HASH = os.environ.get("API_HASH", "9d70e41f8c67908ed547e31c2cfe9c38")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8588875170:AAE-2TF39moR_LksMVaYbxG5JLHB-pASoQM")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8471574210"))
DATABASE_URI = os.environ.get("DATABASE_URI", "mongodb+srv://Udeswal82_db_user:MovieBot12345@cluster0.bwrhkn0.mongodb.net/?retryWrites=true&w=majority")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "Cluster0")
STORAGE_CHANNEL = int(os.environ.get("STORAGE_CHANNEL", "-1002361665487"))
UPI_ID = os.environ.get("UPI_ID", "example@upi")

# MongoDB
mongo = AsyncIOMotorClient(DATABASE_URI)
db = mongo[DATABASE_NAME]
files_col = db["files"]

# Render Keep-Alive
web_app = FastAPI()

@web_app.get("/")
def home():
    return {"status": "running"}

def run_web():
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(web_app, host="0.0.0.0", port=port)

app = Client("toji_stream_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
USER_PAGES = {}

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    # Direct File Fetch Handler
    if len(message.command) > 1:
        doc_id = message.command[1]
        doc = await files_col.find_one({"_id": doc_id})
        if doc:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=doc["chat_id"],
                message_id=doc["msg_id"],
                caption=f"🎬 **{doc['file_name']}**\n\n⚡ **Powered By :** Filmy Men"
            )
            return

    text = (
        "🥷 **I am #Toji v2.1**\n"
        "🍿 **Unlimited files & series**\n"
        "⚡ **Direct In-App Telegram Player**\n"
        "💯 **100% Free, always**\n"
        "🏷️ **By The Filmy Men**\n\n"
        "🔍 *Kisi bhi movie ka naam likh kar bhejein:*"
    )
    buttons = [
        [InlineKeyboardButton("🔍 Quick Help", callback_data="help"), InlineKeyboardButton("👮 Admin Support", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("💡 Movie Ideas", callback_data="ideas"), InlineKeyboardButton("💳 Upgrade Plan", callback_data="plan_menu")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Channel Auto Indexer (जब चैनल में वीडियो डाली जाए)
@app.on_message(filters.channel & (filters.document | filters.video))
async def auto_index(client, message):
    media = message.document or message.video
    if not media:
        return
    f_name = media.file_name or message.caption or "Movie File"
    size = round(media.file_size / (1024 * 1024), 1)
    size_str = f"{round(size/1024, 2)} GB" if size >= 1024 else f"{size} MB"
    
    doc = {
        "_id": f"{message.chat.id}_{message.id}",
        "file_name": f_name,
        "file_size": size_str,
        "chat_id": message.chat.id,
        "msg_id": message.id
    }
    await files_col.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)

# Search Handler
@app.on_message(filters.text & ~filters.command(["start", "plan"]))
async def movie_search(client, message):
    query = message.text.strip()
    status_msg = await message.reply_text(f"🔎 **Searching database for:** `{query}`...")
    
    try:
        cursor = files_col.find({"file_name": {"$regex": query, "$options": "i"}})
        results = await cursor.to_list(length=30)
    except Exception:
        results = []

    if not results:
        await status_msg.edit_text("❌ **Ye movie channel me nahi mili. Channel me upload/forward karein.**")
        return

    USER_PAGES[message.from_user.id] = {"query": query, "results": results, "page": 0}
    await status_msg.delete()
    await display_page(client, message.chat.id, message.id, message.from_user.id, edit=False)

async def display_page(client, chat_id, reply_id, user_id, edit=False, msg_id=None):
    data = USER_PAGES.get(user_id)
    if not data:
        return
    results = data["results"]
    page = data["page"]
    per_page = 6
    total_pages = (len(results) + per_page - 1) // per_page
    start = page * per_page
    current = results[start:start+per_page]

    btn = []
    for item in current:
        btn_text = f"📁 {item['file_size']} | {item['file_name']}"[:42] + " ↗️"
        btn.append([InlineKeyboardButton(btn_text, callback_data=f"send_{item['_id']}")])

    nav = []
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"📑 Pages {page+1}/{total_pages}", callback_data="pages"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("Next ⏩", callback_data="next_p"))
        elif page > 0:
            nav.append(InlineKeyboardButton("⏪ Prev", callback_data="prev_p"))
        btn.append(nav)

    cap = f"⛩️ **Requested By :** [{client.me.first_name}](tg://user?id={user_id})\n━━━━━━━━━━━━━━━━━━━━━━"
    if edit and msg_id:
        await client.edit_message_text(chat_id, msg_id, cap, reply_markup=InlineKeyboardMarkup(btn))
    else:
        await client.send_message(chat_id, cap, reply_to_message_id=reply_id, reply_markup=InlineKeyboardMarkup(btn))

@app.on_callback_query()
async def callbacks(client, query: CallbackQuery):
    u_id = query.from_user.id
    d = query.data

    if d == "close_btn":
        await query.message.delete()
    elif d == "next_p" and u_id in USER_PAGES:
        USER_PAGES[u_id]["page"] += 1
        await display_page(client, query.message.chat.id, None, u_id, edit=True, msg_id=query.message.id)
    elif d == "prev_p" and u_id in USER_PAGES:
        USER_PAGES[u_id]["page"] -= 1
        await display_page(client, query.message.chat.id, None, u_id, edit=True, msg_id=query.message.id)
    elif d.startswith("send_"):
        doc_id = d.replace("send_", "")
        doc = await files_col.find_one({"_id": doc_id})
        if doc:
            await query.answer("Sending Video File...", show_alert=False)
            await client.copy_message(
                chat_id=query.message.chat.id,
                from_chat_id=doc["chat_id"],
                message_id=doc["msg_id"],
                caption=f"🎬 **{doc['file_name']}**\n⚡ **Powered By :** Filmy Men"
            )
    elif d == "plan_menu":
        plan_text = "🌸 **Premium Plans** 🌸\n\n🏷️ **Plan 1 : 50₹ - 1 Month**\n🏷️ **Plan 2 : 90₹ - 2 Month**"
        btns = [
            [InlineKeyboardButton("1 Month", callback_data="pay_50"), InlineKeyboardButton("2 Month", callback_data="pay_90")],
            [InlineKeyboardButton("← Back", callback_data="close_btn")]
        ]
        await query.message.reply_text(plan_text, reply_markup=InlineKeyboardMarkup(btns))
    elif d.startswith("pay_"):
        amt = d.split("_")[1]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26pn=MovieBot%26am={amt}%26cu=INR"
        p_btns = [
            [InlineKeyboardButton("📤 UPLOAD SCREENSHOT", url=f"tg://user?id={ADMIN_ID}")],
            [InlineKeyboardButton("❌ CANCEL", callback_data="close_btn")]
        ]
        await query.message.reply_photo(photo=qr_url, caption=f"⚡ **{amt}₹ Pay karein**", reply_markup=InlineKeyboardMarkup(p_btns))
    elif d in ["help", "ideas", "pages"]:
        await query.answer("Working!", show_alert=False)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app.run()
    
