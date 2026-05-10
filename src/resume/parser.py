import PyPDF2
from google import genai
import os
import json
import time
from dotenv import load_dotenv
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)
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
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert ATS resume parser. Extract the following information from the provided resume text and return it strictly as a JSON object.
    Do NOT include any markdown formatting like ```json ... ```, just the raw JSON object.
    
    You must capture ALL sections present in the resume, preserving their original order.
    The output JSON MUST follow this exact structure:
    {{
        "personal_info": {{
            "name": "Full Name",
            "email": "Email Address",
            "phone": "Phone Number",
            "linkedin": "LinkedIn URL",
            "github": "Github URL"
        }},
        "sections": [
            {{
                "title": "SECTION_TITLE",
                "type": "text | list | items",
                "content": "Use this for 'text' type (e.g. Summary)",
                "list": ["item 1", "item 2"], # Use this for 'list' type (e.g. Skills)
                "items": [ # Use this for 'items' type (e.g. Experience, Education, Projects)
                    {{
                        "heading": "Job Title / Degree / Project Name",
                        "subheading": "Company / University (optional)",
                        "date": "Dates (optional)",
                        "bullets": ["Bullet 1", "Bullet 2"]
                    }}
                ]
            }}
        ]
    }}
    
    Resume Text:
    {resume_text}
    """
    
    max_retries = 3
    base_delay = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            # Clean response string in case it contains markdown
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()

            parsed_data = json.loads(response_text)
            time.sleep(base_delay)
            return parsed_data
        except Exception as e:
            print(f"Error parsing AI response to JSON (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = base_delay * (2 ** attempt)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                try:
                    print(f"Raw response: {response.text}")
                except Exception:
                    pass
                return {}
    return {}

def tailor_resume_content(parsed_resume: dict, job_description: str) -> dict:
    """Tailor the resume content specifically for a given job description."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        # Fallback to the original parsed resume if API key is not set
        return parsed_resume
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an expert career coach and resume writer. 
    I have my master resume details in JSON format and a job description.
    Please tailor the content within the 'sections' array to better align with the job description.
    Specifically, focus on tailoring summaries, skills, and bullet points under experience or projects.
    Keep the truthfulness of the experience but emphasize the relevant aspects.
    Return ONLY a JSON object matching the exact structure of the input master resume JSON (with 'personal_info' and 'sections').
    Do NOT include any markdown formatting like ```json ... ```.

    Master Resume JSON:
    {json.dumps(parsed_resume)}

    Job Description:
    {job_description}
    """
    
    max_retries = 3
    base_delay = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()

            tailored_data = json.loads(response_text)
            time.sleep(base_delay)
            return tailored_data
        except Exception as e:
            print(f"Error parsing AI response to JSON (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = base_delay * (2 ** attempt)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                return parsed_resume
    return parsed_resume
