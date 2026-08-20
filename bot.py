import os
import threading
import uvicorn
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
DATABASE_URI = os.environ.get("DATABASE_URI", "")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "Cluster0")
STORAGE_CHANNEL = int(os.environ.get("STORAGE_CHANNEL", "0"))
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
UPI_ID = os.environ.get("UPI_ID", "example@upi")

mongo = AsyncIOMotorClient(DATABASE_URI)
db = mongo[DATABASE_NAME]
files_col = db["files"]

web_app = FastAPI()

@web_app.get("/")
def home():
    return {"status": "running"}

def run_web():
    uvicorn.run(web_app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

app = Client("toji_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
USER_PAGES = {}

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    if len(message.command) > 1:
        file_id = message.command[1]
        doc = await files_col.find_one({"_id": file_id})
        if doc:
            await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=doc.get("chat_id", STORAGE_CHANNEL),
                message_id=doc["msg_id"],
                caption=f"🎬 **{doc['file_name']}**\n\n⛩️ **Powered By :** Filmy Men",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Download | Stream", url="https://t.me/"), InlineKeyboardButton("Scan Audio", callback_data="scan_aud")],
                    [InlineKeyboardButton("close", callback_data="close_btn")]
                ])
            )
            return

    text = "🥷 **I am #Toji v2.1**\n🍿 **Unlimited files**\n⚡ **Get instant file**\n💯 **100% Free, always**\n🏷️ **By The Filmy Men**\n\n🔍 *Kisi bhi movie ka naam likh kar bhejein.*"
    buttons = [
        [InlineKeyboardButton("🔍 Quick Help", callback_data="help"), InlineKeyboardButton("👮 Admin Support", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("💡 Movie Ideas", callback_data="ideas"), InlineKeyboardButton("💳 Upgrade Plan", callback_data="plan_menu")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.channel & (filters.document | filters.video))
async def auto_index(client, message):
    media = message.document or message.video
    if not media:
        return
    file_name = media.file_name or message.caption or "Unknown Video"
    file_size = round(media.file_size / (1024 * 1024 * 1024), 2)
    size_str = f"{file_size} GB" if file_size >= 1 else f"{round(media.file_size / (1024 * 1024), 2)} MB"
    doc = {
        "_id": f"{message.chat.id}_{message.id}",
        "file_name": file_name,
        "file_size": size_str,
        "chat_id": message.chat.id,
        "msg_id": message.id
    }
    await files_col.update_one({"_id": doc["_id"]}, {"$set": doc}, upsert=True)

@app.on_message(filters.text & filters.private & ~filters.command(["start", "plan"]))
async def search_handler(client, message):
    query = message.text.strip()
    cursor = files_col.find({"file_name": {"$regex": query, "$options": "i"}})
    results = await cursor.to_list(length=100)
    if not results:
        await message.reply_text("❌ **Koi movie nahi mili. Spelling check karein.**")
        return
    USER_PAGES[message.from_user.id] = {"query": query, "results": results, "page": 0}
    await display_page(client, message.chat.id, message.id, message.from_user.id, edit=False)

async def display_page(client, chat_id, reply_id, user_id, edit=False, msg_id=None):
    data = USER_PAGES.get(user_id)
    if not data:
        return
    results = data["results"]
    page = data["page"]
    per_page = 8
    total_pages = (len(results) + per_page - 1) // per_page
    start = page * per_page
    current = results[start:start+per_page]
    btn = [[InlineKeyboardButton("📩 Get All Files 📩", callback_data="get_all")]]
    for item in current:
        title = f"📗 {item['file_size']} | {item['file_name']}"[:45] + " ↗️"
        btn.append([InlineKeyboardButton(title, url=f"https://t.me/{client.me.username}?start={item['_id']}")])
    nav = []
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"📑 Total {total_pages} Pages", callback_data="pages"))
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
    elif d == "plan_menu":
        plan_text = "🌸 **Premium Users Benefits** 🌸\n\n🚫 No Ads\n⚡ Get Instant Movies\n🗂️ Scan Language / Subs\n🌐 Browser Download & Streaming\n\n🎟️ **Premium Plans And Pricing** 🌸\n\n🏷️ **Plan 1 : 50₹ - 1 Month**\n🏷️ **Plan 2 : 90₹ - 2 Month**\n🏷️ **Plan 3 : 140₹ - 3 Month**\n🏷️ **Plan 4 : 190₹ - 4 Month**\n\n📌 *Click button to select plan:*"
        btns = [
            [InlineKeyboardButton("1 Month", callback_data="pay_50"), InlineKeyboardButton("2 Month", callback_data="pay_90")],
            [InlineKeyboardButton("3 Month", callback_data="pay_140"), InlineKeyboardButton("4 Month", callback_data="pay_190")],
            [InlineKeyboardButton("← Back", callback_data="close_btn")]
        ]
        await query.message.reply_text(plan_text, reply_markup=InlineKeyboardMarkup(btns))
    elif d.startswith("pay_"):
        amt = d.split("_")[1]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26pn=MovieBot%26am={amt}%26cu=INR"
        pay_cap = f"⚡ **{amt}₹ plan select kiya gaya hai**\n\n1️⃣ **Scan it and pay**\n2️⃣ **After payment Upload screenshot**"
        p_btns = [
            [InlineKeyboardButton("📤 UPLOAD SCREENSHOT", url=f"tg://user?id={ADMIN_ID}")],
            [InlineKeyboardButton("📞 CONTACT ADMIN", url=f"tg://user?id={ADMIN_ID}")],
            [InlineKeyboardButton("❌ CANCEL PAYMENT", callback_data="close_btn")]
        ]
        await query.message.reply_photo(photo=qr_url, caption=pay_cap, reply_markup=InlineKeyboardMarkup(p_btns))
    elif d in ["help", "ideas", "scan_aud", "get_all"]:
        await query.answer("Ye option active hai!", show_alert=False)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app.run()
