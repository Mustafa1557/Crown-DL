import os
import threading
import fitz
import google.generativeai as genai
from flask import Flask
from gtts import gTTS
from pdf2docx import Converter
from PyPDF2 import PdfMerger
from deep_translator import GoogleTranslator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- 1. إعداد Flask ---
app = Flask(__name__)
@app.route('/')
def home(): return "Gemini Medical Bot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. سحب الإعدادات من Environment Variables ---
GEMINI_KEY = os.environ.get('GOOGLE_API_KEY')
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID') # سيسحب الرقم من راندر
DOWNLOAD_DIR = "downloads"

# إعداد Gemini
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

async def notify_admin(context, message):
    if ADMIN_ID:
        try: await context.bot.send_message(chat_id=ADMIN_ID, text=f"📢 مراقبة:\n{message}")
        except: pass

def cleanup(file_path):
    try:
        if os.path.exists(file_path): os.remove(file_path)
    except: pass

# --- 3. وظائف البوت الذكي ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    await notify_admin(context, f"مستخدم بدأ البوت: {user_name}")
    await update.message.reply_text(f"أهلاً يا {user_name}! 👋\nأنا بوت Gemini الخاص بك.\n- اسألني أي سؤال طبي أو برمجبي.\n- أرسل PDF للترجمة أو التحويل.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
        await notify_admin(context, f"💬 {update.message.from_user.first_name} سأل: {user_text}")
    except Exception as e:
        await update.message.reply_text("عذراً، تأكد من ضبط مفتاح Gemini في الإعدادات.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.lower().endswith('.pdf'): return
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    pdf_path = os.path.join(DOWNLOAD_DIR, doc.file_name)
    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(pdf_path)
    context.user_data['current_file'] = pdf_path

    keyboard = [[InlineKeyboardButton("ترجمة (Gemini) 🇸🇩", callback_data='translate')],
                [InlineKeyboardButton("تحويل Word 📝", callback_data='word')],
                [InlineKeyboardButton("صوت 🎙️", callback_data='audio')]]
    await update.message.reply_text(f"ملف {doc.file_name} جاهز. ماذا نفعل؟", reply_markup=InlineKeyboardMarkup(keyboard))

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
            prompt = f"ترجم النص التالي للعربية بوضوح واحترافية: {text[:2500]}"
            response = model.generate_content(prompt)
            await query.message.reply_text(response.text)
        except: await query.message.reply_text("خطأ في الترجمة.")

    elif query.data == 'word':
        await query.edit_message_text("🔄 جاري التحويل...")
        docx_path = pdf_path.replace('.pdf', '.docx')
        cv = Converter(pdf_path); cv.convert(docx_path); cv.close()
        await query.message.reply_document(document=open(docx_path, 'rb'))
        cleanup(docx_path)

    elif query.data == 'audio':
        await query.edit_message_text("🎧 جاري التحويل لصوت...")
        doc = fitz.open(pdf_path)
        text = "".join([page.get_text() for page in doc])
        tts = gTTS(text=text[:2000], lang='en')
        audio_path = pdf_path.replace('.pdf', '.mp3')
        tts.save(audio_path)
        await query.message.reply_audio(audio=open(audio_path, 'rb'))
        cleanup(audio_path)

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
