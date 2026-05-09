import os
import threading
import fitz
import google.generativeai as genai
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

app = Flask(__name__)
@app.route('/')
def home(): return "Gemini Fixed Mode is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- البيانات المباشرة ---
GEMINI_KEY = "AIzaSyCO5SisFRfssgoyH0tjfoAtBjfalm0OP6U"
BOT_TOKEN = "8647878698:AAEbsrfsgydzS0opvQkymNeArAm7JV3VlK8"
MY_ADMIN_ID = "8168754101"

# تهيئة Gemini (تعديل اسم الموديل)
try:
    genai.configure(api_key=GEMINI_KEY)
    # جربنا هنا gemini-pro لأنه أحياناً 1.5 flash بيتطلب تحديث مكتبات معين
    model = genai.GenerativeModel('gemini-pro') 
    print("✅ Gemini Configured with Pro Model")
except Exception as e:
    print(f"❌ Gemini Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"أهلاً {update.message.from_user.first_name}! تم تحديث النظام لإصدار Pro المستقر. جرب الآن.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        # لو فشل Pro، حنجرب نخليه يختار أول موديل متاح تلقائياً
        await update.message.reply_text(f"عذراً، ما زال هناك تعارض في الإصدار. التفاصيل: {str(e)}")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
