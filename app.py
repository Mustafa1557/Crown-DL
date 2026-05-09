import os
import threading
import fitz
import google.generativeai as genai
from flask import Flask
from gtts import gTTS
from pdf2docx import Converter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- 1. إعداد Flask ---
app = Flask(__name__)
@app.route('/')
def home(): return "Gemini Test Mode is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. الإعدادات (تجربة المفتاح المباشر) ---
# حطينا المفتاح هنا مباشرة للتجربة فقط
GEMINI_KEY = "AIzaSyCO5SisFRfssgoyH0tjfoAtBjfalm0OP6U"
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
DOWNLOAD_DIR = "downloads"

# تهيئة Gemini بالمفتاح المباشر
try:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini Configured Directly")
except Exception as e:
    print(f"❌ Gemini Config Error: {e}")

async def notify_admin(context, message):
    if ADMIN_ID:
        try: await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 مراقبة التجربة:\n{message}")
        except: pass

def cleanup(file_path):
    try:
        if os.path.exists(file_path): os.remove(file_path)
    except: pass

# --- 3. وظائف البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"مرحباً {user_name}! نحن الآن في وضع اختبار المفتاح المباشر.\nاسألني أي سؤال لنرى هل سيعمل Gemini.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # المحاولة المباشرة للتحدث مع Gemini
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        # لو فشل حتى والمفتاح مكتوب، حيطبع لينا نوع الخطأ بالضبط
        await update.message.reply_text(f"الخطأ الفني هو: {str(e)}")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.lower().endswith('.pdf'): return
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    pdf_path = os.path.join(DOWNLOAD_DIR, doc.file_name)
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(pdf_path)
    context.user_data['current_file'] = pdf_path

    keyboard = [[InlineKeyboardButton("ترجمة (Gemini) 🇸🇩", callback_data='translate')],
                [InlineKeyboardButton("تحويل Word 📝", callback_data='word')]]
    await update.message.reply_text(f"الملف {doc.file_name} جاهز للاختبار.", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pdf_path = context.user_data.get('current_file')
    if not pdf_path: return

    if query.data == 'translate':
        await query.edit_message_text("🔄 جاري تجربة الترجمة المباشرة...")
        try:
            doc = fitz.open(pdf_path)
            text = "".join([page.get_text() for page in doc])
            response = model.generate_content(f"ترجم هذا النص الطبي: {text[:1000]}")
            await query.message.reply_text(response.text)
        except Exception as e:
            await query.message.reply_text(f"خطأ ترجمة: {str(e)}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    if not TOKEN: return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()

