import os
import asyncio
from aiohttp import web
from pyrogram import Client, filters

# Configuration
API_ID = int(os.environ.get("API_ID", "38398715"))
API_HASH = os.environ.get("API_HASH", "9d70e41f8c67908ed547e31c2cfe9c38")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8588875170:AAE-2TF39moR_LksMVaYbxG5JLHB-pASoQM")
SESSION_STRING = os.environ.get("SESSION_STRING", "BQJJ6vsAxbndI_hi483TiILHUL-RNmqenVNleErZYY0Htf7E8j02A7yKRoL41MOeZtVbhyTTviQG56HQQrFIORezNimH_XeCsZ4IO2307ySSqNOYJpz6Ccncl84FLdmM6Ekm-GlED7f805aKtaUppAMKQzzsRq0XeycPc9Mh1Pmk5KdMN5brdQpcnZIst6SMc-imIzAwAiCBiWx1jcFbU2e0ZEkK0swk3C_aiHazrbk1MfiH1z2phcNXTrf--YM_XOCmemiKUroScFc1yOeoNL6Fn8lUroaz9uW-z3nqPmYI2IuyhhMuoQx37BrhXwvgY6ObUzopOdYe7JDJiRc88PLt4RPC8gAAAAH_79WiAQ")
STORAGE_GROUP = int(os.environ.get("STORAGE_GROUP", "-1004463914808"))
PORT = int(os.environ.get("PORT", 8080))

TARGET_BOT = "ipapkornbot"

bot = Client("main_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user = Client("fetcher_user", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# Dummy Web Server to fix Render Port Binding
async def handle_ping(request):
    return web.Response(text="Bot is Alive and Running!")

async def start_web_server():
    server = web.Application()
    server.router.add_get("/", handle_ping)
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

# Bot Handlers
@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    await m.reply_text(
        "🥷 **#Toji Movie Engine Online**\n\n"
        "🍿 *Kisi bhi movie ya web series ka naam likhkar bhejein:*"
    )

@bot.on_message(filters.private & ~filters.command("start"))
async def handle_search(c, m):
    query = m.text.strip()
    status_msg = await m.reply_text(f"🔍 **'{query}' search ho raha hai...**")
    
    try:
        await m.forward(STORAGE_GROUP)
    except Exception:
        pass

    try:
        await user.send_message(TARGET_BOT, query)
        await asyncio.sleep(4)

        found_file = False
        async for msg in user.get_chat_history(TARGET_BOT, limit=3):
            if msg.video or msg.document:
                found_file = True
                file_obj = msg.video or msg.document
                caption_text = f"🎬 **{file_obj.file_name or query}**\n\n⚡ *Provided by #Toji Engine*"
                
                await user.copy_message(
                    chat_id=m.chat.id,
                    from_chat_id=TARGET_BOT,
                    message_id=msg.id,
                    caption=caption_text
                )
                await status_msg.delete()
                break
        
        if not found_file:
            await status_msg.edit_text("❌ **File nahi mili!** Kripya spelling check karein.")

    except Exception:
        await status_msg.edit_text("⚠️ **Error:** Server se file fetch nahi ho saki.")

async def main():
    await start_web_server()
    await user.start()
    await bot.start()
    print(">>> Toji Engine Web Server & Bot is Running Live!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
