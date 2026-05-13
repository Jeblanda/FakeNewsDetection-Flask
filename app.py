from flask import Flask, render_template, request, redirect, flash, url_for
import os
import re
from PIL import Image
import pytesseract
from google import genai 

app = Flask(__name__)
app.secret_key = 'your_secret_key' 

# --- Gemini Configuration ---
# ⚠️ SECURITY: Use os.environ for keys in production!
GEMINI_API_KEY = "AIzaSyAXwwDlk2vPr8l3n1nQbvuEWFC-wP8VZUQ"

client = genai.Client(api_key=GEMINI_API_KEY)

# --- Tesseract Path (Windows) ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Helper Functions ---

def extract_text_from_image(image_file):
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"❌ OCR Error: {e}")
        return ""

def analyze_with_gemini(news_text):
    """Uses the 2026 stable gemini-2.5-flash model to avoid 429 errors."""
    prompt = f"""
    You are a professional fact-checker. Analyze the following news content:
    TEXT: "{news_text}"
    
    Determine if this news is REAL or FAKE. 
    Provide your response in this exact format:
    LABEL: [REAL or FAKE]
    CONFIDENCE: [Number 0-100]
    EXPLANATION: [One sentence explaining why]
    """
    try:
        # ✅ UPDATED MODEL: Using 2.5-flash which has active quota
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        # This catches the 429 error and prints a cleaner message
        if "429" in str(e):
            print("❌ Quota Error: You hit the rate limit. Wait 60 seconds.")
        else:
            print(f"❌ Gemini Error: {e}")
        return None

# --- Routes ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/check')
def check():
    return render_template('check.html')

@app.route('/result', methods=['POST'])
def result():
    news_content = ""
    
    # 1. Handle Input (Image or Text)
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        news_content = extract_text_from_image(file)
        if not news_content:
            flash("OCR failed to read the image. Please try a clearer text-based image.")
            return redirect(url_for('check'))
    else:
        title = request.form.get("title", "").strip()
        article = request.form.get("article", "").strip()
        news_content = f"{title}\n{article}".strip()

    # 2. Minimum Length Check
    if len(news_content) < 20:
        flash("Please provide more news content (at least 20 characters) for analysis.")
        return redirect(url_for('check'))

    try:
        # 3. AI Analysis
        ai_response = analyze_with_gemini(news_content)
        
        if not ai_response:
            flash("The AI is currently 'out of office' (Rate Limit). Please wait a minute and try again.")
            return redirect(url_for('check'))

        # 4. Parse Results
        # Simple regex/string check to handle formatting variations
        label = "REAL" if "LABEL: REAL" in ai_response.upper() else "FAKE"
        
        # Cleanup for the UI
        display_text = ai_response.replace("LABEL:", "Verdict:").replace("CONFIDENCE:", "Confidence:").replace("EXPLANATION:", "Reasoning:")

        return render_template("result.html", label=label, reason=display_text)

    except Exception as e:
        print(f"Error in result route: {e}")
        flash("An unexpected error occurred.")
        return redirect(url_for('check'))

if __name__ == "__main__":
    app.run(debug=True)