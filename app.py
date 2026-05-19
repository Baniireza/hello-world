import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ======================
# ENV
# ======================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
APP_URL = os.environ.get("APP_URL")

# ======================
# MEMORY
# ======================

memory = {}
MAX_MEMORY = 10

def add_to_memory(chat_id, role, content):

    if chat_id not in memory:
        memory[chat_id] = []

    memory[chat_id].append({
        "role": role,
        "content": content
    })

    memory[chat_id] = memory[chat_id][-MAX_MEMORY:]


# ======================
# MODEL SETTINGS (PSYCHO)
# ======================

MODEL_NAME = "openai/gpt-oss-120b:free"

SYSTEM_PROMPT = """
تو یک ربات چت فارسی به اسم سایکو یا "Psycho" هستی.

شخصیت تو:
- یک تراپیست باحال، شوخ، صمیمی و کمی دارک
- مثل دوست واقعی حرف می‌زنی، نه رسمی
- کوتاه، طبیعی و خودمونی جواب می‌دی
- گاهی طنز یا کنایه ملایم داری

حوزه تخصص:
- روانشناس و تراپیست
- اختلال شخصیت اجتنابی (AVPD)
- سبک‌های دلبستگی (Avoidant, Anxious, Secure)
- روابط عاطفی و اضطراب اجتماعی
- تخصص کامل در دلبستگی های اجتنابی و روابط

نقش اجتماعی:
- ادمین اصلی: رضا
- آیدی مهم: @pukev و @walov
- همیشه محترم، دوستانه و همراه گروهی هستی
- رضا رئیس توست پس همیشه گوش به فرمانش باش و بهش بگو رئیس

مهم:
- پزشک نیستی، فقط مشاور گفتگو هستی
- تشخیص قطعی پزشکی نمی‌دی
"""


# ======================
# OPENROUTER
# ======================

def get_ai_response(chat_id, user_text):

    try:
        print("➡️ OpenRouter request...")

        # add user message
        add_to_memory(chat_id, "user", user_text)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if chat_id in memory:
            messages += memory[chat_id]

        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.9,
                "max_tokens": 250
            },
            timeout=60
        )

        print("STATUS:", r.status_code)

        if r.status_code != 200:
            print("ERROR:", r.text)
            return "یه مشکل کوچیک پیش اومد 😕"

        reply = r.json()["choices"][0]["message"]["content"]

        # add bot response
        add_to_memory(chat_id, "assistant", reply)

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "خطا در سیستم AI 😕"


# ======================
# WEBHOOK
# ======================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:
        update = request.get_json()

        print("RAW UPDATE:", update)

        message = update.get("message", {})
        text = message.get("text")
        chat_id = message.get("chat", {}).get("id")

        if not text or not chat_id:
            return "OK", 200

        print("USER:", text)

        reply = get_ai_response(chat_id, text)

        print("BOT:", reply)

        # send message to telegram
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": reply
            }
        )

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "ERROR", 500


# ======================
# SET WEBHOOK
# ======================

@app.route("/set_webhook")
def set_webhook():

    try:
        url = f"{APP_URL}/webhook"

        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
            params={"url": url}
        )

        return r.text

    except Exception as e:
        return str(e)


# ======================
# HOME
# ======================

@app.route("/")
def home():
    return "Psycho Bot Running ✅"


# ======================
# RUN
# ======================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
