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
    
    # Sections
    sections = resume_data.get("sections", [])
    for section in sections:
        title = section.get("title", "").upper()
        if not title:
            continue
            
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(2)
        
        sec_type = section.get("type")

        if sec_type == "text":
            content = section.get("content", "")
            if content:
                pdf.set_font("helvetica", '', 10)
                clean_content = content.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, clean_content)
                pdf.ln(5)

        elif sec_type == "list":
            items = section.get("list", [])
            if items:
                pdf.set_font("helvetica", '', 10)
                clean_items = [item.encode('latin-1', 'replace').decode('latin-1') for item in items]
                items_str = ", ".join(clean_items)
                pdf.multi_cell(0, 5, items_str)
                pdf.ln(5)

        elif sec_type == "items":
            items = section.get("items", [])
            for item in items:
                pdf.set_font("helvetica", 'B', 10)
                heading = item.get("heading", "").encode('latin-1', 'replace').decode('latin-1')
                date_str = item.get("date", "").encode('latin-1', 'replace').decode('latin-1')

                pdf.cell(140, 5, heading, new_x=XPos.RIGHT, new_y=YPos.TOP, align='L')
                pdf.cell(50, 5, date_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='R')

                subheading = item.get("subheading", "")
                if subheading:
                    pdf.set_font("helvetica", 'I', 10)
                    clean_sub = subheading.encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(0, 5, clean_sub, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')

                bullets = item.get("bullets", [])
                if bullets:
                    pdf.set_font("helvetica", '', 10)
                    for bullet in bullets:
                        pdf.set_x(15)
                        clean_bullet = bullet.encode('latin-1', 'replace').decode('latin-1')
                        pdf.multi_cell(0, 5, f"- {clean_bullet}")
                pdf.ln(3)

    pdf.output(output_path)

if __name__ == "__main__":
    # Test generation
    dummy_data = {
        "personal_info": {"name": "John Doe", "email": "john@example.com"},
        "sections": [
            {"title": "Professional Summary", "type": "text", "content": "Experienced software engineer."},
            {"title": "Skills", "type": "list", "list": ["Python", "Java"]},
            {"title": "Experience", "type": "items", "items": [{"heading": "SDE", "subheading": "Tech Corp", "date": "2020 - Present", "bullets": ["Did things", "Fixed bugs"]}]},
            {"title": "Education", "type": "items", "items": [{"heading": "MS CS", "subheading": "State Univ", "date": "2020"}]}
        ]
    }
    generate_pdf(dummy_data, "test_resume.pdf")
    print("Test PDF generated successfully.")
