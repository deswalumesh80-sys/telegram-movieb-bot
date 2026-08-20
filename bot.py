import os
import threading
import uvicorn
import requests
import cloudscraper
from bs4 import BeautifulSoup
from fastapi import FastAPI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Credentials
API_ID = int(os.environ.get("API_ID", "38398715"))
API_HASH = os.environ.get("API_HASH", "9d70e41f8c67908ed547e31c2cfe9c38")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8588875170:AAE-2TF39moR_LksMVaYbxG5JLHB-pASoQM")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8471574210"))
UPI_ID = os.environ.get("UPI_ID", "example@upi")

# Web Scraper setup
scraper = cloudscraper.create_scraper()

# FastAPI Server for 24/7 Render Keep-Alive
web_app = FastAPI()

@web_app.get("/")
def home():
    return {"status": "multi_movie_scraper_alive"}

def run_web():
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(web_app, host="0.0.0.0", port=port)

app = Client("movie_links_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
USER_PAGES = {}

# 1. Start Interface
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    text = (
        "🥷 **I am #Toji v2.1 (Multi-Site Engine)**\n"
        "🍿 **Unlimited Movies & Web Series**\n"
        "⚡ **Auto-Scraped Links: VegaMovies, KatmovieHD & Cloud Servers**\n"
        "💯 **100% Free, always**\n"
        "🏷️ **By The Filmy Men**\n\n"
        "🔍 *Kisi bhi movie ya series ka naam likh kar bhejein:*"
    )
    buttons = [
        [InlineKeyboardButton("🔍 Quick Help", callback_data="help"), InlineKeyboardButton("👮 Admin Support", url=f"tg://user?id={ADMIN_ID}")],
        [InlineKeyboardButton("💡 Movie Ideas", callback_data="ideas"), InlineKeyboardButton("💳 Upgrade Plan", callback_data="plan_menu")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# 2. Multi-Site Scraper Engine (VegaMovies + Alternative Sources)
def fetch_movie_links(query):
    results = []
    
    # Source A: VegaMovies Search
    try:
        search_url = f"https://vegamovies.im/search/{query.replace(' ', '+')}"
        res = scraper.get(search_url, timeout=7)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for art in soup.find_all("article")[:5]:
                a_tag = art.find("a")
                if a_tag and a_tag.get("href"):
                    title = art.get_text(separator=" ", strip=True).replace("Download", "").strip()[:42]
                    results.append({"title": f"🌐 [VegaMovies] {title}", "url": a_tag["href"]})
    except Exception as e:
        print(f"Vega Scraping error: {e}")

    # Source B: Cloud Stream / Katmovie Alternative Fallbacks
    query_encoded = requests.utils.quote(query)
    results.append({
        "title": f"⚡ [1080p Full HD] {query.title()} Direct Server",
        "url": f"https://vidsrc.to/embed/movie/{query_encoded}"
    })
    results.append({
        "title": f"🎬 [720p HD] KatMovieHD Search Link",
        "url": f"https://katmoviehd.mom/?s={query_encoded}"
    })
    results.append({
        "title": f"📱 [480p Fast Stream] Online Web Player",
        "url": f"https://autoembed.cc/embed/movie/{query_encoded}"
    })

    return results

# 3. User Search Handler
@app.on_message(filters.text & filters.private & ~filters.command(["start", "plan"]))
async def handle_movie_search(client, message):
    query = message.text.strip()
    status_msg = await message.reply_text(f"🔎 **Fetching links from VegaMovies & Cloud Servers for:** `{query}`...")

    results = fetch_movie_links(query)

    USER_PAGES[message.from_user.id] = {"query": query, "results": results, "page": 0}
    await status_msg.delete()
    await display_page(client, message.chat.id, message.id, message.from_user.id, edit=False)

# 4. Button Display
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

    btn = [[InlineKeyboardButton("🍿 Open Direct HD Server 🍿", url=current[0]["url"])]]
    for item in current:
        btn_text = item["title"] + " ↗️"
        btn.append([InlineKeyboardButton(btn_text, url=item["url"])])

    nav = []
    if total_pages > 1:
        nav.append(InlineKeyboardButton(f"📑 Pages {page+1}/{total_pages}", callback_data="pages"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("Next ⏩", callback_data="next_p"))
        elif page > 0:
            nav.append(InlineKeyboardButton("⏪ Prev", callback_data="prev_p"))
        btn.append(nav)

    try:
        user_obj = await client.get_users(user_id)
        u_name = user_obj.first_name
    except Exception:
        u_name = "User"

    cap = f"⛩️ **Requested By :** [{u_name}](tg://user?id={user_id})\n━━━━━━━━━━━━━━━━━━━━━━\n⚡ **Source:** VegaMovies & Multi-Cloud Networks"
    
    if edit and msg_id:
        await client.edit_message_text(chat_id, msg_id, cap, reply_markup=InlineKeyboardMarkup(btn))
    else:
        await client.send_message(chat_id, cap, reply_to_message_id=reply_id, reply_markup=InlineKeyboardMarkup(btn))

# 5. Callbacks
@app.on_callback_query()
async def callback_actions(client, query: CallbackQuery):
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
        await query.message.reply_photo(photo=qr_url, caption=f"⚡ **{amt}₹ Plan Selected**", reply_markup=InlineKeyboardMarkup(p_btns))
    elif d in ["help", "ideas", "pages"]:
        await query.answer("Active!", show_alert=False)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    app.run()
    
