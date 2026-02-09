import os
import re
import time
import asyncio
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

# ========== CONFIG ==========
API_ID = 28446111
API_HASH = "4ef8f43ed7d3f22b1e3acc40e86d7506"
BOT_TOKEN = "8526706863:AAEmBUevBA5WjydQIpWybwHXmFLFEO25gxc"
OWNER_ID = 8327651421
# ============================

bot = Client("yt_txt_uploader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

STOP_FLAG = False


# ================= PROGRESS BAR =================
async def progress_bar(current, total, message, start):
    now = time.time()
    diff = now - start
    if diff == 0:
        return

    percent = current * 100 / total
    speed = current / diff
    eta = (total - current) / speed if speed else 0

    def h(x):
        for u in ["B", "KiB", "MiB", "GiB"]:
            if x < 1024:
                return f"{x:.2f}{u}"
            x /= 1024

    bar = "◆" * int(percent / 8) + "◇" * (12 - int(percent / 8))

    text = (
        "╭──⌈📤 𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 📤⌋──╮\n"
        f"┣⪼ [ {bar} ]\n"
        f"┣⪼ 🚀 Speed : {h(speed)}/s\n"
        f"┣⪼ 📈 Progress : {percent:.1f}%\n"
        f"┣⪼ ⏳ Loaded : {h(current)}\n"
        f"┣⪼ 🍁 Size : {h(total)}\n"
        f"┣⪼ 🕛 ETA : {int(eta)}s\n"
        "╰────⌈ ✪ Spark ✪ ⌋────╯"
    )
    try:
        await message.edit_text(text)
    except:
        pass


# ================= COMMANDS =================
@bot.on_message(filters.command("start"))
async def start(_, m: Message):
    await m.reply_text(
        "🎬 **YouTube TXT Uploader Bot**\n\n"
        "• Send `.txt` file\n"
        "• Select quality per file\n"
        "• Channel upload supported\n"
        "• /stop = instant stop"
    )


@bot.on_message(filters.command("stop"))
async def stop(_, m: Message):
    global STOP_FLAG
    STOP_FLAG = True
    await m.reply_text("🛑 **Process stopped successfully**")


# ================= MAIN TXT HANDLER =================
@bot.on_message(filters.document & filters.private)
async def txt_handler(client: Client, m: Message):
    global STOP_FLAG
    STOP_FLAG = False

    if not m.document.file_name.endswith(".txt"):
        return

    path = await m.download()
    with open(path, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f if x.strip()]

    await m.reply_text("🎞️ Send quality: 360 / 480 / 720 / 1080")
    q = (await client.listen(m.chat.id)).text.strip()
    if q not in ["360", "480", "720", "1080"]:
        q = "360"

    await m.reply_text("📚 Send batch name")
    batch = (await client.listen(m.chat.id)).text.strip()

    await m.reply_text("🎓 Send Uploaded By name")
    uploader = (await client.listen(m.chat.id)).text.strip()

    await m.reply_text("📢 Send Channel ID or /me")
    ch = (await client.listen(m.chat.id)).text.strip()
    CHANNEL_ID = m.chat.id if ch == "/me" else int(ch)

    await m.reply_text(
        f"🚀 **Starting Upload**\n\n"
        f"Quality: {q}p\n"
        f"Total: {len(lines)}"
    )

    index = 1

    for line in lines:
        if STOP_FLAG:
            await m.reply_text("🛑 **Stopped by user**")
            break

        try:
            title, url = line.split(":", 1)
            safe = re.sub(r"[^\w\- ]", "", title)[:60]
            filename = f"{safe}.mp4"

            ytf = f"bv*[height<={q}]/bv*/b"
            cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{filename}"'
            subprocess.run(cmd, shell=True)

            if not os.path.exists(filename):
                continue

            caption = (
                f"🏷️ **Index ID** : {str(index).zfill(3)}\n\n"
                f"📑 **Title** : {title}\n\n"
                f"📚 **Batch** : {batch}\n\n"
                f"🎓 **Uploaded By** : {uploader}\n\n"
                f"🎞️ **Quality** : {q}p"
            )

            msg = await m.reply_text("📤 Uploading...")
            start = time.time()

            await client.send_video(
                chat_id=CHANNEL_ID,
                video=filename,
                caption=caption,
                supports_streaming=True,
                progress=progress_bar,
                progress_args=(msg, start)
            )

            await msg.delete()
            os.remove(filename)
            index += 1

        except Exception as e:
            await m.reply_text(f"❌ Failed: `{e}`")

    os.remove(path)
    STOP_FLAG = False
    await m.reply_text("✅ **Task Finished**")


# ================= RUN =================
print("Bot Started")
bot.run()
