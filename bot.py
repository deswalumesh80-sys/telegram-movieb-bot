import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import cloudscraper
from bs4 import BeautifulSoup

# Correct Credentials from Screenshot
API_ID = 38398715
API_HASH = "6d70e41f8c67908ed547e31c2cfe9c3a"
BOT_TOKEN = "8588875170:AAE-2TF39moR_LksMVaYbxG5JLHB-pASoQM"
PORT = int(os.environ.get("PORT", 8080))

bot = Client("vegamovies_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
scraper = cloudscraper.create_scraper()

async def handle_ping(request):
    return web.Response(text="Bot is running!", status=200)

def search_vegamovies(query):
    search_url = f"https://new2.vegamovies.futbol/?s={query.replace(' ', '+')}"
    try:
        response = scraper.get(search_url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        articles = soup.find_all("article")
        for article in articles[:6]:
            title_tag = article.find("h3") or article.find("h2") or article.find("a")
            link_tag = article.find("a")
            if title_tag and link_tag:
                title = title_tag.get_text().strip()
                link = link_tag.get("href")
                if title and link and link.startswith("http"):
                    results.append((title, link))
        return results
    except Exception:
        return []

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    await m.reply_text(
        "🥷 **#Toji VegaMovies Engine Online**\n\n"
        "🍿 *Kisi bhi movie ya web series ka naam likhkar bhejein:*"
    )

@bot.on_message(filters.private & ~filters.command("start"))
async def handle_search(c, m):
    query = m.text.strip()
    status_msg = await m.reply_text(f"🔍 **'{query}' search ho raha hai...**")
    
    results = search_vegamovies(query)
    
    if not results:
        return await status_msg.edit_text("❌ **Koi result nahi mila!** Spelling check karke dobara search karein.")
    
    buttons = []
    for title, link in results:
        short_title = (title[:30] + "..") if len(title) > 30 else title
        buttons.append([InlineKeyboardButton(f"🎬 {short_title}", url=link)])
    
    await status_msg.edit_text(
        f"🍿 **Results for:** `{query}`\n\n⚡ *Source: VegaMovies*",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    await bot.start()
    print(">>> Bot Started Successfully!")
    await idle()
    await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
    
