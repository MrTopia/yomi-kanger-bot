import os
from telegram import Update, InputSticker, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import tempfile
from moviepy import editor as mp

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo! Send a sticker, photo, gif or video and reply with /kang to steal it.")

async def kang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a sticker/photo/video/gif to kang it.")
        return

    replied = update.message.reply_to_message

    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "media.webp")

        # Handle stickers
        if replied.sticker:
            file = await context.bot.get_file(replied.sticker.file_id)
            await file.download_to_drive(path)
            await send_to_sticker_set(update, context, path)

        # Handle photos
        elif replied.photo:
            file = await context.bot.get_file(replied.photo[-1].file_id)
            await file.download_to_drive(path)
            img = Image.open(path).convert("RGBA")
            img = img.resize((512, 512))
            img.save(path, "WEBP")
            await send_to_sticker_set(update, context, path)

        # Handle video/gif
        elif replied.video or replied.animation:
            vid = replied.video or replied.animation
            file = await context.bot.get_file(vid.file_id)
            raw_path = os.path.join(tmpdir, "raw.mp4")
            await file.download_to_drive(raw_path)
            clip = mp.VideoFileClip(raw_path).resize(height=512).subclip(0, min(3, clip.duration))
            clip.write_videofile(path, codec='libvpx', audio=False)
            await send_to_sticker_set(update, context, path, animated=True)

        else:
            await update.message.reply_text("Unsupported file type.")

async def send_to_sticker_set(update, context, path, animated=False):
    user = update.message.from_user
    pack_name = f"{user.username}_by_{context.bot.username}"
    emoji = "😎"

    try:
        if animated:
            input_sticker = InputSticker(sticker=InputFile(path), emoji_list=[emoji])
            await context.bot.create_new_sticker_set(user_id=user.id, name=pack_name, title=f"{user.first_name}'s Pack", stickers=[input_sticker], sticker_format='video')
        else:
            await context.bot.add_sticker_to_set(user_id=user.id, name=pack_name, sticker=InputSticker(sticker=InputFile(path), emoji_list=[emoji]))
    except:
        input_sticker = InputSticker(sticker=InputFile(path), emoji_list=[emoji])
        await context.bot.create_new_sticker_set(user_id=user.id, name=pack_name, title=f"{user.first_name}'s Pack", stickers=[input_sticker], sticker_format='static')

    await update.message.reply_text(f"Sticker kanged to [this pack](https://t.me/addstickers/{pack_name})", parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kang", kang))
    app.run_polling()
