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
model = genai.GenerativeModel('gemini-1.5-pro')

# Configure Tesseract (Update path as needed)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

conversation_history = []
import re

def format_response(response_text):
    """
    Enforces strict formatting with bullet points and sections.
    """
    # Clean up unwanted characters and fix any inconsistent spacing
    cleaned_response = re.sub(r"---\s*some space\s*", "---", response_text)  # Fix space inconsistencies
    
    # Split into sections by '---'
    sections = re.split(r"---+", cleaned_response)
    
    formatted_response = ""
    
    for section in sections:
        # Skip empty sections
        if not section.strip():
            continue
        
        # Extract the header using regex (anything between "**")
        section_header = re.search(r"\*\*(.*?)\*\*", section)
        if section_header:
            header = section_header.group(1).strip()
        else:
            header = ""
        
        # Remove header tags and extra spaces
        content = re.sub(r"\*\*.*?\*\*", "", section).strip()  # Remove headers from content
        
        # Process content based on the section header
        if "Suspected Conditions" in header:
            formatted_response += "🩺 **Suspected Conditions**\n"
            # Split into bullet points (handle different bullet styles)
            bullets = re.split(r"\n|•|🔹|📌", content)
            for bullet in bullets:
                bullet = bullet.strip()
                if bullet:
                    formatted_response += f"- {bullet}\n"
        
        elif "Key Findings" in header:
            formatted_response += "📊 **Key Findings**\n"
            bullets = re.split(r"\n|•|🔹|📌", content)
            for bullet in bullets:
                bullet = bullet.strip()
                if bullet:
                    formatted_response += f"- {bullet}\n"
        
        elif "Recommended Actions" in header:
            formatted_response += "🔍 **Recommended Actions**\n"
            bullets = re.split(r"\n|•|🔹|✅", content)
            for bullet in bullets:
                bullet = bullet.strip()
                if bullet:
                    formatted_response += f"- {bullet}\n"
        
        elif "Health Insights & Advice" in header:
            formatted_response += "💡 **Health Insights & Advice**\n"
            bullets = re.split(r"\n|•|🔹|✨", content)
            for bullet in bullets:
                bullet = bullet.strip()
                if bullet:
                    formatted_response += f"- {bullet}\n"
        
        else:
            # Handle non-structured text (e.g., disclaimers)
            formatted_response += f"{section.strip()}\n\n"
    
    # Ensure the response ends with a proper ending
    formatted_response += "\n\n🐰 **Stay healthy and take care!** 💖"

    return formatted_response


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
        prompt = """🏥 **Diagnify Health Report Analysis** 🏥  

👋 **Hello! Your name is Diagnify 🐰**, an AI-powered medical assistant. Analyze the health report and respond **strictly in this format**:  

---

🌟 **Health Report Summary** 🌟  

🩺 **Suspected Conditions**  
- **[Condition 1]** (X% probability) – One-line explanation  
- **[Condition 2]** (Y% probability) – One-line explanation  

---

📊 **Key Findings**  
- **[Parameter 1]** – Value (Normal range) – One-line explanation  
- **[Parameter 2]** – Value (Normal range) – One-line explanation  

---

🔍 **Recommended Actions**  
- **[Action 1]** – One-line reason  
- **[Action 2]** – One-line reason  

---

💡 **Health Insights & Advice**  
- **[Recommendation 1]**  
- **[Recommendation 2]**  

---

⚠️ **Disclaimer**: This analysis is for informational purposes only. Consult a healthcare professional for diagnosis.  

🐰 **Stay healthy and take care!** 💖  

🔹 **Rules**:  
- Use bullet points (`-`) only. NO PARAGRAPHS.  
- Keep explanations concise (1 line per bullet).  
- Maintain the exact section order and headings.  
"""
        prompt = """🏥 **Diagnify Health Report Analysis** 🏥  

👋 **Hello! Your name is Diagnify 🐰**, an AI-powered medical assistant designed by the TECH TEAM of Daignify. I will analyze your health report with scientific accuracy and provide structured insights in an easy-to-understand format.  

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
        formatted_response = format_response(response.text)
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