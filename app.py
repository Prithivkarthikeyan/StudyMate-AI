from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader
from google import genai
import os
from dotenv import load_dotenv

# Load hidden variables from .env file
load_dotenv()

app = Flask(__name__)

# Fetch the API key securely
api_key = os.getenv("GEMINI_API_KEY")

# 🔥 IDHU DHAAN NAMMA TEST LINE 🔥
print("🔥 ENODA API KEY:", api_key) 

client = genai.Client(api_key=api_key)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():

    pdf = request.files["pdf_file"]

    if not pdf:
        return "No PDF selected"

    reader = PdfReader(pdf)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    prompt = f"""
    Generate 10 flashcards from the following PDF. 
    Strictly follow this format for each card, with no extra text:
    Q: [Question]
    A: [Answer]

    Content:
    {text}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        raw_text = response.text
        flashcards = []
        parts = raw_text.split('Q:')
        
        for part in parts[1:]:
            if 'A:' in part:
                q, a = part.split('A:', 1)
                flashcards.append({'q': q.strip(), 'a': a.strip()})

        return render_template("flashcards.html", flashcards=flashcards, pdf_text=text)

    except Exception as e:
        return f"Error:<br><br>{e}"

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = data.get("question")
    pdf_text = data.get("pdf_text")

    if not question or not pdf_text:
        return jsonify({"error": "Missing data"}), 400

    prompt = f"""
    You are a helpful AI study assistant. Answer the user's question based ONLY on the following PDF text.
    If the answer is not in the text, say "I couldn't find the answer in the uploaded PDF."

    PDF Text:
    {pdf_text}

    Question:
    {question}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return jsonify({"answer": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)