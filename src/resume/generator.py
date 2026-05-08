from fpdf import FPDF
from fpdf.enums import XPos, YPos
import json

class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        pass

def generate_pdf(resume_data: dict, output_path: str):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Fonts
    # We use basic fonts (helvetica) for clean black-and-white ATS formatting
    pdf.set_font("helvetica", 'B', 16)
    
    # Personal Info
    info = resume_data.get("personal_info", {})
    name = info.get("name", "Applicant Name")
    pdf.cell(0, 10, name, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    
    pdf.set_font("helvetica", '', 10)
    contact_info = []
    if info.get("email"): contact_info.append(info.get("email"))
    if info.get("phone"): contact_info.append(info.get("phone"))
    if info.get("linkedin"): contact_info.append(info.get("linkedin"))
    if info.get("github"): contact_info.append(info.get("github"))
    
    pdf.cell(0, 5, " | ".join(contact_info), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(5)
    
    # Summary
    summary = resume_data.get("summary")
    if summary:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, "PROFESSIONAL SUMMARY", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("helvetica", '', 10)
        pdf.multi_cell(0, 5, summary)
        pdf.ln(5)
    
    # Skills
    skills = resume_data.get("skills", [])
    if skills:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, "SKILLS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("helvetica", '', 10)
        skills_str = ", ".join(skills)
        pdf.multi_cell(0, 5, skills_str)
        pdf.ln(5)
    
    # Experience
    experience = resume_data.get("experience", [])
    if experience:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, "EXPERIENCE", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(2)
        
        for exp in experience:
            pdf.set_font("helvetica", 'B', 10)
            pdf.cell(100, 5, exp.get("role", ""), new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
            pdf.cell(90, 5, exp.get("duration", ""), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            
            pdf.set_font("helvetica", 'I', 10)
            pdf.cell(0, 5, exp.get("company", ""), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
            
            pdf.set_font("helvetica", '', 10)
            for bullet in exp.get("description", []):
                pdf.set_x(15)
                # Handle non-ascii characters gracefully for basic FPDF
                clean_bullet = bullet.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, f"- {clean_bullet}")
            pdf.ln(3)

    # Education
    education = resume_data.get("education", [])
    if education:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, "EDUCATION", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(2)
        
        for edu in education:
            pdf.set_font("helvetica", 'B', 10)
            pdf.cell(140, 5, edu.get("degree", ""), new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
            pdf.cell(50, 5, edu.get("graduation_date", ""), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')
            
            pdf.set_font("helvetica", 'I', 10)
            pdf.cell(0, 5, edu.get("university", ""), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
            pdf.ln(2)

    pdf.output(output_path)

if __name__ == "__main__":
    # Test generation
    dummy_data = {
        "personal_info": {"name": "John Doe", "email": "john@example.com"},
        "summary": "Experienced software engineer.",
        "skills": ["Python", "Java"],
        "experience": [{"role": "SDE", "company": "Tech Corp", "duration": "2020 - Present", "description": ["Did things", "Fixed bugs"]}],
        "education": [{"degree": "MS CS", "university": "State Univ", "graduation_date": "2020"}]
    }
    generate_pdf(dummy_data, "test_resume.pdf")
    print("Test PDF generated successfully.")
