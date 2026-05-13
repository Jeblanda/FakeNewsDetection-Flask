from flask import Flask, render_template, request, redirect, flash, url_for
import os
from google import genai

app = Flask(__name__)
app.secret_key = 'your_secret_key_123'

# --- CONFIGURATION ---
# IMPORTANT: Delete your old key and get a new one from AI Studio.
# This one is hardcoded for local testing.
GEMINI_API_KEY = "AIzaSyCDTW31PNdUcsdVRRcFEUQkfRquxFZpKLs"

# Initialize Client with stable v1 API version
try:
    client = genai.Client(
        api_key=GEMINI_API_KEY,
        http_options={'api_version': 'v1'}
    )
except Exception as e:
    print(f"Client Initialization Error: {e}")

def analyze_with_gemini(news_text):
    # 2026 Standard: Use gemini-2.5-flash or gemini-3-flash
    model_id = "gemini-2.5-flash" 
    
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
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        
        if response and response.text:
            return response.text
        else:
            print("Empty response - possible safety block.")
            return None
            
    except Exception as e:
        print(f"--- GEMINI API ERROR ---\n{e}\n-------------------------")
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
        flash("AI error. Check your terminal for the 404/403 details.")
        return redirect(url_for('check'))

    label = "REAL" if "LABEL: REAL" in ai_response.upper() else "FAKE"
    
    display_text = ai_response.replace("LABEL:", "Verdict:") \
                             .replace("CONFIDENCE:", "Confidence:") \
                             .replace("EXPLANATION:", "Reasoning:")

    return render_template("result.html", label=label, reason=display_text)

if __name__ == "__main__":
    app.run(debug=True)