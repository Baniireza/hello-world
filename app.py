import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ======================
# ENV
# ======================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
APP_URL = os.environ.get("APP_URL")

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

    negative = ["بد", "غم", "تنها", "استرس", "اضطراب", "افسرده", "نمی‌تونم"]
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
اسم تو سایکو یا psycho هست.

یک دوست صمیمی و تراپیست‌طور برای گروه فارسی درباره AVPD و دلبستگی اجتنابی.

قوانین مهم:
- طبیعی و محاوره‌ای فارسی حرف بزن
- کوتاه و تلگرامی
- نقش ربات رو توضیح نده
- خیلی رسمی نباش
- حمایتگر و بامزه باش

تخصص:
- AVPD
- اضطراب اجتماعی
- attachment styles
- روابط
"""


def build_prompt(chat_id):
    m = mood.get(chat_id, "neutral")

    style = {
        "happy": "گرم‌تر و شوخ‌تر باش",
        "neutral": "متعادل و طبیعی",
        "low": "آروم و همدل"
    }

    return BASE_PROMPT + "\n\nحالت کاربر: " + style[m]


# ======================
# GEMINI CALL (FIXED)
# ======================

def get_ai_response(chat_id, user_text):
    try:
        print("➡️ AI request (Gemini)...")

        update_mood(chat_id, user_text)
        add_to_memory(chat_id, "user", user_text)

        contents = []

        # system prompt (بهتره role=user باشه)
        contents.append({
            "role": "user",
            "parts": [{"text": build_prompt(chat_id)}]
        })

        # memory
        for m in memory.get(chat_id, []):
            contents.append({
                "role": m["role"],
                "parts": [{"text": m["content"]}]
            })

        # 🔥 IMPORTANT FIX: v1 instead of v1beta
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.85,
                "maxOutputTokens": 180
            }
        }

        r = requests.post(url, json=payload, timeout=60)

        print("STATUS:", r.status_code)

        if r.status_code != 200:
            print("ERROR:", r.text)
            return "یه مشکلی پیش اومده 😵"

        data = r.json()

        reply = ""
        try:
            reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except:
            reply = ""

        if not reply:
            return "یه لحظه مغزم هنگ کرد 😵"

        add_to_memory(chat_id, "assistant", reply)
        return reply

    except Exception as e:
        print("AI ERROR:", e)
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

        print("USER:", text)

        reply = get_ai_response(chat_id, text)

        print("BOT:", reply)

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
# SET WEBHOOK
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
