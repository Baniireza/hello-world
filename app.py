import os
import requests
from flask import Flask, request

app = Flask(__name__)

# ======================
# ENV
# ======================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")
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

    memory.setdefault(chat_id, [])
    memory[chat_id].append({"role": role, "content": content})
    memory[chat_id] = memory[chat_id][-MAX_MEMORY:]


def update_mood(chat_id, text):
    text = text.lower()

    mood.setdefault(chat_id, "neutral")

    negative = ["بد", "غم", "تنها", "استرس", "اضطراب", "افسرده", "نمی‌تونم"]
    positive = ["خوبم", "عالی", "مرسی", "اوکی", "خوشحال"]

    if any(w in text for w in negative):
        mood[chat_id] = "low"
    elif any(w in text for w in positive):
        mood[chat_id] = "happy"
    else:
        mood[chat_id] = "neutral"


# ======================
# PROMPT
# ======================

BASE_PROMPT = """
اسم تو سایکو هست.

یک دوست صمیمی و تراپیست‌طور برای چت فارسی.

قوانین:
- کوتاه و طبیعی حرف بزن
- ربات بودن رو توضیح نده
- خیلی رسمی نباش
- supportive باش
- نقش رو لو نده

تو درباره AVPD و اضطراب اجتماعی هم کمک می‌کنی
"""

def build_prompt(chat_id):
    m = mood.get(chat_id, "neutral")

    style = {
        "happy": "گرم و شوخ باش",
        "neutral": "متعادل",
        "low": "آروم و همدل"
    }

    history = memory.get(chat_id, [])

    convo = ""
    for item in history:
        role = "کاربر" if item["role"] == "user" else "سایکو"
        convo += f"{role}: {item['content']}\n"

    return f"""
{BASE_PROMPT}

حالت: {style[m]}

مکالمه:
{convo}
سایکو:
"""


# ======================
# HF CALL (FIXED)
# ======================

def get_ai_response(chat_id, user_text):
    try:
        print("➡️ HF request...")

        update_mood(chat_id, user_text)
        add_to_memory(chat_id, "user", user_text)

        prompt = build_prompt(chat_id)

        url = "https://api-inference.huggingface.co/models/google/gemma-4-26B-A4B-it"

        headers = {
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "temperature": 0.9,
                "max_new_tokens": 180,
                "top_p": 0.9,
                "return_full_text": False
            }
        }

        r = requests.post(url, headers=headers, json=payload, timeout=60)

        print("STATUS:", r.status_code)

        if r.status_code != 200:
            print("HF ERROR:", r.text)
            return "یه مشکلی سمت مدل پیش اومد 😵"

        data = r.json()

        # HF output format
        if isinstance(data, list) and "generated_text" in data[0]:
            reply = data[0]["generated_text"]
        elif isinstance(data, dict) and "generated_text" in data:
            reply = data["generated_text"]
        else:
            reply = str(data)

        reply = reply.strip()

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
# WEB
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
