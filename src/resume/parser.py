import PyPDF2
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def parse_resume_with_ai(resume_text: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY not found or invalid in .env file")
    
    genai.configure(api_key=api_key)
    # Use gemini-1.5-flash as the free, fast model
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert ATS resume parser. Extract the following information from the provided resume text and return it strictly as a JSON object.
    Do NOT include any markdown formatting like ```json ... ```, just the raw JSON object.
    
    Required JSON structure:
    {{
        "personal_info": {{
            "name": "Full Name",
            "email": "Email Address",
            "phone": "Phone Number",
            "linkedin": "LinkedIn URL",
            "github": "Github URL"
        }},
        "summary": "Professional Summary",
        "education": [
            {{"degree": "Degree Name", "university": "University Name", "graduation_date": "Date"}}
        ],
        "experience": [
            {{"role": "Job Title", "company": "Company Name", "duration": "Dates", "description": ["Bullet 1", "Bullet 2"]}}
        ],
        "skills": ["Skill 1", "Skill 2"]
    }}
    
    Resume Text:
    {resume_text}
    """
    
    response = model.generate_content(prompt)
    try:
        # Clean response string in case it contains markdown
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        parsed_data = json.loads(response_text)
        return parsed_data
    except Exception as e:
        print(f"Error parsing AI response to JSON: {e}")
        print(f"Raw response: {response.text}")
        return {}

def tailor_resume_content(parsed_resume: dict, job_description: str) -> dict:
    """Tailor the resume content specifically for a given job description."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        # Fallback to the original parsed resume if API key is not set
        return parsed_resume
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert career coach and resume writer. 
    I have my master resume details in JSON format and a job description.
    Please tailor the 'summary', 'experience' bullet points, and 'skills' to better align with the job description.
    Keep the truthfulness of the experience but emphasize the relevant aspects.
    Return ONLY a JSON object matching the exact structure of the input master resume JSON.
    Do NOT include any markdown formatting like ```json ... ```.

    Master Resume JSON:
    {json.dumps(parsed_resume)}

    Job Description:
    {job_description}
    """
    
    response = model.generate_content(prompt)
    try:
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        tailored_data = json.loads(response_text)
        return tailored_data
    except Exception as e:
        print(f"Error parsing AI response to JSON: {e}")
        return parsed_resume
