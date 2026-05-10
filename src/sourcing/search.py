from ddgs import DDGS
from bs4 import BeautifulSoup
import requests
import json
import os
from google import genai
from dotenv import load_dotenv
import warnings
import time

# Suppress the deprecation warning
warnings.filterwarnings("ignore", category=FutureWarning)

load_dotenv()

DEFAULT_JOB_TITLES = [
    "Software Engineer",
    "Backend Engineer",
    "Full Stack Engineer",
    "Data Scientist",
    "Machine Learning Engineer"
]

ATS_DOMAINS = {
    "greenhouse": "boards.greenhouse.io",
    "lever": "jobs.lever.co",
    "workday": "myworkdayjobs.com"
}

def search_jobs(job_title: str, ats_type: str, max_results: int = 10) -> list:
    """Search for jobs on a specific ATS platform using DuckDuckGo."""
    domain = ATS_DOMAINS.get(ats_type)
    if not domain:
        return []
    
    query = f'site:{domain} "{job_title}"'
    print(f"Searching: {query}")
    results = []
    try:
        ddgs = DDGS()
        # DuckDuckGo occasionally throttles, we use text search
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
                "ats_type": ats_type
            })
    except Exception as e:
        print(f"Error searching DDG: {e}")
    return results

def fetch_job_description(url: str) -> str:
    """Attempt to fetch the job description from the URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Very basic extraction - most ATS put main content in body
            return soup.get_text(separator=' ', strip=True)[:10000] # Limit length
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ""

def evaluate_job(job_description: str) -> dict:
    """
    Evaluates if a job is suitable based on visa/OPT status and clearance requirements.
    Must strictly reject security clearance and ensure OPT/Visa is allowed or not mentioned.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        return {"is_match": True, "reason": "No API key to evaluate. Assuming match."}

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    You are an AI assistant helping an international MS in CS student on OPT find jobs.
    Review the following job description and determine if it is a match based on these strict rules:
    1. EXCLUDE: If the job requires a Security Clearance (e.g., TS/SCI, Secret), it must be rejected.
    2. EXCLUDE: If the job explicitly states it does NOT sponsor visas AND does not accept OPT/CPT, it must be rejected.
    3. INCLUDE: If the job explicitly mentions supporting OPT/CPT or Visa Sponsorship, it is a match.
    4. INCLUDE: If the job does NOT mention visas or OPT at all, it is a match (we will apply anyway).
    
    Return a strict JSON object:
    {{
        "is_match": true or false,
        "reason": "short explanation of why"
    }}
    Do NOT include any markdown formatting like ```json ... ```.

    Job Description:
    {job_description[:5000]} # Limit to 5k chars for API constraints
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

            time.sleep(base_delay) # Add standard delay to respect rate limits
            return json.loads(response_text)
        except Exception as e:
            print(f"Error evaluating job (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                sleep_time = base_delay * (2 ** attempt)
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                return {"is_match": False, "reason": f"Error during AI evaluation after {max_retries} attempts."}

if __name__ == "__main__":
    # Test DDG
    print("Testing DDG search...")
    res = search_jobs("Software Engineer", "greenhouse", 2)
    print(res)
