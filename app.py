import os
import threading
import google.generativeai as genai
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home(): return "AI Bot is fixing itself!"

# --- البيانات المباشرة ---
GEMINI_KEY = "AIzaSyCO5SisFRfssgoyH0tjfoAtBjfalm0OP6U"
BOT_TOKEN = "8647878698:AAEbsrfsgydzS0opvQkymNeArAm7JV3VlK8"

genai.configure(api_key=GEMINI_KEY)

# دالة لاختيار الموديل المتاح تلقائياً
def get_working_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except:
        return genai.GenerativeModel('gemini-1.5-flash') # كخيار أخير

model = get_working_model()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم تحديث النظام تلقائياً للنسخة المتوافقة. جرب الآن!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"خطأ تقني: {str(e)}")

def main():
    port = int(os.environ.get("PORT", 10000))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
