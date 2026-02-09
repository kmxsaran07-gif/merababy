import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import pyromod.listen

# ================= CONFIG =================
API_ID = 28446111       # <-- change
API_HASH = "4ef8f43ed7d3f22b1e3acc40e86d7506"  # <-- change
BOT_TOKEN = "8526706863:AAEmBUevBA5WjydQIpWybwHXmFLFEO25gxc"  # <-- change
# =========================================

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Client(
    "yt_txt_uploader",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ================= START ==================
@bot.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    await m.reply_text(
        "🎥 **YouTube TXT Uploader Bot**\n\n"
        "📄 Send your `.txt` file\n"
        "📌 TXT format stays SAME\n"
        "🎞️ Bot will ask quality once per file\n"
        "📤 Channel upload supported\n"
        "✅ Live + Normal videos"
    )

# ============ TXT HANDLER =================
@bot.on_message(filters.document & filters.private)
async def txt_handler(client: Client, m: Message):
    if not m.document.file_name.endswith(".txt"):
        await m.reply_text("❌ Please send a valid .txt file")
        return

    status = await m.reply_text("📥 Reading TXT file...")
    txt_path = await m.download()

    # ---------- Read TXT ----------
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]

    entries = []
    for line in lines:
        if ":" in line and "youtu" in line:
            name, url = line.split(":", 1)
            clean_name = re.sub(r'[\\/*?:"<>|]', "", name).strip()
            entries.append((clean_name, url.strip()))

    if not entries:
        await status.edit("❌ No valid YouTube links found")
        os.remove(txt_path)
        return

    # ---------- Ask Quality ----------
    await status.edit(
        "🎞️ **Select quality for THIS TXT file**\n\n"
        "Send one number:\n"
        "`360` / `480` / `720` / `1080`"
    )
    q_msg = await client.listen(m.chat.id)
    QUALITY = q_msg.text.strip()

    if QUALITY not in ["360", "480", "720", "1080"]:
        QUALITY = "360"

    # ---------- Ask Channel ----------
    await status.edit(
        "📤 **Send Channel ID** (e.g. `-100xxxxxxxxx`)\n"
        "or send `/me` to upload here"
    )
    c_msg = await client.listen(m.chat.id)

    if c_msg.text.strip() == "/me":
        CHANNEL_ID = m.chat.id
    else:
        CHANNEL_ID = int(c_msg.text.strip())

    await status.edit(
        f"▶️ **Starting upload**\n\n"
        f"🎞️ Quality: {QUALITY}p\n"
        f"📦 Total videos: {len(entries)}"
    )

    # ---------- Download + Upload ----------
    for idx, (title, url) in enumerate(entries, start=1):
        filename = f"{idx:03d} - {title}.mp4"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        ytf = f"bv*[height<={QUALITY}]/bv*/b"

        cmd = [
            "yt-dlp",
            "-f", ytf,
            "--extractor-args", "youtube:player_client=android",
            "--downloader", "ffmpeg",
            "--hls-use-mpegts",
            "--merge-output-format", "mp4",
            "-o", filepath,
            url
        ]

        prog = await m.reply_text(
            f"⬇️ **Downloading {idx}/{len(entries)}**\n"
            f"🎓 {title}\n"
            f"🎞️ {QUALITY}p"
        )

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process.communicate()

        if not os.path.exists(filepath):
            await prog.edit(f"❌ Failed: {title}")
            continue

        await prog.edit("⬆️ **Uploading to Telegram...**")

        await client.send_document(
            chat_id=CHANNEL_ID,
            document=filepath,
            caption=f"🎓 **{title}**\n🎞️ Quality: {QUALITY}p"
        )

        os.remove(filepath)
        await prog.edit(f"✅ Uploaded: {title}")

    os.remove(txt_path)
    await m.reply_text("🎉 **All videos uploaded successfully**")

# =========================================
print("Bot Started...")
bot.run()
