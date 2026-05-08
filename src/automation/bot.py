from playwright.sync_api import sync_playwright
import time
import os

def apply_to_greenhouse(page, job_url, resume_path, personal_info):
    """Automate applying to a Greenhouse job."""
    print(f"Applying to Greenhouse: {job_url}")
    page.goto(job_url)
    
    # Wait for form to load
    page.wait_for_selector('form#application_form', timeout=10000)
    
    # Fill standard fields
    page.fill('input[name="job_application[first_name]"]', personal_info.get('first_name', ''))
    page.fill('input[name="job_application[last_name]"]', personal_info.get('last_name', ''))
    page.fill('input[name="job_application[email]"]', personal_info.get('email', ''))
    page.fill('input[name="job_application[phone]"]', personal_info.get('phone', ''))
    
    # Fill LinkedIn / Github if present (often custom questions, but sometimes standard)
    # Greenhouse often has custom question fields for URLs. We look for labels containing 'linkedin' or 'github'
    
    # Upload Resume
    # Greenhouse usually has a file input inside a div with id 'resume_fieldset' or similar
    file_inputs = page.locator('input[type="file"]')
    if file_inputs.count() > 0:
        # Usually the first file input is the resume
        file_inputs.first.set_input_files(resume_path)
    
    # Wait a bit to simulate human interaction
    time.sleep(1)
    
    # Click Submit (We will NOT actually click submit during testing/general runs unless explicitly desired)
    # page.click('input[type="submit"]')
    # For now, we just print success
    print("Greenhouse form filled successfully (Submit bypassed).")
    return True

def apply_to_lever(page, job_url, resume_path, personal_info):
    """Automate applying to a Lever job."""
    print(f"Applying to Lever: {job_url}")
    
    # Lever usually requires clicking 'Apply for this job' first if we are not on the /apply page
    if "/apply" not in job_url:
        job_url = job_url.rstrip("/") + "/apply"
        
    page.goto(job_url)
    page.wait_for_selector('form', timeout=10000)
    
    # Fill standard fields
    page.fill('input[name="name"]', f"{personal_info.get('first_name', '')} {personal_info.get('last_name', '')}")
    page.fill('input[name="email"]', personal_info.get('email', ''))
    page.fill('input[name="phone"]', personal_info.get('phone', ''))
    
    # URLs
    if personal_info.get('linkedin'):
        linkedin_input = page.locator('input[name="urls[LinkedIn]"]')
        if linkedin_input.count() > 0:
            linkedin_input.fill(personal_info.get('linkedin'))
            
    if personal_info.get('github'):
        github_input = page.locator('input[name="urls[GitHub]"]')
        if github_input.count() > 0:
            github_input.fill(personal_info.get('github'))
    
    # Upload Resume
    file_input = page.locator('input[type="file"][data-qa="resume-upload-input"]')
    if file_input.count() > 0:
        file_input.set_input_files(resume_path)
    else:
        # Fallback
        file_inputs = page.locator('input[type="file"]')
        if file_inputs.count() > 0:
            file_inputs.first.set_input_files(resume_path)
    
    time.sleep(1)
    
    # Submit button
    # page.click('button[data-qa="btn-submit"]')
    print("Lever form filled successfully (Submit bypassed).")
    return True

def auto_apply(job_url: str, ats_type: str, resume_path: str, personal_info: dict) -> bool:
    """Main entry point to start the Playwright bot."""
    if ats_type not in ["greenhouse", "lever"]:
        print(f"Auto-apply not supported for ATS type: {ats_type}")
        return False
        
    try:
        with sync_playwright() as p:
            # Run headless for background operation
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            page = context.new_page()
            
            success = False
            if ats_type == "greenhouse":
                success = apply_to_greenhouse(page, job_url, resume_path, personal_info)
            elif ats_type == "lever":
                success = apply_to_lever(page, job_url, resume_path, personal_info)
                
            browser.close()
            return success
    except Exception as e:
        print(f"Error during auto-apply: {e}")
        return False

if __name__ == "__main__":
    print("Testing auto_apply module loaded.")
