import logging
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

# 1. PASTE YOUR COPIED NUMERIC TELEGRAM ID HERE (e.g., 584920394)
ADMIN_ID = 1126219851  

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Helper function to clean file names safely
def get_safe_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)[:50]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Welcome to your YouTube Downloader Bot!**\n\n"
        "• Send me any YouTube link directly to download it as a **Video** (Capped at 720p/45MB).\n"
        "• Use the command `/mp3 <link>` to download it as a high-quality **Audio Track**."
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("✨ YouTube Saver Bot Status: Online and running perfectly, Boss!")
    else:
        await update.message.reply_text("❌ Unauthorized. Admin access only.")

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE, is_audio=False, url=""):
    if not url:
        url = update.message.text

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    status_message = await update.message.reply_text("⏳ Processing your request... Please wait.")
    file_id = str(update.message.message_id)
    
        # Bypassing YouTube's automated block rules
    if is_audio:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'audio_{file_id}.%(ext)s',
            'max_filesize': 45 * 1024 * 1024,
            'extractor_args': {'youtube': {'player_client': 'web_safari,web_embedded,-tv_downgraded'}},
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        expected_ext = "mp3"
        
    else:
        ydl_opts = {
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
            'outtmpl': f'video_{file_id}.%(ext)s',
            'max_filesize': 45 * 1024 * 1024,
            'extractor_args': {'youtube': {'player_client': 'web_safari,web_embedded,-tv_downgraded'}},
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
            await status_message.edit_text("📤 Uploading file to Telegram...")
            
            with open(final_output, 'rb') as local_file:
                if is_audio:
                    await update.message.reply_audio(audio=local_file, title=title, caption="Audio extracted successfully!")
                else:
                    await update.message.reply_video(video=local_file, caption=f"🎥 {title}")
            
            os.remove(final_output)
            await status_message.delete()
        else:
            await status_message.edit_text("❌ System error: Downloaded asset could not be located.")

    except Exception as e:
        logging.error(e)
        await status_message.edit_text("❌ Failed to process. The video might be too long, private, or over the 50MB limit.")
        for item in os.listdir('.'):
            if file_id in item:
                try: os.remove(item)
                except: pass

async def mp3_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/mp3 <paste your youtube link here>`")
        return
    url_arg = context.args[0]
    await download_media(update, context, is_audio=True, url=url_arg)

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await download_media(update, context, is_audio=False)

if __name__ == '__main__':
    # 2. BOTFATHER TOKEN GOES DIRECTLY HERE
    BOT_TOKEN = "8836848217:AAE_Ht4bzJ2ymkg0E6ChsZvnI__fMOjfNOI"

    # Direct standard connection (Zero docker layers needed)
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(CommandHandler('mp3', mp3_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), video_handler))
    
    application.run_polling()
