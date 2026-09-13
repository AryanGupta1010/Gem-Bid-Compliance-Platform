import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_pdf(filename, pages_content):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    for i, content in enumerate(pages_content):
        if i > 0:
            c.showPage()
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height - 72, f"Document Page {i + 1}")
        
        c.setFont("Helvetica", 12)
        y = height - 120
        for line in content.split('\n'):
            c.drawString(72, y, line)
            y -= 20
    
    c.save()

def main():
    os.makedirs("demo_documents", exist_ok=True)
    
    # TECHNOVA
    technova_pages = [
        "Company Profile\nName: TechNova Solutions\nCPPP Debarment Status: No debarment record found. Active and compliant.",
        "Tax Information\nGST Identification Number: 27AADCB2230M1Z2\nRegistration Status: Active",
        "Financial Overview\nAverage annual turnover for the last 3 financial years is verified.\nFY 2024-25 turnover: INR 14.2 Crore",
        "Manufacturing Details\nLocal content percentage is certified to be 62%.\nThis qualifies as Class-I local supplier.",
        "Authorization\nValid OEM Authorization Letter\nWe hereby authorize TechNova Solutions to supply and support our equipment."
    ]
    create_pdf("demo_documents/technova.pdf", technova_pages)
    
    # APEX
    apex_pages = [
        "Company Profile\nName: Apex Enterprises\nCPPP Debarment Status: Debarred match found. Currently on suspension list.",
        "Tax Information\nGST Identification Number: 07BBPCA1120K1Z1\nRegistration Status: Suspended",
        "Financial Overview\nAverage annual turnover for the last 3 financial years is verified.\nFY 2024-25 turnover: INR 8.5 Crore",
        "Manufacturing Details\nLocal content percentage is certified to be 31%.\nThis does not meet the minimum requirements.",
        "Authorization\nOEM Authorization Letter\nWe hereby authorize Apex Core Technologies to supply and support our equipment."
    ]
    create_pdf("demo_documents/apex.pdf", apex_pages)
    
    # MEDCORE
    medcore_pages = [
        "Company Profile\nName: MedCore Systems\nCPPP Debarment Status: No debarment record found.",
        "Tax Information\nGST Identification Number: 29CCPMD3340L1Z3 (Unreadable / Illegible scan)\nRegistration Status: Unknown",
        "Financial Overview\nAverage annual turnover for the last 3 financial years is verified.\nFY 2024-25 turnover: INR 11.4 Crore",
        "Manufacturing Details\nEvidence conflicts - section A states local content is 48%.\nHowever, section B states local content is 52%.",
        "Authorization\nOEM Authorization Letter\nMissing official signature. Validity is undetermined."
    ]
    create_pdf("demo_documents/medcore.pdf", medcore_pages)

    print("Successfully generated golden demo PDFs in demo_documents/")

if __name__ == "__main__":
    main()
