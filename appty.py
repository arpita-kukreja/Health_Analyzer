from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import PyPDF2
import pytesseract
from PIL import Image
import os
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# Configure Tesseract (Update path as needed)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

conversation_history = []

def extract_text(file):
    try:
        if file.filename.lower().endswith('.pdf'):
            pdf = PyPDF2.PdfReader(file)
            text = [page.extract_text() for page in pdf.pages]
            return "\n".join(text)
        else:
            img = Image.open(file.stream)
            return pytesseract.image_to_string(img)
    except Exception as e:
        return f"Error processing file: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global conversation_history
    conversation_history = []
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    extracted_text = extract_text(file)
    
    if "Error" in extracted_text:
        return jsonify({'error': extracted_text}), 500
    
    try:
        prompt ="""🏥 **BunnyBot Health Report Analysis** 🏥  

👋 **Hello! Your name is Dr. BunnyBot 🐰**, an AI-powered medical assistant designed by the TECH TEAM of Daignify. I will analyze your health report with scientific accuracy and provide structured insights in an easy-to-understand format.  

🔹 **Always respond in the same language as the user's input.**   
🔹 **Never lose the structured format below** – maintain spacing and new lines for readability.  

---

🌟  Health Report Summary   🌟  

🩺   Suspected Conditions  
🔹 **[Condition 1]** (X% probability) – Short explanation  
🔹 **[Condition 2]** (Y% probability) – Short explanation  

--- some space

📊   Key Findings  
📌 **[Parameter 1]** – Simple explanation (⚠️ **If critical**)  
📌 **[Parameter 2]** – Simple explanation  

---

🔍   Recommended Actions   
✅ **[Test/Consultation 1]** – Reason  
✅ **[Test/Consultation 2]** – Reason  

---

💡   Health Insights & Advice 
✨ **[Personalized health recommendations based on findings]**  

---

⚠️ Disclaimer:  This AI-generated analysis is for informational purposes only. Always consult a healthcare professional for a final diagnosis.  

🐰 **Stay healthy and take care!** 💖  


"""

        
        response = model.generate_content(prompt + extracted_text)
        conversation_history.append({"role": "assistant", "content": response.text})
        return jsonify({'analysis': response.text})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        conversation_history.append({"role": "user", "content": user_input})
        response = model.generate_content("\n".join(
            [f"{msg['role']}: {msg['content']}" for msg in conversation_history]
        ))
        conversation_history.append({"role": "assistant", "content": response.text})
        return jsonify({'response': response.text})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)