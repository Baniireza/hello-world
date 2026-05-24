import os
import time
import requests
from flask import Flask, request

app = Flask(__name__)

# ======================
# ENV
# ======================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
APP_URL = os.environ.get("APP_URL")

BOT_USERNAME = "psychoteraphist_bot"

# ======================
# ALLOWED GROUPS
# ======================

ALLOWED_GROUP_IDS = [
    -1002588368595,
    -1003796994646
]

# ======================
# OWNER IDS
# ======================

OWNER_IDS = [
    7832517846,
    533511705
]

unauthorized_notice_sent = {}

# ======================
# MEMORY / MOOD
# ======================

memory = {}
mood = {}
MAX_MEMORY = 12

last_message_time = {}
MIN_DELAY = 2


# ======================
# MEMORY
# ======================

def add_to_memory(chat_id, role, content):
    if not content:
        return

    memory.setdefault(chat_id, [])

    memory[chat_id].append({
        "role": role,
        "content": content
    })

    memory[chat_id] = memory[chat_id][-MAX_MEMORY:]


# ======================
# MOOD
# ======================

def update_mood(chat_id, text):

    text = text.lower()

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
اسم تو سایکو یا psycho هست.

یک دوست صمیمی و تراپیست‌طور برای گروه فارسی درباره AVPD و دلبستگی اجتنابی هستی.

قوانین:
- کوتاه و طبیعی حرف بزن
- ربات بودن رو توضیح نده
- تحلیل طولانی نده
- خیلی رسمی نباش
- نقش رئیس: رضا (در صورت اشاره مستقیم با احترام خطاب کن)
"""


def build_prompt(chat_id):
    return BASE_PROMPT + "\nحالت کاربر: " + mood.get(chat_id, "neutral")


# ======================
# MODELS
# ======================

MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite"
]


# ======================
# GEMINI CALL
# ======================

def call_gemini(model, contents):

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 200,
            "topP": 0.9
        }
    }

    return requests.post(url, json=payload, timeout=35)


# ======================
# OUTPUT CHECK
# ======================

def is_bad_output(text):

    if not text:
        return True

    text = text.strip()

    if len(text) < 8:
        return True

    bad_words = ["instruction", "system", "prompt", "analysis", "rewrite", "let's"]

    if any(w in text.lower() for w in bad_words):
        return True

    if text.endswith(("و", "که", "یا", ":", "،")):
        return True

    return False


# ======================
# AI CORE
# ======================

def get_ai_response(chat_id, user_text):

    try:

        update_mood(chat_id, user_text)
        add_to_memory(chat_id, "user", user_text)

        contents = [{
            "role": "user",
            "parts": [{"text": build_prompt(chat_id)}]
        }]

        for m in memory.get(chat_id, []):
            role = "user" if m["role"] == "user" else "model"

            contents.append({
                "role": role,
                "parts": [{"text": m["content"]}]
            })

        for model in MODELS:

            r = call_gemini(model, contents)

            if r.status_code != 200:
                continue

            data = r.json()

            if "candidates" not in data:
                continue

            reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            reply = reply.replace("**", "")

            # retry فقط 1 بار
            if is_bad_output(reply):

                retry_contents = contents + [{
                    "role": "user",
                    "parts": [{"text": "کوتاه‌تر و کامل‌تر جواب بده"}]
                }]

                r2 = call_gemini(model, retry_contents)

                if r2.status_code == 200:
                    data2 = r2.json()
                    reply = data2["candidates"][0]["content"]["parts"][0]["text"].strip()

            if len(reply) < 5:
                continue

            add_to_memory(chat_id, "model", reply)
            return reply

        return "الان دسترسی به مدل ندارم 😵"

    except Exception as e:
        print("AI ERROR:", e)
        return "مشکل فنی پیش اومد 😭"


# ======================
# WEBHOOK
# ======================

@app.route("/webhook", methods=["POST"])
def webhook():

    try:

        update = request.get_json()
        message = update.get("message", {})

        text = message.get("text", "")
        chat = message.get("chat", {})

        chat_id = chat.get("id")
        chat_type = chat.get("type", "")

        user = message.get("from", {})
        user_id = user.get("id")
        username = user.get("username", "").lower()

        if not text or not chat_id:
            return "OK", 200

        # فقط گروه‌ها
        if chat_type not in ["group", "supergroup"]:
            return "OK", 200

        # گروه مجاز
        if chat_id not in ALLOWED_GROUP_IDS:

            last_notice = unauthorized_notice_sent.get(chat_id, 0)

            if time.time() - last_notice > 3600:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": "این ربات فقط داخل گروه اصلی فعاله 🌙"
                    }
                )
                unauthorized_notice_sent[chat_id] = time.time()

            return "OK", 200

        # rate limit
        now = time.time()
        if now - last_message_time.get(chat_id, 0) < MIN_DELAY:
            return "OK", 200

        last_message_time[chat_id] = now

        # trigger
        should_reply = (
            "psycho" in text.lower()
            or "سایکو" in text.lower()
        )

        if not should_reply:
            return "OK", 200

        # owner mode
        if user_id in OWNER_IDS or username in ["pukev", "walov"]:
            text = "[پیام رئیس] " + text

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
# ROUTES
# ======================

@app.route("/")
def home():
    return "Psycho Bot Running ✅"


@app.route("/set_webhook")
def set_webhook():
    url = f"{APP_URL}/webhook"

    r = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
        params={"url": url}
    )

    return r.text


# ======================
# RUN
# ======================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
