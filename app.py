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
def home(): return "Gemini Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. الإعدادات (قراءة من راندر) ---
# الكود حيمشي يفتش في راندر عن الاسم ده بالضبط
GEMINI_KEY = os.environ.get('GOOGLE_API_KEY') 
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')
DOWNLOAD_DIR = "downloads"

# تهيئة Gemini
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini Link Active")
    except Exception as e:
        print(f"❌ Gemini Setup Error: {e}")

async def notify_admin(context, message):
    if ADMIN_ID:
        try: await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 تقرير النظم:\n{message}")
        except: pass

def cleanup(file_path):
    try:
        if os.path.exists(file_path): os.remove(file_path)
    except: pass

# --- 3. وظائف البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"أهلاً يا {user_name}! 👋\nأنا مساعدك الذكي. اسألني أي سؤال أو أرسل ملف PDF.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("عذراً، لم أستطع الوصول لعقلي الإلكتروني (Gemini). تأكد من إعدادات المفتاح.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.lower().endswith('.pdf'): return
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    pdf_path = os.path.join(DOWNLOAD_DIR, doc.file_name)
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(pdf_path)
    context.user_data['current_file'] = pdf_path

    keyboard = [[InlineKeyboardButton("ترجمة (Gemini) 🇸🇩", callback_data='translate')],
                [InlineKeyboardButton("تحويل لـ Word 📝", callback_data='word')]]
    await update.message.reply_text(f"تم استلام {doc.file_name}. اختر العملية:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pdf_path = context.user_data.get('current_file')
    if not pdf_path: return

    if query.data == 'translate':
        await query.edit_message_text("🔄 جاري الترجمة الاحترافية...")
        try:
            doc = fitz.open(pdf_path)
            text = "".join([page.get_text() for page in doc])
            response = model.generate_content(f"ترجم النص التالي للعربية بوضوح: {text[:2000]}")
            await query.message.reply_text(response.text)
        except Exception as e:
            await query.message.reply_text(f"حدث خطأ: {str(e)}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    if not TOKEN: return
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # أهم سطر لمنع التعارض (Conflict Error)
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
