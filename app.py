import streamlit as st
import os
import json
import pandas as pd
from dotenv import load_dotenv, set_key

# Load modules
from src.db.models import SessionLocal, init_db
from src.db.crud import add_job, get_all_jobs, get_jobs_by_status, update_job_status
from src.resume.parser import extract_text_from_pdf, parse_resume_with_ai, tailor_resume_content
from src.resume.generator import generate_pdf
from src.sourcing.search import search_jobs, fetch_job_description, evaluate_job, DEFAULT_JOB_TITLES, ATS_DOMAINS
from src.automation.bot import auto_apply

# Initialize Database
init_db()

# Load env
load_dotenv()

st.set_page_config(page_title="Auto Apply Bot", layout="wide")
st.title("🤖 Auto Apply Bot")

tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Setup", "🔍 Sourcing", "🚀 Applications", "📊 Dashboard"])

# --- TAB 1: SETUP ---
with tab1:
    st.header("Initial Setup")
    
    # API Key
    api_key = os.getenv("GEMINI_API_KEY")
    st.subheader("1. API Key")
    key_input = st.text_input("Google Gemini API Key", value=api_key if api_key and api_key != "your_api_key_here" else "", type="password")
    if st.button("Save API Key"):
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        set_key(env_path, "GEMINI_API_KEY", key_input)
        st.success("API Key saved to .env!")
        
    # Resume Upload
    st.subheader("2. Master Resume")
    uploaded_file = st.file_uploader("Upload your master PDF resume", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Process Master Resume"):
            with st.spinner("Extracting text and parsing with AI..."):
                # Save temp pdf
                temp_pdf = "temp_master.pdf"
                with open(temp_pdf, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                text = extract_text_from_pdf(temp_pdf)
                parsed_json = parse_resume_with_ai(text)
                
                # Save parsed json locally
                with open("master_profile.json", "w") as f:
                    json.dump(parsed_json, f, indent=4)
                    
                st.success("Resume parsed successfully!")
                st.json(parsed_json)

# --- TAB 2: SOURCING ---
with tab2:
    st.header("Job Sourcing")
    col1, col2 = st.columns(2)
    with col1:
        job_titles_str = st.text_area("Job Titles to Search (comma separated)", value=", ".join(DEFAULT_JOB_TITLES))
    with col2:
        target_ats = st.multiselect("Target ATS Platforms", options=list(ATS_DOMAINS.keys()), default=["greenhouse", "lever"])
        max_results = st.number_input("Max Results per Search", min_value=1, max_value=50, value=5)
        
    if st.button("Start Search & Filter"):
        if not os.path.exists("master_profile.json"):
            st.error("Please parse your master resume in the Setup tab first.")
        else:
            job_titles = [t.strip() for t in job_titles_str.split(",")]
            db = SessionLocal()
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_searches = len(job_titles) * len(target_ats)
            completed = 0
            
            for title in job_titles:
                for ats in target_ats:
                    status_text.text(f"Searching for '{title}' on {ats}...")
                    results = search_jobs(title, ats, max_results)
                    
                    for r in results:
                        # Add to DB initially as 'new'
                        company_name = r['title'].split(" at ")[-1] if " at " in r['title'] else "Unknown"
                        job = add_job(db, company=company_name, title=r['title'], url=r['url'], ats_type=r['ats_type'], description=r['snippet'])
                        
                        # Fetch and evaluate
                        full_desc = fetch_job_description(r['url'])
                        eval_res = evaluate_job(full_desc)
                        
                        if eval_res.get('is_match'):
                            update_job_status(db, job.id, "queued", eval_res.get('reason'))
                        else:
                            update_job_status(db, job.id, "rejected", eval_res.get('reason'))
                            
                    completed += 1
                    progress_bar.progress(completed / total_searches)
            
            status_text.text("Search complete!")
            db.close()

# --- TAB 3: APPLICATIONS ---
with tab3:
    st.header("Queued Applications")
    db = SessionLocal()
    queued_jobs = get_jobs_by_status(db, "queued")
    
    if not queued_jobs:
        st.info("No queued jobs found. Go to Sourcing to find some!")
    else:
        st.write(f"Found {len(queued_jobs)} jobs queued for application.")
        df = pd.DataFrame([{
            "ID": j.id, "Company": j.company, "Title": j.title, "ATS": j.ats_type, "URL": j.url
        } for j in queued_jobs])
        st.dataframe(df)
        
        if st.button("Start Autonomous Applying"):
            if not os.path.exists("master_profile.json"):
                st.error("Missing master_profile.json")
            else:
                with open("master_profile.json", "r") as f:
                    master_profile = json.load(f)
                
                # Split personal info for the bot
                info = master_profile.get("personal_info", {})
                names = info.get("name", "Applicant").split()
                bot_info = {
                    "first_name": names[0] if names else "",
                    "last_name": " ".join(names[1:]) if len(names)>1 else "",
                    "email": info.get("email", ""),
                    "phone": info.get("phone", ""),
                    "linkedin": info.get("linkedin", ""),
                    "github": info.get("github", "")
                }
                
                progress = st.progress(0)
                for i, job in enumerate(queued_jobs):
                    st.write(f"Processing: {job.company} - {job.title}")
                    
                    # 1. Tailor Resume
                    tailored_profile = tailor_resume_content(master_profile, job.description or job.title)
                    pdf_path = f"resume_{job.id}.pdf"
                    generate_pdf(tailored_profile, pdf_path)
                    
                    # 2. Apply
                    success = auto_apply(job.url, job.ats_type, os.path.abspath(pdf_path), bot_info)
                    
                    # 3. Update DB
                    if success:
                        update_job_status(db, job.id, "applied", "Successfully automated.")
                        st.success(f"Applied to {job.company}!")
                    else:
                        update_job_status(db, job.id, "failed", "Bot failed to complete form.")
                        st.error(f"Failed to apply to {job.company}")
                        
                    progress.progress((i + 1) / len(queued_jobs))
    db.close()

# --- TAB 4: DASHBOARD ---
with tab4:
    st.header("Application Tracking Dashboard")
    db = SessionLocal()
    all_jobs = get_all_jobs(db)
    
    if all_jobs:
        df = pd.DataFrame([{
            "Company": j.company,
            "Title": j.title,
            "ATS": j.ats_type,
            "Status": j.status,
            "Date Found": j.date_found.strftime("%Y-%m-%d"),
            "Notes": j.notes
        } for j in all_jobs])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Jobs Found", len(df))
        col2.metric("Queued", len(df[df['Status'] == 'queued']))
        col3.metric("Applied", len(df[df['Status'] == 'applied']))
        col4.metric("Rejected/Failed", len(df[df['Status'].isin(['rejected', 'failed'])]))
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data yet.")
    db.close()
