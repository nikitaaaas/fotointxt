import os
import logging
from PIL import Image
import pytesseract
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота 
BOT_TOKEN = os.getenv('7635139431:AAGSZYwT40RXU069lSH7WgpEdyQVhlCxxHE')

# Стани бота
(
    STATE_START,
    STATE_CHOOSE_LANG,
    STATE_WAIT_PHOTO
) = range(3)

# Клавіатура для вибору мови
LANG_KEYBOARD = ReplyKeyboardMarkup(
    [['English', 'Українська']],
    resize_keyboard=True,
    one_time_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка команди /start"""
    await update.message.reply_text(
        "Привіт! Обери, якою мовою у тебе текст на фото:",
        reply_markup=LANG_KEYBOARD
    )
    return STATE_CHOOSE_LANG

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка вибору мови"""
    text = update.message.text
    if text not in ['English', 'Українська']:
        await update.message.reply_text(
            "Будь ласка, оберіть мову з клавіатури:",
            reply_markup=LANG_KEYBOARD
        )
        return STATE_CHOOSE_LANG
    
    context.user_data['language'] = 'eng' if text == 'English' else 'ukr'
    await update.message.reply_text(
        "Тепер відправ мені фото з текстом:",
        reply_markup=None  # Видаляємо клавіатуру
    )
    return STATE_WAIT_PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка отриманого фото"""
    if 'language' not in context.user_data:
        await update.message.reply_text(
            "Спочатку оберіть мову. Напишіть /start",
            reply_markup=None
        )
        return STATE_START
    
    user = update.message.from_user
    logger.info(f"User {user.id} sent a photo")
    
    # Отримуємо фото
    photo_file = await update.message.photo[-1].get_file()
    photo_path = f"temp_photo_{user.id}.jpg"
    await photo_file.download_to_drive(photo_path)
    
    try:
        # Відкриваємо зображення і розпізнаємо текст
        image = Image.open(photo_path)
        text = pytesseract.image_to_string(
            image,
            lang=context.user_data['language']
        )
        
        if text.strip():
            await update.message.reply_text(f"Розпізнаний текст:\n\n{text}")
        else:
            await update.message.reply_text("Не вдалося розпізнати текст на фото.")
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("Сталася помилка при обробці фото.")
    finally:
        # Видаляємо тимчасовий файл
        if os.path.exists(photo_path):
            os.remove(photo_path)
    
    return STATE_WAIT_PHOTO

def main():
    # Створюємо додаток і передаємо токен
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        choose_language
    ))
    application.add_handler(MessageHandler(
        filters.PHOTO,
        handle_photo
    ))
    
    # Запускаємо бота
    application.run_polling()

if __name__ == '__main__':
    main()
