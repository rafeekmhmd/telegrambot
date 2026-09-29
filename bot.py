import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

ADMIN_ID = 1126219851  # 1. CHANGE THIS TO YOUR NUMERIC USER ID

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_safe_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)[:50]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ **Welcome to the Ultimate Media Downloader!**\n\n"
        "Send me a valid YouTube link directly, and I will generate an interactive menu on your screen."
    )

# Admin command panel check
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("✨ Downloader Status: Online and fully updated, Boss!")
    else:
        await update.message.reply_text("❌ Unauthorized access.")

# Step 1: Detect link and present Main Interactive Screen
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please enter a valid YouTube link.")
        return

    # Create Selection Buttons on Screen
    keyboard = [
        [
            InlineKeyboardButton("🎥 Video Screen", callback_data=f"menu_video|{url}"),
            InlineKeyboardButton("🎵 MP3 Audio Screen", callback_data=f"menu_audio|{url}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎯 **Format Choice:** Select your output medium below:", reply_markup=reply_markup)

# Step 2: Handle quality choice submenu
async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data, url = query.data.split("|")
    
    if data == "menu_video":
        keyboard = [
            [InlineKeyboardButton("HD High Quality (720p)", callback_data=f"dl_video_720|{url}")],
            [InlineKeyboardButton("Standard Quality (480p)", callback_data=f"dl_video_480|{url}")]
        ]
        text = "🎬 Select your preferred **Video Resolution**:"
    else:
        keyboard = [
            [InlineKeyboardButton("High Definition (320kbps MP3)", callback_data=f"dl_audio_320|{url}")],
            [InlineKeyboardButton("Standard Audio (192kbps MP3)", callback_data=f"dl_audio_192|{url}")]
        ]
        text = "🎧 Select your preferred **Audio Quality**:"
        
    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

# Step 3: Download and deliver the chosen payload
async def process_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, url = query.data.split("|")
    await query.edit_message_text("⏳ Connecting to secure bypass nodes... Please wait.")
    
    file_id = str(query.message.message_id)
    
    # Advanced mobile client spoofs to eliminate "Sign in to confirm you are not a bot" errors
    base_bypass_args = {'youtube': {'player_client': ['ios', 'android', 'mweb']}}

    if "dl_audio" in action:
        quality = "320" if "320" in action else "192"
        ydl_opts = {
            'format': 'ba/b',
            'outtmpl': f'audio_{file_id}.%(ext)s',
            'max_filesize': 45 * 1024 * 1024,
            'extractor_args': base_bypass_args,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
        }
        expected_ext = "mp3"
    else:
        height = "720" if "720" in action else "480"
        ydl_opts = {
            'format': f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best',
            'outtmpl': f'video_{file_id}.%(ext)s',
            'max_filesize': 45 * 1024 * 1024,
            'extractor_args': base_bypass_args,
            'merge_output_format': 'mp4',
        }
        expected_ext = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = get_safe_filename(info.get('title', 'media_file'))
            
        filename = f"audio_{file_id}.{expected_ext}" if "dl_audio" in action else f"video_{file_id}.{expected_ext}"
        final_output = f"{title}.{expected_ext}"
        
        if os.path.exists(filename):
            os.rename(filename, final_output)
            await query.edit_message_text("📤 Dispatching media files safely to your Telegram screen...")
            
            with open(final_output, 'rb') as local_file:
                if "dl_audio" in action:
                    await query.message.reply_audio(audio=local_file, title=title, caption=f"🎵 Converted at {quality}kbps")
                else:
                    await query.message.reply_video(video=local_file, caption=f"🎥 Resolution: {height}p")
            
            os.remove(final_output)
            await query.message.delete()
        else:
            await query.edit_message_text("❌ Download was successful, but processing failed to save locally.")

    except Exception as e:
        logging.error(e)
        await query.edit_message_text("❌ Bypassing failed. The video might be completely blocked by YouTube or over the 45MB ceiling.")
        for item in os.listdir('.'):
            if file_id in item:
                try: os.remove(item)
                except: pass

if __name__ == '__main__':
    # 2. VERIFY YOUR SECRET BOT TOKEN IS PLACED HERE Correctly
    BOT_TOKEN = "8836848217:AAE_Ht4bzJ2ymkg0E6ChsZvnI__fMOjfNOI"

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_link))
    application.add_handler(CallbackQueryHandler(handle_menu_selection, pattern="^menu_"))
    application.add_handler(CallbackQueryHandler(process_download, pattern="^dl_"))
    
    application.run_polling()
