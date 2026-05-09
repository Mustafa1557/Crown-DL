import os
import threading
import google.generativeai as genai
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- 1. إعداد الـ Web Server (عشان راندر ما يقفل البوت) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Security Mode: ACTIVE"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- 2. سحب البيانات بالأسماء (الترتيب اللي في راندر) ---
# الأسماء دي لازم تكون هي نفسها الـ Key في الـ Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
GEMINI_KEY = os.environ.get('GOOGLE_API_KEY')
ADMIN_ID = os.environ.get('ADMIN_ID')

# --- 3. تهيئة ذكاء Gemini (ضبط الشخصية والردود) ---
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    # هنا بنحدد ليه "الكتلوج" اللي يمشي عليه عشان إجاباته تعجبك
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash-latest',
        system_instruction=(
            "أنت 'دحيح'، مساعد ذكي لطلاب العلوم والطب. "
            "قواعدك: 1. الإجابة مختصرة جداً وفي نقاط. "
            "2. استخدم الرموز التعبيرية (Emoji) لتسهيل القراءة. "
            "3. ركز على المعلومة المهمة للامتحان فقط. "
            "4. إذا سألك طالب سوداني، كن قريباً من لهجته في الترحيب."
        )
    )

# --- 4. معالجة الرسائل والردود ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.message.from_user.first_name
    await update.message.reply_text(f"يا هلا بـ {user_name}! 🔥\nالبوت شغال بأعلى نظام أمان حالياً. أرمي لي أي سؤال في المنهج!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    # إشعار "يكتب الآن" عشان تحس بفاعلية البوت
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = model.generate_content(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        # رسالة خطأ دبلوماسية
        await update.message.reply_text("حصل ضغط شوية على السيرفر، جرب ترسل السؤال تاني بعد ثواني.")

# --- 5. تشغيل المحرك الأساسي ---
def main():
    # تشغيل Flask في خيط منفصل (Thread)
    threading.Thread(target=run_flask, daemon=True).start()
    
    if not BOT_TOKEN:
        print("❌ خطأ: لم يتم العثور على التوكن في إعدادات راندر!")
        return

    # بناء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # الروابط (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # أهم سطر لمنع التعارض وتنظيف الرسايل القديمة
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
