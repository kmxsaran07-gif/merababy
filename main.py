import os
import asyncio
import subprocess
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL

API_ID = 28446111
API_HASH = "4ef8f43ed7d3f22b1e3acc40e86d7506"
BOT_TOKEN = "8526706863:AAEmBUevBA5WjydQIpWybwHXmFLFEO25gxc"

bot = Client("yt_txt_uploader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

STOP = False

def run(cmd):
    subprocess.run(cmd, shell=True)

@bot.on_message(filters.command("stop"))
async def stop(_, m):
    global STOP
    STOP = True
    await m.reply("🛑 **Stopped successfully**")

@bot.on_message(filters.document & filters.private)
async def handle_txt(_, m: Message):
    global STOP
    STOP = False

    txt = await m.download()
    with open(txt, "r", encoding="utf-8") as f:
        lines = [x.strip() for x in f if x.strip()]

    await m.reply("🎞 **Send Quality** (360 / 480 / 720)")
    q = int((await bot.listen(m.chat.id)).text)

    await m.reply("▶️ **Send Start Index** (default = 1)")
    start = int((await bot.listen(m.chat.id)).text or 1)

    await m.reply("📚 **Send Batch Name**")
    batch = (await bot.listen(m.chat.id)).text

    await m.reply("🎓 **Send Uploaded By name**")
    uploader = (await bot.listen(m.chat.id)).text

    total = len(lines)
    await m.reply(f"🚀 **Starting Upload**\n\nQuality: {q}p\nTotal: {total}")

    for i in range(start-1, total):
        if STOP:
            break

        title, url = lines[i].split(":", 1)
        index = str(i+1).zfill(3)
        filename = f"{index}.mp4"

        ydl_opts = {
            "format": f"bv*[height<={q}]/bv*/b",
            "outtmpl": filename,
            "merge_output_format": "mp4",
            "writethumbnail": True,
            "postprocessors": [
                {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
                {"key": "EmbedThumbnail"}
            ]
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            duration = info.get("duration", 0)

        # fix duration
        fixed = f"fixed_{filename}"
        run(f'ffmpeg -i "{filename}" -c copy -movflags +faststart "{fixed}" -y')

        thumb = f"{filename}.jpg" if os.path.exists(f"{filename}.jpg") else None

        caption = f"""
🏷️ Index » {index}

📑 Title » {title}

📚 Batch » {batch}

🎓 Uploaded By » {uploader}

🎞 Quality » {q}p
"""

        msg = await m.reply("📤 Uploading...")
        await bot.send_video(
            chat_id=m.chat.id,
            video=fixed,
            thumb=thumb,
            caption=caption.strip(),
            progress=progress,
            progress_args=(msg,)
        )

        os.remove(filename)
        os.remove(fixed)
        if thumb: os.remove(thumb)

    await m.reply("✅ **All done**")

def progress(current, total, msg):
    percent = current * 100 / total
    bar = "◆" * int(percent/10) + "◇" * (10-int(percent/10))
    text = f"""
╭──⌈📤 Uploading 📤⌋──╮
┣⪼ [{bar}]
┣⪼ 📈 Progress : {percent:.1f}%
┣⪼ 📦 Loaded : {current/1024/1024:.2f} MB
┣⪼ 🧱 Size : {total/1024/1024:.2f} MB
╰────⌈ ✪ Spark ✪ ⌋────╯
"""
    asyncio.create_task(msg.edit(text))

bot.run()
