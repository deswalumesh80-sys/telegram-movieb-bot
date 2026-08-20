import os
import threading
import uvicorn
import requests
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Configuration
API_ID = int(os.environ.get("API_ID", "38398715"))
API_HASH = os.environ.get("API_HASH", "9d70e41f8c67908ed547e31c2cfe9c38")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8588875170:AAE-2TF39moR_LksMVaYbxG5JLHB-pASoQM")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8471574210"))
UPI_ID = os.environ.get("UPI_ID", "example@upi")

# Kinopoisk Dev API Settings
KP_API_KEY = os.environ.get("KP_API_KEY", "XN7WBQA-MF24EYN-Q4SWZHF-7AR2715")
KP_API_URL = os.environ.get("KP_API_URL", "https://api.kinopoisk.dev/v1.4")

# Keep-Alive Web Server for Render
web_app = FastAPI()

@web_app.get("/")
def home():
    return {"status": "bot_running_successfully"}

def run_web():
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(web_app, host="0.0.0.0", port=port)

app = Client("toji_kinopoisk_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
USER_PAGES = {}

# 1. Start Interface
@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = (
        "🥷 **I am #Toji v2.1**\n"
        "🍿 **Unlimited files & series**\n"
        "⚡ **Get instant stream**\n"
        "💯 **100% Free, always**\n"
        "🏷️ **By The Filmy Men**\n\n"
        "🔍 *Kisi bhi movie ya web series ka naam likh kar bhejein.*"
    )
    buttons = [
        [InlineKeyboardButton("🔍 Quick Help", callback_data="help"), InlineKeyboardButton("👮 Admin Support", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("💡 Movie Ideas", callback_data="ideas"), InlineKeyboardButton("💳 Upgrade Plan", callback_data="plan_menu")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# 2. Search Handler (Kinopoisk Cloud API)
@app.on_message(filters.text & ~filters.command(["start", "plan"]))
async def kinopoisk_search(client, message):
    query = message.text.strip()
    if query.startswith("/"):
        return

    status_msg = await message.reply_text("🔎 **Searching server for:** `" + query + "`...")
    
    headers = {
        "X-API-KEY": KP_API_KEY,
        "Accept": "application/json"
    }
    
    search_url = f"{KP_API_URL}/movie/search"
    params = {"page": 1, "limit": 15, "query": query}
    
    try:
        res = requests.get(search_url, headers=headers, params=params, timeout=10).json()
        results = res.get("docs", [])
    except Exception:
        results = []

    if not results:
        await status_msg.edit_text("❌ **Koi movie nahi mili. Spelling check karein.**")
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

    btn = [[InlineKeyboardButton("📩 Get All Files 📩", callback_data="get_all")]]
    for item in current:
        title = item.get("name") or item.get("alternativeName") or item.get("enName") or "Unknown"
        year = item.get("year", "N/A")
        item_id = item.get("id")
        btn.append([InlineKeyboardButton(f"🎬 {title} ({year}) ↗️", callback_data=f"kp_{item_id}")])

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

# 3. Callbacks & Movie Detail Presentation (Toji Layout)
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
    elif d.startswith("kp_"):
        kp_id = d.split("_")[1]
        
        # Details Fetch
        headers = {"X-API-KEY": KP_API_KEY}
        detail_url = f"{KP_API_URL}/movie/{kp_id}"
        
        try:
            m = requests.get(detail_url, headers=headers, timeout=8).json()
            title = m.get("name") or m.get("alternativeName") or m.get("enName") or "Movie Details"
            rating = m.get("rating", {}).get("imdb") or m.get("rating", {}).get("kp") or "7.5"
            stream_url = f"https://kinobox.tv/embed/{kp_id}"
        except Exception:
            title = "Movie Details"
            rating = "7.5"
            stream_url = f"https://kinobox.tv/embed/{kp_id}"

        response_caption = (
            f"🎬 **Movie Details Ready**\n"
            f"🆔 **Subject ID :** `{kp_id}`\n"
            f"⭐️ **Rating :** `{rating}`\n\n"
            f"⚡ **Powered By :** MovieBox API\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        watch_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch / Stream", url=stream_url), InlineKeyboardButton("⬇️ Download", url=stream_url)],
            [InlineKeyboardButton("🔙 Back to List", callback_data="close_btn")]
        ])
        
        await query.message.reply_text(response_caption, reply_markup=watch_btn)
    elif d == "plan_menu":
        plan_text = (
            "🌸 **Premium Plans And Pricing** 🌸\n\n"
            "🏷️ **Plan 1 : 50₹ - 1 Month**\n"
            "🏷️ **Plan 2 : 90₹ - 2 Month**\n"
            "🏷️ **Plan 3 : 140₹ - 3 Month**\n"
            "🏷️ **Plan 4 : 190₹ - 4 Month**\n\n"
            "📌 *Select a plan:*"
        )
        btns = [
            [InlineKeyboardButton("1 Month", callback_data="pay_50"), InlineKeyboardButton("2 Month", callback_data="pay_90")],
            [InlineKeyboardButton("3 Month", callback_data="pay_140"), InlineKeyboardButton("4 Month", callback_data="pay_190")],
            [InlineKeyboardButton("← Back", callback_data="close_btn")]
        ]
        await query.message.reply_text(plan_text, reply_markup=InlineKeyboardMarkup(btns))
    elif d.startswith("pay_"):
        amt = d.split("_")[1]
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26pn=MovieBot%26am={amt}%26cu=INR"
        p_btns = [
            [InlineKeyboardButton("📤 UPLOAD SCREENSHOT", url=f"tg://user?id={ADMIN_ID}")],
            [InlineKeyboardButton("❌ CANCEL PAYMENT", callback_data="close_btn")]
        ]
        await query.message.reply_photo(photo=qr_url, caption=f"⚡ **{amt}₹ Plan Chuna Gaya Hai**\n\nScan karke payment screenshot bhejein.", reply_markup=InlineKeyboardMarkup(p_btns))
    elif d in ["help", "ideas", "get_all"]:
        await query.answer("Working option!", show_alert=False)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app.run()
    
