import os
import threading
import uvicorn
import requests
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
UPI_ID = os.environ.get("UPI_ID", "example@upi")

SEARCH_API = "https://autoembed.cc/api/search"

web_app = FastAPI()

@web_app.get("/")
def home():
    return {"status": "running"}

def run_web():
    uvicorn.run(web_app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

app = Client("toji_server_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
USER_PAGES = {}

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    text = (
        "🥷 **I am #Toji v2.1**\n"
        "🍿 **Unlimited Movies & Web Series**\n"
        "⚡ **Direct Server Cloud Stream**\n"
        "💯 **100% Free, always**\n"
        "🏷️ **By The Filmy Men**\n\n"
        "🔍 *Kisi bhi movie ya web series ka naam likhein:*"
    )
    buttons = [
        [InlineKeyboardButton("🔍 Quick Help", callback_data="help"), InlineKeyboardButton("👮 Admin Support", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("💡 Movie Ideas", callback_data="ideas"), InlineKeyboardButton("💳 Upgrade Plan", callback_data="plan_menu")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.text & filters.private & ~filters.command(["start", "plan"]))
async def server_search(client, message):
    query = message.text.strip()
    status_msg = await message.reply_text("🔎 **Searching cloud servers...**")
    
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key=fba577b8f9e6d0a7a72d3f3f0d453b34&query={requests.utils.quote(query)}"
        res = requests.get(url, timeout=10).json()
        results = [i for i in res.get("results", []) if i.get("media_type") in ["movie", "tv"]]
    except Exception:
        results = []

    if not results:
        await status_msg.edit_text("❌ **Koi movie nahi mili. Sahi spelling likhein.**")
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

    btn = [[InlineKeyboardButton("📩 Get All Results 📩", callback_data="get_all")]]
    for item in current:
        title = item.get("title") or item.get("name") or "Unknown"
        media_type = item.get("media_type", "movie").upper()
        year = (item.get("release_date") or item.get("first_air_date") or "2024")[:4]
        item_id = item["id"]
        btn.append([InlineKeyboardButton(f"🎬 [{media_type}] {title} ({year}) ↗️", callback_data=f"get_{item_id}_{media_type}")])

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
async def handle_callbacks(client, query: CallbackQuery):
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
    elif d.startswith("get_"):
        _, item_id, media_type = d.split("_")
        stream_url = f"https://vidsrc.to/embed/{media_type.lower()}/{item_id}"
        
        watch_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch / Stream Online", url=stream_url)],
            [InlineKeyboardButton("⚡ Fast Download", url=stream_url)],
            [InlineKeyboardButton("❌ Close", callback_data="close_btn")]
        ])
        await query.message.reply_text(
            f"🎬 **Movie Ready To Stream!**\n\n"
            f"🆔 **Server ID :** `{item_id}`\n"
            f"⚡ **Powered By :** MovieBox Cloud API\n"
            f"🍿 **Quality :** 1080p / 720p HD\n\n"
            f"👇 *Neeche diye gaye link par click karke dekhein:*",
            reply_markup=watch_btn
        )
    elif d == "plan_menu":
        plan_text = "🌸 **Premium Plans** 🌸\n\n🏷️ **Plan 1 : 50₹ - 1 Month**\n🏷️ **Plan 2 : 90₹ - 2 Month**\n🏷️ **Plan 3 : 140₹ - 3 Month**"
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
    elif d in ["help", "ideas", "scan_aud", "get_all"]:
        await query.answer("Active!", show_alert=False)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app.run()
    
