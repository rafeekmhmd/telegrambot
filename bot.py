import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp

# 1. PASTE YOUR COPIED NUMERIC TELEGRAM ID HERE (e.g., 584920394)
ADMIN_ID = 1126219851  

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send me any YouTube video link, and I will try to fetch the video file for you!"
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("✨ YouTube Saver Bot Status: Online and running perfectly, Boss!")
    else:
        await update.message.reply_text("❌ Unauthorized. Admin access only.")

async def download_youtube_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    # Simple check to see if it's a YouTube link
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    status_message = await update.message.reply_text("⏳ Processing video... Please wait.")

    # Configuration for video processing
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'downloaded_video.mp4',
        'max_filesize': 45 * 1024 * 1024, # Limit to 45MB so Telegram can send it smoothly
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        await status_message.edit_text("📤 Uploading video to Telegram...")
        
        # Send the file back to the user
        with open('downloaded_video.mp4', 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption="Downloaded via your Mobile Bot!")
            
        # Clean up the cloud storage file
        os.remove('downloaded_video.mp4')
        await status_message.delete()

    except Exception as e:
        logging.error(e)
        await status_message.edit_text("❌ Failed to download. The video might be too large or restricted.")
        if os.path.exists('downloaded_video.mp4'):
            os.remove('downloaded_video.mp4')

if __name__ == '__main__':
    # 2. MAKE SURE YOUR SECRET BOTFATHER TOKEN IS PLACED HERE
    application = ApplicationBuilder().token('8836848217:AAE_Ht4bzJ2ymkg0E6ChsZvnI__fMOjfNOI').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_youtube_video))
    
    application.run_polling()
