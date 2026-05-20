import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ======================
# ENV
# ======================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_API_KEY = os.environ.get("HF_API_KEY")
APP_URL = os.environ.get("APP_URL")

HF_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

# ======================
# MEMORY + MOOD
# ======================

memory = {}
mood = {}
MAX_MEMORY = 12


def add_to_memory(chat_id, role, content):
    if not content:
        return

    if chat_id not in memory:
        memory[chat_id] = []

    memory[chat_id].append({"role": role, "content": content})
    memory[chat_id] = memory[chat_id][-MAX_MEMORY:]


def update_mood(chat_id, text):
    text = text.lower()

    if chat_id not in mood:
        mood[chat_id] = "neutral"

    negative = ["بد", "غم", "تنها", "افسرده", "استرس", "اضطراب", "نمی‌تونم"]
    positive = ["خوبم", "عالی", "مرسی", "اوکی", "خوشحال"]

    if any(w in text for w in negative):
        mood[chat_id] = "low"
    elif any(w in text for w in positive):
        mood[chat_id] = "happy"
    else:
        mood[chat_id] = "neutral"


# ======================
# SYSTEM PROMPT
# ======================

BASE_PROMPT = """
تو سایکو هستی.

دوست صمیمی و تراپیست‌طور درباره AVPD و دلبستگی اجتنابی.

قوانین:
- کوتاه و طبیعی حرف بزن
- خودت رو ربات معرفی نکن
- تحلیل سنگین نده مگر لازم باشه
- خیلی انسانی و دوستانه رفتار کن

شخصیت:
- بامزه
- کمی دارک
- supportive

تو روانشناسی بلدی ولی:
- تشخیص پزشکی نمی‌دی
"""


def build_prompt(chat_id):
    m = mood.get(chat_id, "neutral")

    style = {
        "happy": "گرم‌تر و شوخ‌تر باش",
        "neutral": "متعادل و طبیعی باش",
        "low": "آروم و همدل باش"
    }

    return BASE_PROMPT + "\nحالت کاربر: " + style[m]


# ======================
# AI CALL (HF)
# ======================

def get_ai_response(chat_id, text):

    try:
        update_mood(chat_id, text)
        add_to_memory(chat_id, "user", text)

        messages = [{"role": "system", "content": build_prompt(chat_id)}]
        messages += memory.get(chat_id, [])

        r = requests.post(
            "https://api-inference.huggingface.co/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {HF_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": HF_MODEL,
                "messages": messages,
                "temperature": 0.8,
                "max_tokens": 180
            },
            timeout=60
        )

        if r.status_code != 200:
            print("HF ERROR:", r.text)
            return "یه مشکلی پیش اومد 😵"

        data = r.json()

        reply = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        ).strip()

        if not reply:
            return "یه لحظه مغزم هنگ کرد 😵"

        add_to_memory(chat_id, "assistant", reply)
        return reply

    except Exception as e:
        print("ERROR:", e)
        return "مغزم قاط زد 😭"


# ======================
# WEBHOOK
# ======================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:
        update = request.get_json()
        message = update.get("message", {})

        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")
        chat_type = message.get("chat", {}).get("type", "")

        if not text or not chat_id:
            return "OK", 200

        text_lower = text.lower()

        should_reply = chat_type == "private"

        if not should_reply:
            triggers = ["psycho", "سایکو", "@psychoteraphist_bot"]
            should_reply = any(t in text_lower for t in triggers)

        if not should_reply:
            return "OK", 200

        reply = get_ai_response(chat_id, text)

        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": reply,
                "reply_to_message_id": message.get("message_id")
            }
        )

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "ERROR", 500


# ======================
# WEB ROUTES
# ======================

@app.route("/set_webhook")
def set_webhook():
    url = f"{APP_URL}/webhook"

    r = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
        params={"url": url}
    )

    return r.text


@app.route("/ping")
def ping():
    return "alive"


@app.route("/")
def home():
    return "Psycho Bot Running ✅"


# ======================
# RUN
# ======================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
