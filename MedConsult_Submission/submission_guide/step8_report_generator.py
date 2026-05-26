# STEP 8: HEALTH REPORT GENERATION
# Generates a professional PDF summary of the health analysis.

from fpdf import FPDF
import datetime

def generate_pdf_report(patient, analysis):
    """
    Creates a PDF document with symptoms and conditions.
    Matches Feature 9.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "MedConsult AI - Health Report", ln=True, align='C')
    
    # Patient Info
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Patient Name: {patient['name']}", ln=True)
    pdf.cell(200, 10, f"Date: {datetime.date.today()}", ln=True)
    
    # Analysis
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Analysis Summary:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Detected Condition: {analysis['condition']}", ln=True)
    pdf.cell(200, 10, f"Severity: {analysis['severity']}", ln=True)
    pdf.cell(200, 10, f"Suggested Specialist: {analysis['specialty']}", ln=True)
    
    # Save the PDF to the output path
    output_path = f"report_{patient['mail'].split('@')[0]}.pdf"
    pdf.output(output_path)
    return output_path
