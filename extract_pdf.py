import sys
try:
    import PyPDF2
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2

def extract_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for i, page in enumerate(reader.pages):
            text += f"--- Page {i+1} ---\n"
            text += page.extract_text() + "\n"
    
    with open("pdf_text_output.txt", "w", encoding="utf-8") as out_file:
        out_file.write(text)

if __name__ == "__main__":
    extract_text("Startup_Policy_Intelligence_Implementation_Plan (1).pdf")
