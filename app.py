import os
import threading
import fitz
import google.generativeai as genai
from flask import Flask
from gtts import gTTS
from pdf2docx import Converter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- 1. إعداد Flask (عشان السيرفر يفضل صاحي) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Direct Key Mode is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. البيانات المباشرة (Direct Configuration) ---
# وضعنا كل شيء هنا مباشرة للتجربة النهائية
GEMINI_KEY = "AIzaSyCO5SisFRfssgoyH0tjfoAtBjfalm0OP6U"
BOT_TOKEN = "8647878698:AAEbsrfsgydzS0opvQkymNeArAm7JV3VlK8"
MY_ADMIN_ID = "8168754101"
DOWNLOAD_DIR = "downloads"

# تهيئة Gemini
try:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Gemini Configured Successfully!")
except Exception as e:
    print(f"❌ Gemini Error: {e}")

async def notify_admin(context, message):
    try:
        await context.bot.send_message(chat_id=MY_ADMIN_ID, text=f"📢 تقرير المراقبة:\n{message}")
    except: pass

# --- 3. وظائف البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"أهلاً {user_name}! 👋\nتم تشغيل البوت بنظام المفاتيح المباشرة.\nأنا جاهز الآن، جرب اسألني أي سؤال.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
        # إشعار لك في الخاص
        await notify_admin(context, f"المستخدم {update.message.from_user.first_name} سأل: {user_text}")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ في Gemini: {str(e)}")

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
    await update.message.reply_text(f"استلمت {doc.file_name}. ماذا نفعل؟", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pdf_path = context.user_data.get('current_file')
    if not pdf_path: return

    if query.data == 'translate':
        await query.edit_message_text("🔄 جاري الترجمة...")
        try:
            doc = fitz.open(pdf_path)
            text = "".join([page.get_text() for page in doc])
            response = model.generate_content(f"ترجم هذا النص الطبي: {text[:1500]}")
            await query.message.reply_text(response.text)
        except Exception as e:
            await query.message.reply_text(f"خطأ: {str(e)}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    # هنا استخدمنا BOT_TOKEN المكتوب فوق مباشرة
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # مسح التراكمات القديمة للرسائل
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
