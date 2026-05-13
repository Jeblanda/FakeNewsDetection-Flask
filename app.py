from flask import Flask, render_template, request, redirect, flash, url_for
import os
from google import genai

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ⚠️ BEST PRACTICE (but you hardcoded for now)
GEMINI_API_KEY = "AIzaSyBWa1K0HAFK-vNIv64LlW8mU_P6ZcSMKRM"

client = genai.Client(api_key=GEMINI_API_KEY)


def analyze_with_gemini(news_text):
    prompt = f"""
You are a fact-checker. Determine if this is REAL or FAKE.

TEXT:
{news_text}

Reply format:
LABEL: REAL or FAKE
CONFIDENCE: 0-100
EXPLANATION: one sentence
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print("Gemini error:", e)
        return None


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/check')
def check():
    return render_template('check.html')


@app.route('/result', methods=['POST'])
def result():
    title = request.form.get("title", "").strip()
    article = request.form.get("article", "").strip()

    news_content = f"{title}\n{article}".strip()

    if len(news_content) < 20:
        flash("Please provide more content.")
        return redirect(url_for('check'))

    ai_response = analyze_with_gemini(news_content)

    if not ai_response:
        flash("AI error. Try again.")
        return redirect(url_for('check'))

    label = "REAL" if "LABEL: REAL" in ai_response.upper() else "FAKE"

    display_text = ai_response.replace("LABEL:", "Verdict:") \
                              .replace("CONFIDENCE:", "Confidence:") \
                              .replace("EXPLANATION:", "Reasoning:")

    return render_template("result.html", label=label, reason=display_text)


# ✅ THIS IS REQUIRED FOR LOCAL RUN
if __name__ == "__main__":
    print("🔥 Flask starting...")
    app.run(debug=True)