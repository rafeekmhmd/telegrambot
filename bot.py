import logging
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

ADMIN_ID = 1126219851  # Replace with your numeric Telegram User ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Helper function to extract a clean filename slug
def get_safe_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)[:50]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **2GB High-Capacity Downloader Bot**\n\n"
        "• Send a link directly to download it as a **Video**\n"
        "• Type `/mp3 <link>` to download it as a **High-Quality Audio Track**"
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE, is_audio=False, url=""):
    if not url:
        url = update.message.text

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please provide a valid YouTube link.")
        return

    status_message = await update.message.reply_text("⏳ Fetching metadata and downloading source from YouTube...")

    # Unique identifier base
    file_id = str(update.message.message_id)
    
    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'audio_{file_id}.%(ext)s',
            'max_filesize': 1950 * 1024 * 1024, # 1.95 GB Cap
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }
        expected_ext = "mp3"
    else:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': f'video_{file_id}.%(ext)s',
            'max_filesize': 1950 * 1024 * 1024, # 1.95 GB Cap
            'merge_output_format': 'mp4',
        }
        expected_ext = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = get_safe_filename(info.get('title', 'media_file'))
            
        filename = f"audio_{file_id}.{expected_ext}" if is_audio else f"video_{file_id}.{expected_ext}"
        final_output = f"{title}.{expected_ext}"
        
        if os.path.exists(filename):
            os.rename(filename, final_output)
            
            await status_message.edit_text("📤 Uploading heavy payload to Telegram server (Up to 2GB supported)...")
            
            with open(final_output, 'rb') as local_file:
                if is_audio:
                    await update.message.reply_audio(audio=local_file, title=title, caption="Audio extracted via Mobile Bot!")
                else:
                    await update.message.reply_video(video=local_file, caption=f"🎥 {title}")
            
            os.remove(final_output)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ Processing completed but local download asset was not located.")

    except Exception as e:
        logging.error(e)
        await status_message.edit_text(f"❌ Operation terminated. Ensure file is within bounds or not restricted.")
        # Cleanup routine
        for f in os.listdir('.'):
            if file_id in f:
                try: os.remove(f)
                except: pass

async def mp3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Missing arguments. Usage: `/mp3 https://youtube.com/...`")
        return
    await download_media(update, context, is_audio=True, url=context.args[0])

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await download_media(update, context, is_audio=False)

if __name__ == '__main__':
    # REPLACE BOTH VALS BELOW TO CONNECT TO LOCAL APIS
    BOT_TOKEN = "8836848217:AAE_Ht4bzJ2ymkg0E6ChsZvnI__fMOjfNOI"
    LOCAL_SERVER_URL = "http://localhost:8081/bot" # Your local instance point

    application = ApplicationBuilder().token(BOT_TOKEN).base_url(LOCAL_SERVER_URL).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('mp3', mp3_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), video_handler))
    
    application.run_polling()
