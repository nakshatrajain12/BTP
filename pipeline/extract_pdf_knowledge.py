"""
One-time script to extract text from the Central Government Schemes PDF
and save it as a text file for GOV-BOT's knowledge base.
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def extract_pdf():
    try:
        import PyPDF2
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
        import PyPDF2

    # Try both possible PDF filenames
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(root, "Central Government Schemes for Startups - Updated as of 30Jan2026 (1).pdf"),
        os.path.join(root, "Startup Policy Intelligence Dashboard.pdf"),
    ]
    
    all_text = ""
    for pdf_path in candidates:
        if os.path.exists(pdf_path):
            print(f"Extracting: {os.path.basename(pdf_path)}")
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        all_text += f"\n--- {os.path.basename(pdf_path)} Page {i+1} ---\n"
                        all_text += page_text + "\n"
    
    if not all_text:
        print("No PDF files found to extract.")
        return
    
    output_path = os.path.join(root, "pipeline", "knowledge_base.txt")
    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write(all_text)
    
    print(f"Knowledge base extracted: {len(all_text)} characters saved to {output_path}")

if __name__ == "__main__":
    extract_pdf()
