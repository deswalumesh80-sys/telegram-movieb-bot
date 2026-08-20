import os
import threading
import uvicorn
import requests
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

API_ID = int(os.environ.get("API_ID", "38398715"))
API_HASH = os.environ.get("API_HASH", "9d70e41f8c67908ed547e31c2cfe9c38")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8588875170:AAE-2TF39moR_LksMVaYbxG5JLHB-pASoQM")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8471574210"))
UPI_ID = os.environ.get("UPI_ID", "example@upi")

web_app = FastAPI()

@web_app.get("/")
def home():
    return {"status": "running"}

def run_web():
    uvicorn.run(web_app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

app = Client("toji_movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
USER_PAGES = {}

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = (
        "🥷 **I am #Toji v2.1**\n"
        "🍿 **Unlimited Movies & Web Series**\n"
        "⚡ **Direct Cloud Server Stream**\n"
        "💯 **100% Free, always**\n"
        "🏷️ **By The Filmy Men**\n\n"
        "🔍 *Kisi bhi movie ya web series ka naam likh kar bhejein.*"
    )
    buttons = [
        [InlineKeyboardButton("🔍 Quick Help", callback_data="help"), InlineKeyboardButton("👮 Admin Support", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("💡 Movie Ideas", callback_data="ideas"), InlineKeyboardButton("💳 Upgrade Plan", callback_data="plan_menu")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.text & ~filters.command(["start", "plan"]))
async def movie_search(client, message):
    query = message.text.strip()
    if query.startswith("/"):
        return

    status_msg = await message.reply_text(f"🔎 **Searching server for:** `{query}`...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    results = []
    
    # 1. Multi Search (Movies + TV Series)
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key=fba577b8f9e6d0a7a72d3f3f0d453b34&language=hi-IN&query={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=10).json()
        for i in res.get("results", []):
            m_type = i.get("media_type")
            if m_type in ["movie", "tv"]:
                title = i.get("title") or i.get("name") or i.get("original_title") or "Movie"
                year = (i.get("release_date") or i.get("first_air_date") or "2024")[:4]
                results.append({"title": title, "year": year, "id": i["id"], "type": m_type})
    except Exception:
        pass

    # 2. English Fallback Search (Agar Hindi/Global me na mile)
    if not results:
        try:
            url_en = f"https://api.themoviedb.org/3/search/multi?api_key=fba577b8f9e6d0a7a72d3f3f0d453b34&query={requests.utils.quote(query)}"
            res_en = requests.get(url_en, headers=headers, timeout=10).json()
            for i in res_en.get("results", []):
                m_type = i.get("media_type")
                if m_type in ["movie", "tv"]:
                    title = i.get("title") or i.get("name") or "Movie"
                    year = (i.get("release_date") or i.get("first_air_date") or "2024")[:4]
                    results.append({"title": title, "year": year, "id": i["id"], "type": m_type})
        except Exception:
            pass

    if not results:
        await status_msg.edit_text("❌ **Koi movie ya series nahi mili. Spelling check karein.**")
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
        btn_text = f"🎬 [{item['type'].upper()}] {item['title']} ({item['year']})"[:45] + " ↗️"
        btn.append([InlineKeyboardButton(btn_text, callback_data=f"play_{item['id']}_{item['type']}")])

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
    elif d.startswith("play_"):
        _, item_id, m_type = d.split("_")
        stream_url = f"https://vidsrc.to/embed/{m_type}/{item_id}"
        dl_url = f"https://autoembed.cc/embed/{m_type}/{item_id}"
        
        watch_btn = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch / Stream Online", url=stream_url)],
            [InlineKeyboardButton("⬇️ Fast Download Server", url=dl_url)],
            [InlineKeyboardButton("❌ Close", callback_data="close_btn")]
        ])
        await query.message.reply_text(
            f"🎬 **Movie Stream Ready!**\n\n"
            f"🆔 **Server ID :** `{item_id}`\n"
            f"🍿 **Quality :** 1080p / 720p HD\n"
            f"⚡ **Powered By :** Global Movie Server\n\n"
            f"👇 *Neeche diye gaye link par click karke dekhein:*",
            reply_markup=watch_btn
        )
    elif d == "plan_menu":
        plan_text = "🌸 **Premium Plans** 🌸\n\n🏷️ **Plan 1 : 50₹ - 1 Month**\n🏷️ **Plan 2 : 90₹ - 2 Month**\n🏷️ **Plan 3 : 140₹ - 3 Month**"
        btns = [
            [InlineKeyboardButton("1 Month", callback_data="pay_50"), InlineKeyboardButton("2 Month", callback_data="pay_90")],
            [InlineKeyboardButton("3 Month", callback_data="pay_140"), InlineKeyboardButton("← Back", callback_data="close_btn")]
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
    elif d in ["help", "ideas", "get_all"]:
        await query.answer("Working option!", show_alert=False)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app.run()
        
