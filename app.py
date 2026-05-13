from flask import Flask, render_template, request, redirect, flash, url_for
import os
from google import genai # Ensure you use the right library in requirements

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ✅ CORRECT: We look for the VARIABLE NAME, not the key itself
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Check if key exists
if not GEMINI_API_KEY:
    print("❌ Missing GEMINI_API_KEY environment variable")
    # For local testing ONLY, you can fallback: 
    # GEMINI_API_KEY = "your_actual_key_here"

client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_with_gemini(news_text):
    prompt = f"Fact-check this: {news_text}. Reply with LABEL: REAL/FAKE, CONFIDENCE, and EXPLANATION."
    
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash", # ✅ Changed from 2.5 to 1.5
            contents=prompt
        )
        return response.text
    except Exception as e:
        print("Gemini error:", e)
        return None

# ... rest of your routes ...

# ✅ For Vercel, the app object needs to be available
app = app


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

    return render_template(
        "result.html",
        label=label,
        reason=ai_response
    )


# ❌ DO NOT USE app.run() ON VERCEL
app = app